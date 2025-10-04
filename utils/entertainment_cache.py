import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg
from psycopg.rows import dict_row
from utils.db import normalize_database_url

CACHE_FILE_POSTS = 'entertainment_posts_cache.json'
CACHE_FILE_EVENTS = 'entertainment_events_cache.json'
CACHE_DURATION_HOURS = 24  # Cache for 24 hours

# Get database URL from environment
DATABASE_URL_RAW = os.getenv('DATABASE_URL')
DATABASE_URL = normalize_database_url(DATABASE_URL_RAW) if DATABASE_URL_RAW else None


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


def _get_events_from_database() -> List[Dict[str, Any]]:
    """Get events from the beard_events database table"""
    events = []
    
    if not DATABASE_URL:
        print("Database URL not configured")
        return _get_fallback_events()
    
    try:
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Get upcoming events ordered by timestamp
                cur.execute("""
                    SELECT 
                        name,
                        url,
                        timestamp,
                        location,
                        venueurl,
                        duration,
                        imageurl,
                        responded
                    FROM beard_events
                    WHERE timestamp >= NOW()
                    ORDER BY timestamp ASC
                    LIMIT 10
                """)
                
                rows = cur.fetchall()
                
                for row in rows:
                    # Format the date nicely
                    event_date = row['timestamp']
                    if event_date:
                        formatted_date = event_date.strftime("%a, %d %b at %H:%M")
                    else:
                        formatted_date = "Date TBA"
                    
                    events.append({
                        "title": row['name'] or "BEARD Live",
                        "url": row['url'] or "https://www.facebook.com/bearduk/events",
                        "date": formatted_date,
                        "venue": row['location'] or "Venue TBA",
                        "venue_url": row['venueurl'],
                        "image_url": row['imageurl'],
                        "duration": row['duration'],
                        "responded": row['responded']
                    })
                    
    except Exception as e:
        print(f"Database query failed: {e}")
        # Return fallback events if database query fails
        return _get_fallback_events()
    
    # If no events found, return fallback
    if not events:
        return _get_fallback_events()
    
    return events


def _get_fallback_posts() -> List[Dict[str, Any]]:
    """Get fallback posts when data is unavailable"""
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
    """Get static promotional posts (no longer scraping Instagram)"""
    # Check if cache is valid
    if _is_cache_valid(CACHE_FILE_POSTS):
        cached_posts = _load_cache(CACHE_FILE_POSTS)
        if cached_posts is not None:
            print("Using cached posts")
            return cached_posts[:3]
    
    print("Using static promotional posts...")
    
    # Use static fallback posts
    posts = _get_fallback_posts()
    
    # Save to cache
    final_posts = posts[:3]
    _save_cache(CACHE_FILE_POSTS, final_posts)
    
    return final_posts


def get_cached_events() -> List[Dict[str, Any]]:
    """Get events from database with caching"""
    # Check if cache is valid
    if _is_cache_valid(CACHE_FILE_EVENTS):
        cached_events = _load_cache(CACHE_FILE_EVENTS)
        if cached_events is not None:
            print("Using cached events")
            return cached_events
    
    print("Fetching events from database...")
    
    # Get events from database
    events = _get_events_from_database()
    
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