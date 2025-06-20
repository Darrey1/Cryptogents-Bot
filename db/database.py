from databases import Database
from datetime import datetime
from datetime import time
from configs import DATABASE_URL

database = Database(DATABASE_URL)



async def init_db():
    print("Connecting to the database...")
    await database.connect()
    
    
async def close_connection():
    print("Closing the database connection...")
    await database.disconnect()
    
    
    
async def toggle_is_member_field(user_id):
    try:
        query = "SELECT is_group_member FROM Users WHERE telegram_id = :user_id"
        result = await database.fetch_one(query, {"user_id": str(user_id)})

        if result is None:
            return f"⚠️ User with ID {user_id} not found in the database.Please react to daily checkin message first"

        new_status = not result["is_group_member"]
        
        update_query = "UPDATE Users SET is_group_member = :new_status WHERE telegram_id = :user_id"
        await database.execute(update_query, {"new_status": new_status, "user_id": str(user_id)})
        return new_status
    
    except Exception as e:
        print(f"Error toggling is_group_member for user {user_id}: {e}")
        return False