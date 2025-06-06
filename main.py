import os
from telegram.ext import ApplicationBuilder, CommandHandler
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

print("BOT_TOKEN:", BOT_TOKEN)  # For testing if token is read correctly

async def start(update, context):
    await update.message.reply_text("Hello! Bot is working.")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is not set!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
