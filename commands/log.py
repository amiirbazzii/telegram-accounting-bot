# commands/log.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.batch_writer import add_expense_to_batch
from utils.nlp import extract_entities_and_intent
from datetime import datetime

logger = logging.getLogger(__name__)

async def log_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    intent = None
    amount = None
    description = None
    category = None
    related_to = None
    date = None

    # Check if NLP results were passed from handle_message
    if 'nlp_result' in context.chat_data:
        logger.debug("Using NLP results found in chat_data")
        nlp_data = context.chat_data.pop('nlp_result') # Get and remove data
        # Basic check to ensure it looks like our data structure
        if nlp_data.get('intent') == 'log':
            amount = nlp_data.get('amount')
            description = nlp_data.get('description', 'item') # Use defaults if missing
            category = nlp_data.get('category', 'misc')
            related_to = nlp_data.get('related_to')
            date = nlp_data.get('date')
            intent = 'log' # We know intent is log here
        else:
            logger.warning("nlp_result found in chat_data, but intent was not 'log'. Discarding.")
            # Fall through to re-process text if structure was unexpected
    
    # If entities were not found in context, process text (handles direct /log command)
    if intent is None: # Check if we successfully got data from context
        try:
            text = update.message.text.strip()
            # Handle direct command invocation
            if text.startswith("/log"):
                command_parts = text.split(maxsplit=1)
                if len(command_parts) > 1:
                    text = command_parts[1].strip()
                else:
                    await update.message.reply_text("Please provide expense details after /log (e.g., '/log $10 for coffee').")
                    return
            
            if not text:
                # This case handles empty messages or if context data was invalid
                await update.message.reply_text("Please tell me what you spent (e.g., 'I spent $20 on a purse').")
                return

            # Use NLP to extract details - ONLY if not passed via context
            logger.debug(f"Processing log request via NLP for text: '{text}'")
            intent, amount, description, category, related_to, date = extract_entities_and_intent(text)
            
            # If NLP still didn't yield 'log' intent (e.g., user typed /log gibberish)
            if intent != 'log':
                 logger.warning(f"NLP did not detect log intent for text: '{text}'")
                 await update.message.reply_text("Sorry, I couldn't understand that as an expense to log.")
                 return

        except Exception as e:
            logger.error(f"Error during text processing in log_expense: {e}", exc_info=True)
            await update.message.reply_text(f"Oops, something went wrong processing your message: {str(e)}")
            return

    # --- Processing Logic (using extracted amount, description, etc.) ---
    try:
        # Ensure an amount was found (critical for logging)
        if amount is None:
            logger.warning("Log intent confirmed, but no amount found.")
            await update.message.reply_text("Sorry, I need an amount to log the expense (e.g., '$20').")
            return
            
        # Prepare the row data for the sheet
        # Ensure defaults if NLP somehow returned None (shouldn't happen with current NLP code)
        description = description or "item"
        category = category or "misc"
        date = date or datetime.now().strftime("%Y-%m-%d") # Fallback date
        expense_row = [description, date, str(amount), category, related_to or ""]
        
        # Add the expense to the batch queue
        add_expense_to_batch(context, expense_row)
        logger.info(f"Added expense to batch: {expense_row}")

        # Send confirmation to the user
        response = f"Got it! Queued expense: {description} for ${amount} ({category})"
        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error during batch adding/reply in log_expense: {e}", exc_info=True)
        # Don't send another message if the error happened during reply
        if not context.error:
             await update.message.reply_text(f"Oops, something went wrong saving your expense: {str(e)}")