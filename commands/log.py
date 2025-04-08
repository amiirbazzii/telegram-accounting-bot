from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet

async def log_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text
        parts = text.split(maxsplit=3)
        if len(parts) < 4:
            await update.message.reply_text("Invalid format. Use: /log $<amount> on <description>")
            return

        amount = parts[1].strip("$")
        description = parts[3]

        try:
            float(amount)
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid number.")
            return

        date = datetime.now().strftime("%Y-%m-%d")
        sheet = get_google_sheet()
        sheet.append_row([date, description, amount])
        await update.message.reply_text(f"Expense logged: ${amount} on {description}")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")