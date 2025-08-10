import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
    CallbackQueryHandler    
)
from db.database import init_db, close_connection
from configs import BOT_TOKEN
from bot.command import (
    start_handler, 
    verification, 
    bot_removed,
    download_command, 
    handle_user_reply,
    warn_command_func,
    kick_command_func,
    unkick_command_func,
    download_new_user_command,
    forward_images
)
from bot.task import background_checkup_task
from configs import SOURCE_CHAT_ID
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)



async def background_task(context):
    """
    Task to be scheduled in the JobQueue.
    Logs admin IDs of the private channel every 30 minutes.
    """
    logger.info("Running cleanup task...")
    try:
        print("this task is scheduled to run every 30 minutes")
        await background_checkup_task(context)
    except Exception as e:
        logger.error(f"Failed to retrieve chat administrators: {e}")
        
        

async def init_db_(application):
    await init_db()
    print("✅ Database connected.")

async def close_connection_(application):
    await close_connection()
    print("🔌 Database disconnected.")

def main() -> None:
    application = (
    Application.builder().token(BOT_TOKEN).post_init(init_db_) .post_shutdown(close_connection_).build())
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("download", download_command))
    application.add_handler(CommandHandler("download2", download_new_user_command))
    application.add_handler(CommandHandler("warn", warn_command_func))
    application.add_handler(CommandHandler("kick", kick_command_func))
    application.add_handler(CommandHandler("unkick", unkick_command_func))
    application.add_handler(ChatMemberHandler(bot_removed, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(ChatMemberHandler(verification, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.Chat(SOURCE_CHAT_ID) & filters.PHOTO, forward_images))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_reply))
    job_queue = application.job_queue
    time_to_sleep =  24 * 60 * 60
    job = job_queue.run_repeating(
        background_task, interval=time_to_sleep, first=0 
    )
    logger.info("Scheduled cleanup task to run every 23 hours.")
    
    logger.info("Starting the bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)