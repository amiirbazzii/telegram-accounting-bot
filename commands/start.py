from telegram import Update
from telegram.ext import ContextTypes

# Define the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to the Accounting Bot! Use /help to see available commands.") 