import psycopg
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.stdout.reconfigure(encoding='utf-8')

async def check():
    db_url = "postgresql://postgres.zjmyyoczruwewsvgxben:%23QZkHwfWXs5_UWP@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
    conn = await psycopg.AsyncConnection.connect(db_url)
    cur = conn.cursor()
    
    await cur.execute("SELECT * FROM activities ORDER BY logged_at DESC LIMIT 5;")
    from psycopg.rows import dict_row
    cur.row_factory = dict_row
    await cur.execute("SELECT * FROM activities ORDER BY logged_at DESC LIMIT 5;")
    acts = await cur.fetchall()
    for act in acts:
        print(act)
    await conn.close()

asyncio.run(check())
