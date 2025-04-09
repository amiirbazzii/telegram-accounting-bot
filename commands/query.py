# commands/query.py
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet
from utils.nlp import extract_entities_and_intent

async def query_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text.strip()
        if text.startswith("/query"):
            text = text[len("/query"):].strip()
        if not text:
            await update.message.reply_text("Please ask something (e.g., 'How much did I spend on food?')")
            return

        intent, amount, description, category, related_to, date = extract_entities_and_intent(text)
        
        # Default to "query" intent if no amount (logging requires amount)
        if intent != "query" and not amount:
            intent = "query"

        if intent != "query":
            await update.message.reply_text("To log an expense, say something like 'I spent $10 on food'.")
            return

        # Determine the month from the date
        query_date = datetime.strptime(date, "%Y-%m-%d")
        month = query_date.strftime("%B")

        # Fetch and filter expenses asynchronously
        sheet = await asyncio.to_thread(get_google_sheet)
        rows = await asyncio.to_thread(sheet.get_all_records)
        
        # Filtering in Python remains for simplicity
        total = 0
        for row in rows:
            try:
                # Add basic error handling for date parsing and amount conversion
                row_date = datetime.strptime(row["Date"], "%Y-%m-%d")
                if row_date.strftime("%B") == month:
                    if not category or str(row["Category"]).lower() == category.lower(): # Ensure case-insensitive compare
                        total += float(row["Amount"])
            except (ValueError, KeyError) as parse_error:
                print(f"Skipping row due to error: {parse_error} - Row: {row}") # Log error instead of crashing
                continue # Skip malformed rows

        if category:
            response = f"You spent ${total:.2f} on {category} in {month}."
        else:
            response = f"Total expenses in {month}: ${total:.2f}"
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"Sorry, I hit an error: {str(e)}")