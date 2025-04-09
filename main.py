# main.py
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Import command handlers
from commands.start import start
from commands.help import help_command
from commands.log import log_expense
from commands.query import query_expense
from commands.export import export_expenses
from utils.nlp import extract_entities_and_intent

async def handle_message(update, context):
    """Handle all text messages and route based on intent."""
    text = update.message.text.strip()
    
    # Skip if it’s a command (let CommandHandlers handle those)
    if text.startswith('/'):
        return
    
    # Unpack all 6 values returned by extract_entities_and_intent
    intent, amount, description, category, related_to, date = extract_entities_and_intent(text)
    
    if intent == "log":
        await log_expense(update, context)
    elif intent == "query":
        await query_expense(update, context)
    else:
        await update.message.reply_text(
            "I’m not sure what you mean. Try something like 'I spent $20 on a purse' or 'How much did I spend?'"
        )

def main() -> None:
    print("BOT_TOKEN:", "Set" if os.getenv("BOT_TOKEN") else "Not set")
    print("GOOGLE_APPLICATION_CREDENTIALS:", "Set" if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") else "Not set")

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set.")

    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("log", log_expense))
    application.add_handler(CommandHandler("query", query_expense))
    application.add_handler(CommandHandler("export", export_expenses))

    # Message handler for natural language input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()