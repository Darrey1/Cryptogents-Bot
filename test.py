from databases import Database
from typing import List, Union, Dict
from configs import DATABASE_URL
import asyncio

database = Database("")



async def init_db():
    print("Connecting to the database...")
    await database.connect()


query = "ALTER TABLE Users ADD COLUMN weex_uuid VARCHAR(100) UNIQUE;"


async def execute_query():
    try:
        await init_db()
        await database.execute(query)
        print("Query executed successfully.")
    except Exception as e:
        print(f"Error executing query: {e}")
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(execute_query())

