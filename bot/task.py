from configs import DEST_CHAT_ID, BROADCAST_MESSAGE

async def background_checkup_task(context):
    """
    Background task to perform periodic checks or updates.
    This function can be customized to include any logic needed for the bot.
    """
    await context.bot.send_message(
            chat_id=DEST_CHAT_ID,
            parse_mode="HTML",
            text=BROADCAST_MESSAGE
        )
