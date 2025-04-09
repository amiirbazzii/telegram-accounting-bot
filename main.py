# main.py
import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Import command handlers
from commands.start import start
from commands.help import help_command
from commands.log import log_expense
from commands.query import query_expense
from commands.export import export_expenses
from utils.nlp import extract_entities_and_intent
from utils.batch_writer import (
    flush_expenses_to_sheet, 
    PENDING_EXPENSES_KEY, 
    FLUSH_INTERVAL_SECONDS
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Set higher logging level for httpx to avoid GET /updates spam
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def handle_message(update, context):
    """Handle all text messages and route based on intent."""
    text = update.message.text.strip()
    
    # Skip if it's a command (let CommandHandlers handle those)
    if text.startswith('/'):
        return
    
    logger.debug(f"Handling message: '{text}'")
    # Unpack all 6 values returned by extract_entities_and_intent
    intent, amount, description, category, related_to, date = extract_entities_and_intent(text)
    logger.debug(f"Extracted: Intent={intent}, Amount={amount}, Desc={description}, Cat={category}, Rel={related_to}, Date={date}")
    
    if intent == "log":
        # Store extracted entities in context to avoid re-processing in log_expense
        context.chat_data['nlp_result'] = {
            'intent': intent, # Store intent too for verification
            'amount': amount,
            'description': description,
            'category': category,
            'related_to': related_to,
            'date': date
        }
        logger.debug(f"Stored NLP result in chat_data for chat ID {update.effective_chat.id}")
        # Pass context to log_expense so it can add to the batch and use stored entities
        await log_expense(update, context)
    elif intent == "query":
        # If query needs NLP results, we could store them too
        # context.chat_data['nlp_result'] = { ... }
        await query_expense(update, context)
    else:
        logger.info(f"Could not determine intent for message: '{text}'")
        await update.message.reply_text(
            "I'm not sure what you mean. Try something like 'I spent $20 on a purse' or 'How much did I spend?'"
        )

def main() -> None:
    logger.info("Starting bot...")
    print("BOT_TOKEN:", "Set" if os.getenv("BOT_TOKEN") else "Not set")
    print("GOOGLE_APPLICATION_CREDENTIALS:", "Set" if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") else "Not set")

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set.")
        raise ValueError("BOT_TOKEN environment variable is not set.")

    application = Application.builder().token(BOT_TOKEN).build()

    # Initialize bot_data for pending expenses
    application.bot_data[PENDING_EXPENSES_KEY] = []
    logger.info(f"Initialized '{PENDING_EXPENSES_KEY}' in bot_data.")

    # Schedule the periodic flush job
    job_queue = application.job_queue
    job_queue.run_repeating(
        flush_expenses_to_sheet, 
        interval=FLUSH_INTERVAL_SECONDS, 
        first=FLUSH_INTERVAL_SECONDS, # Start after the first interval
        name="periodic_flush_job"
    )
    logger.info(f"Scheduled periodic expense flush every {FLUSH_INTERVAL_SECONDS} seconds.")

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("log", log_expense))
    application.add_handler(CommandHandler("query", query_expense))
    application.add_handler(CommandHandler("export", export_expenses))

    # Message handler for natural language input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running and polling for updates...")
    application.run_polling()

if __name__ == "__main__":
    main()