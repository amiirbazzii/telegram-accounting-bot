import os
from telegram.ext import Application, CommandHandler

# Import command handlers from commands package
from commands.start import start
from commands.help import help_command
from commands.log import log_expense
from commands.query import query_expense
from commands.export import export_expenses

def main() -> None:
    # Check environment variables (mask sensitive data)
    print("BOT_TOKEN:", "Set" if os.getenv("BOT_TOKEN") else "Not set")
    print("GOOGLE_APPLICATION_CREDENTIALS:", "Set" if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") else "Not set")

    # Load bot token
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set.")

    # Initialize the Telegram bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("log", log_expense))
    application.add_handler(CommandHandler("query", query_expense))
    application.add_handler(CommandHandler("export", export_expenses))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()