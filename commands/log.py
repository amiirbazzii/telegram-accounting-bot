# commands/log.py
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet
from utils.nlp import extract_entities_and_intent

async def log_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text.strip()
        if text.startswith("/log"):
            text = text[len("/log"):].strip()
        if not text:
            await update.message.reply_text("Please tell me what you spent (e.g., 'I spent $20 on a purse for my wife').")
            return

        intent, amount, description, category, related_to, date = extract_entities_and_intent(text)

        if amount is None:
            await update.message.reply_text("Please include an amount (e.g., 'I spent $20 on a purse').")
            return

        sheet = await asyncio.to_thread(get_google_sheet)
        await asyncio.to_thread(
            sheet.append_row,
            [description, date, str(amount), category, related_to or ""]
        )

        response = f"Expense logged: {description} for ${amount} ({category})"
        if related_to:
            response += f" for {related_to}"
        response += f" on {date}"
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"Oops, something went wrong: {str(e)}")