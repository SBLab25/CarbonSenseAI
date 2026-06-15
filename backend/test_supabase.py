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
    
    # 3. Test queries
    try:
        await cur.execute("SELECT to_char(logged_at, 'YYYY-MM'), to_char(CURRENT_TIMESTAMP, 'YYYY-MM') FROM activities LIMIT 1;")
        print("to_char test:", await cur.fetchall())
    except Exception as e:
        print("to_char error:", e)
        await conn.rollback()
        
    try:
        await cur.execute("SELECT logged_at::date as date_str, SUM(co2_kg) as total_kg FROM activities GROUP BY logged_at::date LIMIT 5;")
        print("group by date test:", await cur.fetchall())
    except Exception as e:
        print("group by error:", e)
        
    await conn.close()

asyncio.run(check())
