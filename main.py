import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
import csv
import io
import json
import spacy

# Load spaCy's English language model
nlp = spacy.load("en_core_web_sm")

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
    

# Import command handlers
from commands.start import start
from commands.help import help_command
from commands.log import log_expense
from commands.query import query_expense
from commands.export import export_expenses

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
