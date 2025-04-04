from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

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

# Main function to start the bot
def main() -> None:
    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
    application = Application.builder().token("8157604700:AAFTME43uhOKEakaCRakd4tmx0X11SNv7yc").build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()