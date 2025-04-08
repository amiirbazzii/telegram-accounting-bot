import csv
import io
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet

# Define the /export command
async def export_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Fetch all rows from the Google Sheet
        sheet = get_google_sheet()
        rows = sheet.get_all_records()  # Returns a list of dictionaries (each row as a dictionary)

        if not rows:
            await update.message.reply_text("No expenses found to export.")
            return

        # Create a CSV file in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

        # Prepare the CSV file for sending
        output.seek(0)  # Move the pointer to the beginning of the file
        await update.message.reply_document(
            document=output,
            filename="expenses.csv",
            caption="Here is your exported expenses file."
        )

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}") 