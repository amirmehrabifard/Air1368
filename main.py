import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# تنظیمات لاگ برای دیدن لاگ‌ها در کنسول
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("7279696446:AAEMrXD2-3PwP3eeMph_alwd5UniUKW_NC0")  # مطمئن شو که توکن رو ست کردی

# هندلر دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(f"Hello, {user_first_name}! Welcome to the bot.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
