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
import ast
from db.database import database
from telegram.constants import ChatMemberStatus
import os 
from telegram.ext import  CallbackContext, ContextTypes
from db.database import toggle_is_member_field, find_user_ids
logger = logging.getLogger(__name__)

from configs import GROUP_CHAT_ID, ADMIN_USER_ID,SOURCE_CHAT_ID, DEST_CHAT_ID, SOURCE_CHAT_TITLE
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

🎥 <a href="https://www.youtube.com/watch?v=HiNSaaEM1us">Watch this quick guide</a>

👇 Then click "Join Crypto Gents" to continue.
"""


        keyboard = [
                [InlineKeyboardButton("Join Crypto Gents", web_app=WebAppInfo(url="https://web-production-99317.up.railway.app/"))]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="HTML", text=message,reply_markup=reply_markup)
        logger.info(f"Sent start message to {user.id} in chat {chat.id} at {datetime.now()}")
        user_data[user.id][f'start_msg_{user.id}'] = msg.id
            
    except Exception as e:
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
        # await context.bot.send_message(
        #     chat_id=chat_id,
        #     text=f"👋 Welcome <b>{user.full_name}</b>!",
        #     parse_mode="HTML"
        # )
        
        
    elif old_status == "member" and new_status in ["left", "kicked"]:
        print(f"❌ User left or was removed: ID={user.id}, Username=@{user.username}, Name={user.full_name}")
        await toggle_is_member_field(user.id)
        # await context.bot.send_message(
        #     chat_id=chat_id,
        #     text=f"👋 <b>{user.username}</b> has left or was removed from the group.",
        #     parse_mode="HTML"
        # )
        
        
        


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.username not in ['JamyMe', 'CryptoPushak', 'bitaddict', 'SirCharbel','hodge100', 'anthonydab', 'develord346']:
        return await update.message.reply_text("❌ You are not authorized to use this command.")

    try:
        query = """
        SELECT * FROM Users
        WHERE 
            id IS NOT NULL AND
            email IS NOT NULL AND
            username IS NOT NULL AND
            telegram_id IS NOT NULL AND
            blofin_uuid IS NOT NULL AND
            is_group_member = TRUE AND
            created_at IS NOT NULL AND
            updated_at IS NOT NULL
        """
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






async def download_new_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.username not in ['JamyMe', 'CryptoPushak', 'bitaddict', 'SirCharbel','hodge100', 'anthonydab', 'develord346']:
        return await update.message.reply_text("❌ You are not authorized to use this command.")

    try:
        query = """
        SELECT * FROM Users
        WHERE 
            is_group_member = FALSE
            OR blofin_uuid IS NULL
            OR email IS NULL
        """
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




        
        

async def warn_command_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = context.user_data
    if user.username not in ['JamyMe', 'CryptoPushak', 'bitaddict', 'SirCharbel','hodge100', 'anthonydab', 'develord346']:
        return await update.message.reply_text("❌ You are not authorized to use this command.")
    
    if user.id not in user_data:
        user_data[user.id] = {}
        
    args = context.args if context.args else []
    print(args)
    if not args:
        return await update.message.reply_text("❌ Usage: `/warn <user_id or username or blofin_uuid>`", parse_mode="Markdown")
    
    if len(args) > 2: 
        await update.message.reply_text("📢 Please enter the warn message to broadcast.")
    else:
        await update.message.reply_text("📢 Please enter the warn message to send to the user.")
        
    user_data[user.id]['state'] = f'warn|{args}'
    



async def kick_command_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = context.user_data
    if user.username not in ['JamyMe', 'CryptoPushak', 'bitaddict', 'SirCharbel','hodge100', 'anthonydab', 'develord346']:
        return await update.message.reply_text("❌ You are not authorized to use this command.")
    
    if user.id not in user_data:
        user_data[user.id] = {}
        
    args = context.args if context.args else []
    print(args)
    if not args:
        return await update.message.reply_text("❌ Usage: `/unkick <user_id or username or blofin_uuid>`", parse_mode="Markdown")
    
    if len(args) > 2: 
        await update.message.reply_text("📢 Please enter the message to notify them after being removed from the group .")
    else:
        await update.message.reply_text("📢 Please enter the message to notify the user after being removed from the group.")
        
    user_data[user.id]['state'] = f'kick|{args}'
    
    

async def unkick_command_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = context.user_data
    if user.username not in ['JamyMe', 'CryptoPushak', 'bitaddict', 'SirCharbel','hodge100', 'anthonydab', 'develord346']:
        return await update.message.reply_text("❌ You are not authorized to use this command.")
    
    if user.id not in user_data:
        user_data[user.id] = {}
        
    args = context.args if context.args else []
    print(args)
    if not args:
        return await update.message.reply_text("❌ Usage: `/unkick <user_id or username or blofin_uuid>`", parse_mode="Markdown")
    
    if len(args) > 2: 
        await update.message.reply_text("📢 Please enter the message to notify them that they have been re-added to the group..")
    else:
        await update.message.reply_text("📢 Please enter the message to notify the user after being re-added to the group.")
        
    user_data[user.id]['state'] = f'unkick|{args}'
        




async def handle_user_reply(update: Update, context: CallbackContext):
    if not update.message:  # Ignore non-message updates
        return
    user = update.message.from_user
    chat = update.effective_chat
    print(f"{chat.title}-{chat.id} ")

    try:
        state = context.user_data[user.id]['state']
        state_text = state.split("|")
    except Exception:
        state_text = [None, None]

    if state_text[0] in ['warn', 'kick', 'unkick']:
        if chat.type != 'private':
            return
        
        warn_user = state_text[-1] if len(state_text) > 1 else None
        if not warn_user:
            return

        try:
            warn_user_list = ast.literal_eval(warn_user)
            if not isinstance(warn_user_list, list):
                return await context.bot.send_message(chat_id=chat.id, text="⚠️ Invalid user list format.")
        except Exception:
            return await context.bot.send_message(chat_id=chat.id, text="⚠️ Failed to process user list.")

        warn_user_ids = await find_user_ids(warn_user_list)
        message = update.message.text.strip()

        if state_text[0] == 'warn':
            failed_ids = []
            for uid in warn_user_ids:
                try:
                    print(f"Sending to {uid}")
                    await context.bot.send_message(chat_id=int(uid), parse_mode="HTML", text=f"⚠️ {message}")
                except Exception as e:
                    print(f"❌ Failed to message {uid}: {e}")
                    failed_ids.append(uid)
            
            context.user_data[user.id]['state'] = None  
            
            if failed_ids:
                return await context.bot.send_message(
                    chat_id=chat.id,
                    parse_mode="HTML",
                    text=f"⚠️ Couldn't message {len(failed_ids)} user(s). Others received the warning."
                )
            return await context.bot.send_message(chat_id=chat.id, parse_mode="HTML", text="✅ Message sent successfully.")


        elif state_text[0] == 'kick':
            failed_ids = []

            for uid in warn_user_ids:
                try:
                    member_status = await context.bot.get_chat_member(GROUP_CHAT_ID, int(uid))
                    if member_status.status not in ["administrator", "creator"]:
                        await context.bot.ban_chat_member(GROUP_CHAT_ID, int(uid))
                        await context.bot.send_message(chat_id=int(uid), parse_mode="HTML", text=f"🚭 {message}")
                except Exception as e:
                    print(f"❌ Failed to kick/message {uid}: {e}")
                    failed_ids.append(uid)

            context.user_data[user.id]['state'] = None

            if failed_ids:
                return await context.bot.send_message(
                    chat_id=chat.id,
                    parse_mode="HTML",
                    text=f"⚠️ Failed to kick or notify {len(failed_ids)} user(s)."
                )
            return await context.bot.send_message(
                chat_id=chat.id,
                parse_mode="HTML",
                text="✅ Users have been removed from the group and also being notify."
            )


        elif state_text[0] == 'unkick':
            failed_ids = []

            for uid in warn_user_ids:
                try:
                    member_status = await context.bot.get_chat_member(GROUP_CHAT_ID, int(uid))
                    if member_status.status not in ["administrator", "creator"]:
                        await context.bot.unban_chat_member(GROUP_CHAT_ID, int(uid))
                        invite_link = None
                        try:
                            invite_link = await context.bot.export_chat_invite_link(chat_id=GROUP_CHAT_ID)
                        except:
                            pass  # Ignore if unable to generate invite link

                        message = f"{message}.\n\n"
                        if invite_link:
                            message += f'<a href="{invite_link}">Please click here to join back</a>'

                        try:
                           await context.bot.send_message(chat_id=int(uid), parse_mode="HTML", text=f"🎉 {message}")
                        except Exception as e:
                            print(f"⚠️ Could not send invite message to {int(uid)}: {e}")
                        
                except Exception as e:
                    #hi
                    print(f"❌ Failed to unkick/message {uid}: {e}")
                    failed_ids.append(uid)

            context.user_data[user.id]['state'] = None

            if failed_ids:
                return await context.bot.send_message(
                    chat_id=chat.id,
                    parse_mode="HTML",
                    text=f"⚠️ Failed to unkick or notify {len(failed_ids)} user(s)."
                )
            return await context.bot.send_message(
                chat_id=chat.id,
                parse_mode="HTML",
                text="✅ Users have been enable to join the group and also being notify."
            )





async def forward_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward images from source group to destination group."""
    print(str(update.effective_chat.title).upper())
    if update.effective_chat.id == SOURCE_CHAT_ID and str(update.effective_chat.title).upper() == SOURCE_CHAT_TITLE:
        try:
            await update.message.forward(chat_id=DEST_CHAT_ID)
            print(f"✅ Forwarded image from {SOURCE_CHAT_ID} to {DEST_CHAT_ID}")
        except Exception as e:
            print(f"⚠ Error forwarding image: {e}")