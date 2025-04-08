from telegram import Update
from telegram.ext import ContextTypes

# Define the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/log - Log an expense (e.g., /log $50 on food)\n"
        "/query - Query expenses (e.g., /query How much did I spend on food in April?)\n"
        "/export - Export expenses as a CSV file"
    ) 