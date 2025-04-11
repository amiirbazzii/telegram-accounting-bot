# main.py
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize Telegram application
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable is not set.")
    raise ValueError("BOT_TOKEN environment variable is not set.")

telegram_app = Application.builder().token(BOT_TOKEN).build()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages and route based on intent."""
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    logger.debug(f"Handling message: '{text}'")
    intent, amount, description, category, related_to, date = extract_entities_and_intent(text)
    logger.debug(f"Extracted: Intent={intent}, Amount={amount}, Desc={description}, Cat={category}, Rel={related_to}, Date={date}")
    
    if intent == "log":
        context.chat_data['nlp_result'] = {
            'intent': intent,
            'amount': amount,
            'description': description,
            'category': category,
            'related_to': related_to,
            'date': date
        }
        logger.debug(f"Stored NLP result in chat_data for chat ID {update.effective_chat.id}")
        await log_expense(update, context)
    elif intent == "query":
        await query_expense(update, context)
    else:
        logger.info(f"Could not determine intent for message: '{text}'")
        await update.message.reply_text(
            "I'm not sure what you mean. Try something like 'I spent $20 on a purse' or 'How much did I spend?'"
        )

async def setup_handlers():
    """Register command and message handlers."""
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("log", log_expense))
    telegram_app.add_handler(CommandHandler("query", query_expense))
    telegram_app.add_handler(CommandHandler("export", export_expenses))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Initialize bot_data for pending expenses
    telegram_app.bot_data[PENDING_EXPENSES_KEY] = []
    logger.info(f"Initialized '{PENDING_EXPENSES_KEY}' in bot_data.")
    
    # Schedule batch flush job
    telegram_app.job_queue.run_repeating(
        flush_expenses_to_sheet,
        interval=FLUSH_INTERVAL_SECONDS,
        first=FLUSH_INTERVAL_SECONDS,
        name="periodic_flush_job"
    )
    logger.info(f"Scheduled periodic expense flush every {FLUSH_INTERVAL_SECONDS} seconds.")

@app.on_event("startup")
async def on_startup():
    """Initialize bot and set webhook on startup."""
    await setup_handlers()
    await telegram_app.initialize()
    await telegram_app.start()
    
    # Get the deployed URL
    # For Vercel, first try VERCEL_URL, then fallback to custom URL if provided
    base_url = os.getenv("VERCEL_URL")
    if base_url:
        # Vercel provides VERCEL_URL without protocol, so add https://
        webhook_url = f"https://{base_url}/webhook"
    else:
        # Fallback to custom domain if provided
        custom_domain = os.getenv("CUSTOM_DOMAIN")
        if custom_domain:
            webhook_url = f"https://{custom_domain}/webhook"
        else:
            # Fallback to a default URL (this should be overridden in production)
            webhook_url = "https://your-bot.vercel.app/webhook"
            logger.warning(f"Using default webhook URL: {webhook_url}. Set VERCEL_URL or CUSTOM_DOMAIN environment variables.")
    
    logger.info(f"Setting webhook to: {webhook_url}")
    await telegram_app.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to {webhook_url}")

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming Telegram updates via webhook."""
    try:
        update = await request.json()
        await telegram_app.update_queue.put(Update.de_json(update, telegram_app.bot))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Bot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))