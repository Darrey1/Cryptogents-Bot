import logging
from telegram import (Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ChatPermissions,
    ReplyKeyboardMarkup, 
    KeyboardButtonRequestChat,
    KeyboardButton,
    WebAppInfo,
    ReplyKeyboardMarkup,
    ChatMember,
    ChatAdministratorRights,
    Bot,
    ChatMemberUpdated
    
)
import csv
import io
from db.database import database
from telegram.constants import ChatMemberStatus
import os 
from telegram.ext import  CallbackContext, ContextTypes
from db.database import toggle_is_member_field
logger = logging.getLogger(__name__)

from configs import ADMIN_USER_ID
from datetime import datetime

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update._effective_chat
        bot_username = context.bot.username 
        user_data = context.user_data
        if user.id not in user_data:
            user_data[user.id] = {}
            
        message = """
🚀 Welcome to Crypto Gents 

To Join:

Step 1: Register with BloFin
Step 2: Submit your Email Address
Step 3: Gain Instant Access

🎥 Watch this quick guide:

👆 Then click "Join Crypto Gents" to access via the in-app browser.

"""

        keyboard = [
                [InlineKeyboardButton("Join Crypto Gents", web_app=WebAppInfo(url="https://web-production-99317.up.railway.app/"))]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="HTML", text=message,reply_markup=reply_markup)
        logger.info(f"Sent start message to {user.id} in chat {chat.id} at {datetime.now()}")
        user_data[user.id][f'start_msg_{user.id}'] = msg.id
            
    except Exception as e:
        print(e)
        await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="HTML", text=f"ERROR:{str(e)}")
        



async def get_admins_and_owner(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Fetch all admins and the owner of a group or channel."""
    try:
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = []
        owner_id = None

        for admin in chat_admins:
            if admin.status == ChatMember.OWNER:
                owner_id = admin.user.id  # Owner ID
            else:
                admin_ids.append(admin.user.id)  # Admins ID

        return owner_id, admin_ids

    except Exception as e:
        print(f"Error fetching admins: {e}")
        return None, []
    
    
    



async def bot_removed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member_update = update.my_chat_member
    if chat_member_update is None:
        print("No my_chat_member data received")
        return

    old_status = chat_member_update.old_chat_member.status
    new_status = chat_member_update.new_chat_member.status
    user = chat_member_update.new_chat_member.user

    if user.is_bot or user.id == context.bot.id:
        return

    chat = chat_member_update.chat
    current_chat_id = chat.id
    chat_title = chat.title
    chat_username = chat.username

    print(f"Bot status changed: {old_status} → {new_status}")
    if old_status == "member" and new_status in ["left", "kicked"]:
        await toggle_is_member_field(user.id)
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"👋 <b>{user.full_name}</b> has left or was removed from the group.",
            parse_mode="HTML"
        )
        print(f"❌ I was removed from the group <b>{chat_title}")
    
    
    

async def verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a captcha for verification when a new member joins."""
    chat = update.effective_chat
    chat_id = chat.id
    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status
    member = update.chat_member.new_chat_member
    user = member.user
    print(f"User {user.id} changed status from {old_status} to {new_status} in chat {chat_id}")
    if old_status in ["left", "kicked"] and new_status == "member":
        await toggle_is_member_field(user.id)
        print(f"✅ User joined: ID={user.id}, Username=@{user.username}, Name={user.full_name}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"👋 Welcome <b>{user.full_name}</b>!",
            parse_mode="HTML"
        )
        
        
    elif old_status == "member" and new_status in ["left", "kicked"]:
        print(f"❌ User left or was removed: ID={user.id}, Username=@{user.username}, Name={user.full_name}")
        await toggle_is_member_field(user.id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"👋 <b>{user.full_name}</b> has left or was removed from the group.",
            parse_mode="HTML"
        )
        
        
        


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        query = "SELECT * FROM Users"
        rows = await database.fetch_all(query)

        if not rows:
            await update.message.reply_text("⚠️ No data found in the Users table.")
            return
        
        columns = rows[0].keys()

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

        output.seek(0)
        filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            filename=filename,
            document=io.BytesIO(output.getvalue().encode('utf-8'))
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error generating CSV: {str(e)}")