import psycopg
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL")
        return
        
    print(f"Connecting to {db_url}...")
    conn = await psycopg.AsyncConnection.connect(db_url)
    cur = conn.cursor()
    
    # Check users
    await cur.execute('SELECT * FROM users LIMIT 1;')
    user = await cur.fetchone()
    print("User:", user)
    
    if user:
        uid = user[0]
        print(f"Checking activities for {uid}")
        await cur.execute('SELECT * FROM activities WHERE user_id = %s LIMIT 5;', (uid,))
        acts = await cur.fetchall()
        print("Activities:", acts)
        
        # Check to_char
        await cur.execute("SELECT to_char(logged_at, 'YYYY-MM'), to_char(CURRENT_TIMESTAMP, 'YYYY-MM') FROM activities LIMIT 1;")
        res = await cur.fetchone()
        print("to_char result:", res)
        
        # Group by
        await cur.execute("SELECT logged_at::date as date_str, SUM(co2_kg) as total_kg FROM activities WHERE user_id = %s GROUP BY logged_at::date", (uid,))
        group_res = await cur.fetchall()
        print("Group by result:", group_res)
        if group_res:
            print("Type of date_str:", type(group_res[0][0]))
            print("Type of total_kg:", type(group_res[0][1]))
            
    await conn.close()

asyncio.run(check())
