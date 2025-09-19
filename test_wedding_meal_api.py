import requests
import json

# Test the wedding meal API endpoint
url = "http://localhost:5000/api/family/wedding-meal"
headers = {"Content-Type": "application/json"}

# First, let's get a guest ID from the LAMP family
import os
from dotenv import load_dotenv
from utils.db import normalize_database_url
import psycopg
from psycopg.rows import dict_row

load_dotenv()
DATABASE_URL = normalize_database_url(os.getenv('DATABASE_URL'))

with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT id, name FROM public.guests WHERE upper(family_id) = %s AND wedding_meal = 1 LIMIT 1', ('LAMP',))
        row = cur.fetchone()
        if row:
            guest_id = str(row['id'])
            guest_name = row['name']
            print(f"Testing with guest: {guest_name} (ID: {guest_id})")

            # Test updating to Beef (5)
            payload = {
                "family_code": "LAMP",
                "guest_id": guest_id,
                "meal_preference": 5
            }

            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                print(f"Response status: {response.status_code}")
                print(f"Response: {response.json()}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("No suitable guest found for testing")