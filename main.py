import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
import csv
import io
import json

# Load Google Sheets credentials securely
def get_google_sheet():
    # Load credentials from the environment variable
    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_json:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
    
    try:
        # Parse the JSON string into a dictionary
        creds_dict = json.loads(creds_json)
        print("Parsed Credentials:", creds_dict)  # Debugging: Print parsed credentials

        # Define the required OAuth scopes
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        print("Scopes:", scopes)  # Debugging: Print scopes

        # Authenticate using the credentials and scopes
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Expenses").sheet1
        return sheet
    except Exception as e:
        print("An error occurred while loading Google Sheets credentials:", str(e))  # Debugging: Print detailed error
        raise ValueError(f"Failed to load Google Sheets credentials: {str(e)}")
    
    
# Define the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to the Accounting Bot! Use /help to see available commands.")

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

# Define the /query command
async def query_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Parse the input (e.g., "/query How much did I spend on food in April?")
        text = update.message.text
        if "on" not in text or "in" not in text:
            await update.message.reply_text("Invalid format. Use: /query How much did I spend on <category> in <month>?")
            return

        # Extract category and month from the input
        parts = text.split("on")[1].strip()  # Split after "on"
        category = parts.split("in")[0].strip()  # Extract the category
        month = parts.split("in")[1].strip()     # Extract the month
        month = month.replace("?", "").strip()   # Remove any question marks or extra spaces

        # Fetch all rows from the Google Sheet
        sheet = get_google_sheet()
        rows = sheet.get_all_records()  # Returns a list of dictionaries (each row as a dictionary)

        # Debug information
        debug_info = f"Searching for: Category='{category}', Month='{month}'\n"
        debug_info += f"Found {len(rows)} total records\n"

        # Filter rows by category and month
        total = 0
        matching_rows = []
        for row in rows:
            row_date = datetime.strptime(row["Date"], "%Y-%m-%d")  # Parse the date
            row_month = row_date.strftime("%B").lower()
            row_category = row["Description"].lower()
            if row_category == category.lower() and row_month == month.lower():
                total += float(row["Amount"])
                matching_rows.append(row)

        debug_info += f"Found {len(matching_rows)} matching records\n"
        if matching_rows:
            debug_info += "Matching records:\n"
            for row in matching_rows:
                debug_info += f"- {row['Date']}: ${row['Amount']} on {row['Description']}\n"

        # Send the result to the user
        await update.message.reply_text(
            f"You spent ${total:.2f} on {category} in {month}.\n\n"
            f"Debug information:\n{debug_info}"
        )
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

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

# Main function to start the bot
def main() -> None:
    print("BOT_TOKEN:", os.getenv("BOT_TOKEN"))
    print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set.")

    # Build the Telegram bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("log", log_expense))
    application.add_handler(CommandHandler("query", query_expense))
    application.add_handler(CommandHandler("export", export_expenses))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()