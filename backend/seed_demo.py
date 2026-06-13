import asyncio
import datetime
import json
from pydantic_settings import BaseSettings

import aiosqlite

DB_PATH = "./carbonsense.db"

async def seed_demo_data():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get ALL users
        async with db.execute("SELECT id FROM users") as cursor:
            users = await cursor.fetchall()
            
        if not users:
            print("No users found. Please complete the onboarding first.")
            return
            
        for user in users:
            user_id = user["id"]
            now = datetime.datetime.now()
            valid_until = now + datetime.timedelta(days=7)

            print(f"Seeding data for user: {user_id}")
            
            # Clean up existing data for this user to avoid duplicates
            await db.execute("DELETE FROM activities WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM insights_cache WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM missions WHERE user_id = ?", (user_id,))
            
            # 1. Insert Activities
            activities = [
                ("transport", "car_petrol", 150, "km", 34.5, now - datetime.timedelta(days=2)),
                ("energy", "electricity", 120, "kWh", 85.2, now - datetime.timedelta(days=5)),
                ("food", "chicken", 2, "meals", 12.0, now - datetime.timedelta(days=1)),
                ("shopping", "clothing", 1, "items", 15.0, now - datetime.timedelta(days=10)),
                ("transport", "flight_domestic", 1, "flights", 150.0, now - datetime.timedelta(days=15)),
            ]
            
            for act in activities:
                await db.execute(
                    """
                    INSERT INTO activities (user_id, category, type, amount, unit, co2_kg, logged_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, act[0], act[1], act[2], act[3], act[4], act[5].strftime("%Y-%m-%d %H:%M:%S"))
                )
                
            # 2. Insert Insights Cache (AI Plan)
            planner_content = {
                "strategies": [
                    {
                        "title": "Meat-Free Days",
                        "action": "Swap beef or pork for beans or tofu twice weekly.",
                        "category": "food",
                        "monthly_saving_kg": 30.0,
                        "difficulty": "medium",
                        "timeframe_days": 30,
                        "mission_type": True
                    },
                    {
                        "title": "LED Bulb Swap",
                        "action": "Replace 5 incandescent bulbs with LEDs.",
                        "category": "energy",
                        "monthly_saving_kg": 15.0,
                        "difficulty": "easy",
                        "timeframe_days": 14,
                        "mission_type": True
                    }
                ]
            }
            
            await db.execute(
                """
                INSERT INTO insights_cache (user_id, agent_type, content_json, is_valid, generated_at, valid_until)
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (user_id, "planner", json.dumps(planner_content), now.strftime("%Y-%m-%d %H:%M:%S"), valid_until.strftime("%Y-%m-%d %H:%M:%S"))
            )

            analyst_content = {
                "primary_hotspot": "energy",
                "findings": ["Energy usage is highest."]
            }
            await db.execute(
                """
                INSERT INTO insights_cache (user_id, agent_type, content_json, is_valid, generated_at, valid_until)
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (user_id, "analyst", json.dumps(analyst_content), now.strftime("%Y-%m-%d %H:%M:%S"), valid_until.strftime("%Y-%m-%d %H:%M:%S"))
            )
                
            # 3. Insert Missions
            missions = [
                ("Meat-Free Days", "Swap beef or pork for beans or tofu twice weekly.", "food", 30.0, 200, "active"),
                ("LED Bulb Swap", "Replace 5 incandescent bulbs with LEDs.", "energy", 15.0, 100, "pending"),
                ("Public Transit Commute", "Take the bus or train to work twice this week.", "transport", 25.0, 150, "completed"),
            ]
            
            for m in missions:
                await db.execute(
                    """
                    INSERT INTO missions (user_id, title, description, category, target_reduction_kg, eco_points_reward, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, m[0], m[1], m[2], m[3], m[4], m[5], now.strftime("%Y-%m-%d %H:%M:%S"))
                )
                
            # Update user Eco Points for the completed mission
            await db.execute(
                "UPDATE users SET eco_points = 150 WHERE id = ?",
                (user_id,)
            )
                
        await db.commit()
        print("Demo data seeded successfully for all users!")

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
