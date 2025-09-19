import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
from flask import url_for

CACHE_FILE_POSTS = 'entertainment_posts_cache.json'
CACHE_FILE_EVENTS = 'entertainment_events_cache.json'
CACHE_DURATION_HOURS = 24  # Cache for 24 hours


def _is_cache_valid(cache_file: str) -> bool:
    """Check if cache file exists and is less than 24 hours old"""
    if not os.path.exists(cache_file):
        return False
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        cache_time = datetime.fromisoformat(data.get('cached_at', ''))
        expiry_time = cache_time + timedelta(hours=CACHE_DURATION_HOURS)
        
        return datetime.now() < expiry_time
    except (json.JSONDecodeError, ValueError, KeyError):
        return False


def _save_cache(cache_file: str, data: List[Dict[str, Any]]) -> None:
    """Save data to cache file with timestamp"""
    cache_data = {
        'cached_at': datetime.now().isoformat(),
        'data': data
    }
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save cache to {cache_file}: {e}")


def _load_cache(cache_file: str) -> Optional[List[Dict[str, Any]]]:
    """Load data from cache file"""
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('data', [])
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def _scrape_instagram_posts() -> List[Dict[str, Any]]:
    """Scrape Instagram posts from beardbanduk"""
    posts = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(
            "https://www.instagram.com/beardbanduk/",
            headers=headers,
            timeout=10
        )
        
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the script tag containing the page data
            script_tags = soup.find_all('script', string=re.compile(r'window\._sharedData'))
            
            if script_tags:
                script_content = script_tags[0].string
                # Extract JSON data
                json_match = re.search(r'window\._sharedData = ({.*?});', script_content)
                
                if json_match:
                    data = json.loads(json_match.group(1))
                    
                    # Navigate through the Instagram data structure
                    entry_data = data.get('entry_data', {})
                    profile_page = entry_data.get('ProfilePage', [])
                    
                    if profile_page and len(profile_page) > 0:
                        user_data = profile_page[0].get('graphql', {}).get('user', {})
                        media_data = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                        
                        for item in media_data[:3]:  # Get last 3 posts
                            node = item.get('node', {})
                            
                            # Extract post data
                            image_url = node.get('display_url', '')
                            caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                            caption = ''
                            if caption_edges:
                                caption = caption_edges[0].get('node', {}).get('text', '')
                            
                            # Truncate caption
                            if len(caption) > 140:
                                caption = caption[:137].rstrip() + "…"
                            
                            permalink = f"https://www.instagram.com/p/{node.get('shortcode', '')}/"
                            
                            if image_url:
                                posts.append({
                                    "caption": caption or "View on Instagram",
                                    "permalink": permalink,
                                    "image_url": image_url,
                                    "timestamp": node.get('taken_at_timestamp')
                                })
    except Exception as e:
        print(f"Instagram scraping failed: {e}")
    
    return posts


def _get_fallback_posts() -> List[Dict[str, Any]]:
    """Get fallback posts when scraping fails"""
    # Note: url_for might not be available outside Flask context, so we'll use a relative path
    fallback_image = "/static/images/entertainment.jpg"
    
    return [
        {
            "caption": "Beard live highlight reel – book us for your next party!",
            "permalink": "https://www.instagram.com/beardbanduk/",
            "image_url": fallback_image,
            "timestamp": None,
        },
        {
            "caption": "Follow @beardbanduk for the latest gig updates and behind-the-scenes content!",
            "permalink": "https://www.instagram.com/beardbanduk/",
            "image_url": fallback_image,
            "timestamp": None,
        },
        {
            "caption": "Indie anthems and party classics - bringing the energy to every venue!",
            "permalink": "https://www.instagram.com/beardbanduk/",
            "image_url": fallback_image,
            "timestamp": None,
        },
        {
            "caption": "Late-night DJ sets keep the dance floor packed until close.",
            "permalink": "https://www.instagram.com/beardbanduk/",
            "image_url": fallback_image,
            "timestamp": None,
        },
        {
            "caption": "Behind the scenes with the band – follow @beardbanduk for more!",
            "permalink": "https://www.instagram.com/beardbanduk/",
            "image_url": fallback_image,
            "timestamp": None,
        }
    ]


def _get_fallback_events() -> List[Dict[str, Any]]:
    """Get fallback events"""
    return [
        {
            "title": "BEARD @ The Vaults",
            "url": "https://www.facebook.com/bearduk/events",
            "date": "Fri, 28 Nov at 21:00",
            "venue": "The Vaults, Southsea"
        },
        {
            "title": "BEARD @ Steamtown",
            "url": "https://www.facebook.com/bearduk/events", 
            "date": "Fri, 19 Dec at 20:00",
            "venue": "Steam Town Brew Co, Eastleigh"
        },
        {
            "title": "Private Party",
            "url": "https://www.facebook.com/bearduk/events",
            "date": "Tomorrow at 19:00",
            "venue": "Private Venue"
        },
        {
            "title": "BEARD @ The Anglers",
            "url": "https://www.facebook.com/bearduk/events",
            "date": "Sun, 21 Dec at 16:00",
            "venue": "The Anglers"
        }
    ]


def get_cached_posts() -> List[Dict[str, Any]]:
    """Get Instagram posts with caching (max once per day)"""
    # Check if cache is valid
    if _is_cache_valid(CACHE_FILE_POSTS):
        cached_posts = _load_cache(CACHE_FILE_POSTS)
        if cached_posts is not None:
            print("Using cached Instagram posts")
            return cached_posts[:3]
    
    print("Cache invalid or missing, scraping Instagram posts...")
    
    # Try to scrape fresh data
    posts = _scrape_instagram_posts()
    
    # If scraping fails or returns insufficient posts, use fallback
    if len(posts) < 3:
        fallback_posts = _get_fallback_posts()
        needed_posts = 3 - len(posts)
        posts.extend(fallback_posts[:needed_posts])
    
    # Save to cache
    final_posts = posts[:3]
    _save_cache(CACHE_FILE_POSTS, final_posts)
    
    return final_posts


def get_cached_events() -> List[Dict[str, Any]]:
    """Get Facebook events with caching (max once per day)"""
    # Check if cache is valid
    if _is_cache_valid(CACHE_FILE_EVENTS):
        cached_events = _load_cache(CACHE_FILE_EVENTS)
        if cached_events is not None:
            print("Using cached Facebook events")
            return cached_events
    
    print("Cache invalid or missing, using fallback events...")
    
    # For now, we're using static events as Facebook scraping is complex
    # In the future, this could be enhanced to scrape Facebook events
    events = _get_fallback_events()
    
    # Save to cache
    _save_cache(CACHE_FILE_EVENTS, events)
    
    return events


def clear_cache() -> None:
    """Clear both cache files"""
    for cache_file in [CACHE_FILE_POSTS, CACHE_FILE_EVENTS]:
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                print(f"Cleared cache file: {cache_file}")
        except Exception as e:
            print(f"Failed to clear cache file {cache_file}: {e}")