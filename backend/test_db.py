import psycopg
import os
import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def check():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL in environment!")
        return
        
    print(f"Connecting to {db_url}...")
    try:
        conn = await psycopg.AsyncConnection.connect(db_url)
    except Exception as e:
        print("Connection failed:", e)
        return
        
    cur = conn.cursor()
    
    # Check if table exists
    try:
        await cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'activities';")
        schema = await cur.fetchall()
        print("Schema:", schema)
    except Exception as e:
        print("Error checking schema:", e)
        
    # Check users
    try:
        await cur.execute('SELECT * FROM users LIMIT 1;')
        user = await cur.fetchone()
        print("User:", user)
    except Exception as e:
        print("Error fetching user:", e)
        user = None
    
    if user:
        uid = user[0]
        print(f"Checking activities for {uid}")
        try:
            await cur.execute('SELECT * FROM activities WHERE user_id = %s LIMIT 5;', (uid,))
            acts = await cur.fetchall()
            print("Activities:", acts)
        except Exception as e:
            print("Error fetching activities:", e)
        
        # Group by check
        try:
            await cur.execute("SELECT logged_at::date as date_str, SUM(co2_kg) as total_kg FROM activities WHERE user_id = %s GROUP BY logged_at::date", (uid,))
            group_res = await cur.fetchall()
            print("Group by result:", group_res)
        except Exception as e:
            print("Error group by:", e)
            
    await conn.close()

asyncio.run(check())
