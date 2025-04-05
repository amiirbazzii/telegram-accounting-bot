
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials

# Load Google Sheets credentials securely
def get_google_sheet():
    # Define the correct OAuth scopes
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    # Authenticate using the environment variable
    creds = Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), scopes=scope)
    client = gspread.authorize(creds)
    # Open the Google Sheet by name
    sheet = client.open("Expenses").sheet1
    return sheet

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
        "/query - Query expenses (e.g., /query How much did I spend on food?)\n"
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

        # Get the current date
        date = datetime.now().strftime("%Y-%m-%d")

        # Save the expense to Google Sheets
        sheet = get_google_sheet()
        sheet.append_row([date, description, amount])

        # Confirm the expense was logged
        await update.message.reply_text(f"Expense logged: ${amount} on {description}")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

# Main function to start the bot
def main() -> None:
    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
    application = Application.builder().token("8157604700:AAFTME43uhOKEakaCRakd4tmx0X11SNv7yc").build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("log", log_expense))

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()