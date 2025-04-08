# commands/log.py
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet
from utils.nlp import extract_entities_and_intent

async def log_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text.strip()
        # Remove /log prefix if present (for command compatibility)
        if text.startswith("/log"):
            text = text[len("/log"):].strip()
        if not text:
            await update.message.reply_text("Please tell me what you spent (e.g., 'I spent $20 on food').")
            return

        intent, amount, category, date = extract_entities_and_intent(text)

        # If no clear "log" intent but amount present, assume logging
        if amount is None:
            await update.message.reply_text("Please include an amount (e.g., 'I spent $20 on food').")
            return

        if not category:
            category = "misc"  # Default category

        # Save to Google Sheets
        sheet = get_google_sheet()
        sheet.append_row([date, category, str(amount)])

        await update.message.reply_text(f"Expense logged: ${amount} on {category} for {date}")
    except Exception as e:
        await update.message.reply_text(f"Oops, something went wrong: {str(e)}")