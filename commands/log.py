from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet

# Define the /log command
async def log_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Parse the input (e.g., "/log $50 on food")
        text = update.message.text
        parts = text.split(maxsplit=3)
        if len(parts) < 4:
            await update.message.reply_text("Invalid format. Use: /log $<amount> on <description>")
            return

        amount = parts[1].strip("$")  # Remove the dollar sign
        description = parts[3]

        # Validate the amount
        try:
            float(amount)  # Ensure the amount is a valid number
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid number.")
            return

        # Get the current date
        date = datetime.now().strftime("%Y-%m-%d")

        # Save the expense to Google Sheets
        sheet = get_google_sheet()
        sheet.append_row([date, description, amount])

        # Confirm the expense was logged
        await update.message.reply_text(f"Expense logged: ${amount} on {description}")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}") 