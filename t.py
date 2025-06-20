from telegram import Bot
import asyncio

# bot = Bot(token="7956036798:AAFJ2O0U7wp6yxMqcO65Qq5SLmleJEV9_3c")
# async def testing():
        
#     chat = await bot.get_chat("@hietedkfines")
#     print(chat.id)  # This will print the channel ID
    
# asyncio.run(testing())


from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    invite_link = await context.bot.export_chat_invite_link(chat.id)
    print(f"Invite Link: {invite_link}")
    print(f"Chat ID: {chat.id}, Title: {chat.title}")

app = Application.builder().token("7681260284:AAFBq1dx0oagOuvRsBUYBQBgcvUlL0xsO1c").build()
app.add_handler(MessageHandler(filters.ALL, handle_message))
app.run_polling()



# -1001322675452