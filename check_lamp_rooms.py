import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from utils.db import normalize_database_url

load_dotenv()
DATABASE_URL_RAW = os.getenv('DATABASE_URL')
DATABASE_URL = normalize_database_url(DATABASE_URL_RAW) if DATABASE_URL_RAW else None

if DATABASE_URL:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, friday_room, saturday_room FROM public.guests WHERE upper(family_id) = 'LAMP'")
            rows = cur.fetchall()
            for row in rows:
                print(f'{row["name"]}: friday_room={row["friday_room"]}, saturday_room={row["saturday_room"]}')
else:
    print('DATABASE_URL not configured')