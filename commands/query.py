from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet
from utils.nlp import nlp

# Define the /query command with improved spaCy integration
async def query_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Parse the input (e.g., "/query How much did I spend on food in April?")
        text = update.message.text[len("/query "):].strip()
        if not text:
            await update.message.reply_text("Invalid format. Use: /query <your question>")
            return

        # Process the text with spaCy
        doc = nlp(text)

        # Extract entities
        category = None
        month = None
        for ent in doc.ents:
            if ent.label_ == "DATE":
                month = ent.text.capitalize()  # Extract month (e.g., "April")
            elif ent.label_ in ["PRODUCT", "NOUN"]:
                category = ent.text.lower()  # Extract category (e.g., "food")

        # Fallback: Simple keyword matching for category and month
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

        # Default to the current month if no month is provided
        if not month:
            month = datetime.now().strftime("%B")  # Current month (e.g., "October")

        # Fetch all rows from the Google Sheet
        sheet = get_google_sheet()
        rows = sheet.get_all_records()

        # Filter rows by category and month
        total = 0
        for row in rows:
            row_date = datetime.strptime(row["Date"], "%Y-%m-%d")  # Parse the date
            if row_date.strftime("%B") == month:
                if not category or row["Description"].lower() == category:
                    total += float(row["Amount"])

        # Construct the response
        if category:
            response = f"You spent ${total:.2f} on {category} in {month}."
        else:
            response = f"Total expenses in {month}: ${total:.2f}"

        # Send the result to the user
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}") 