import os
from dotenv import load_dotenv
from utils.db import normalize_database_url
import psycopg
from psycopg.rows import dict_row

load_dotenv()
DATABASE_URL = normalize_database_url(os.getenv('DATABASE_URL'))

with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT name, wedding_meal FROM public.guests WHERE upper(family_id) = %s', ('LAMP',))
        rows = cur.fetchall()
        for row in rows:
            print(f'{row["name"]}: wedding_meal = {row["wedding_meal"]}')