from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet
from utils.nlp import nlp

async def query_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text[len("/query "):].strip()
        if not text:
            await update.message.reply_text("Invalid format. Use: /query <your question>")
            return

        doc = nlp(text)
        category = None
        month = None
        for ent in doc.ents:
            if ent.label_ == "DATE":
                month = ent.text.capitalize()
            elif ent.label_ in ["PRODUCT", "NOUN"]:
                category = ent.text.lower()

        if not category:
            for token in doc:
                if token.text.lower() in ["food", "travel", "groceries", "utilities"]:
                    category = token.text.lower()
                    break

        if not month:
            for token in doc:
                if token.text.lower() in [
                    "january", "february", "march", "april", "may", "june",
                    "july", "august", "september", "october", "november", "december"
                ]:
                    month = token.text.capitalize()
                    break

        if not month:
            month = datetime.now().strftime("%B")

        sheet = get_google_sheet()
        rows = sheet.get_all_records()
        total = 0
        for row in rows:
            row_date = datetime.strptime(row["Date"], "%Y-%m-%d")
            if row_date.strftime("%B") == month:
                if not category or row["Description"].lower() == category:
                    total += float(row["Amount"])

        if category:
            response = f"You spent ${total:.2f} on {category} in {month}."
        else:
            response = f"Total expenses in {month}: ${total:.2f}"
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")