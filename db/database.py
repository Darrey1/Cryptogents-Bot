from databases import Database
from typing import List, Union, Dict
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
    
    
    
    
async def find_user_ids(identifiers: List[Union[str, int]]) -> List[str]:
    if not identifiers:
        return []

    result_ids = []
    
    for identifier in identifiers:
        identifier_str = str(identifier).strip()
        query = """
            SELECT telegram_id FROM Users
            WHERE telegram_id = :exact
               OR blofin_uuid = :exact
               OR username = :exact
            LIMIT 1
        """

        values = {
            "exact": identifier_str
        }

        row = await database.fetch_one(query=query, values=values)
        if row and row["telegram_id"]:
            result_ids.append(str(row["telegram_id"]))

    return result_ids

