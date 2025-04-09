# commands/query.py
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet
from utils.nlp import extract_entities_and_intent

logger = logging.getLogger(__name__)

# Cache configuration
QUERY_CACHE_KEY = 'query_cache'
CACHE_TTL_MINUTES = 10 # How long to keep cache results valid

async def query_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    # Initialize cache in bot_data if it doesn't exist
    if QUERY_CACHE_KEY not in context.bot_data:
        context.bot_data[QUERY_CACHE_KEY] = {}
        
    cache = context.bot_data[QUERY_CACHE_KEY]
    
    try:
        text = update.message.text.strip()
        # Handle direct command usage
        if text.startswith("/query"):
            command_parts = text.split(maxsplit=1)
            if len(command_parts) > 1:
                text = command_parts[1].strip()
            else:
                 await update.message.reply_text("Please ask something after /query (e.g., '/query total spent last month').")
                 return
        
        if not text:
            await update.message.reply_text("Please ask something (e.g., 'How much did I spend on food?')")
            return

        logger.debug(f"Processing query request for text: '{text}'")
        # Extract entities needed for the query
        # Note: If handle_message passed entities, we could potentially reuse them here too.
        intent, amount, description, category, related_to, date = extract_entities_and_intent(text)
        
        # Basic validation: We expect a query intent from NLP for this handler
        # Allow fallback to query if NLP wasn't sure but user used /query command?
        # For now, strict check: intent must be query or resolved to query.
        if intent != "query" and not text.startswith("/query"): # Allow if explicitly invoked
            logger.warning(f"Intent was not 'query' for text: '{text}'")
            # Send a helpful message instead of generic error
            await update.message.reply_text("I can only answer questions about expenses (e.g., 'how much spent on food?'). To log, try 'spent $10 on lunch'.")
            return

        # Determine the month and year from the extracted date for filtering and caching
        try:
            query_date_obj = datetime.strptime(date, "%Y-%m-%d")
            month_year = query_date_obj.strftime("%Y-%B") # Use YYYY-Month for cache key stability
            month_display = query_date_obj.strftime("%B %Y") # For user display
        except ValueError:
             logger.error(f"Could not parse date '{date}' from NLP. Using current month.")
             now = datetime.now()
             month_year = now.strftime("%Y-%B")
             month_display = now.strftime("%B %Y")

        # Normalize category for cache key (lowercase or None)
        cache_category = category.lower() if category else "overall"
        
        # --- Cache Check ---
        cache_entry_key = f"{month_year}_{cache_category}"
        now = datetime.now()
        
        if cache_entry_key in cache:
            cached_data = cache[cache_entry_key]
            if now < cached_data['expiry']:
                logger.info(f"Cache hit for query key: {cache_entry_key}")
                cached_total = cached_data['result']
                # Recreate response from cached data
                response = f"Total expenses in {month_display}: ${cached_total:.2f}" 
                if category:
                    response = f"You spent ${cached_total:.2f} on {cache_category} in {month_display}."
                await update.message.reply_text(response)
                return # End early due to cache hit
            else:
                 logger.info(f"Cache expired for query key: {cache_entry_key}")
                 del cache[cache_entry_key] # Remove expired entry

        logger.info(f"Cache miss for query key: {cache_entry_key}. Fetching from Google Sheet.")
        # --- Fetch and Filter (Cache Miss Path) ---
        sheet = await asyncio.to_thread(get_google_sheet)
        # This is still the bottleneck - reads all data!
        rows = await asyncio.to_thread(sheet.get_all_records)
        logger.debug(f"Fetched {len(rows)} rows from the sheet.")
        
        total = 0.0
        for row in rows:
            try:
                # Check if row date matches the target month and year
                row_date_obj = datetime.strptime(row["Date"], "%Y-%m-%d")
                if row_date_obj.strftime("%Y-%B") == month_year:
                    # Check category match (case-insensitive) if a category was specified
                    row_category = str(row.get("Category", "")).lower()
                    if category is None or row_category == cache_category:
                        total += float(row["Amount"])
            except (ValueError, KeyError, TypeError) as parse_error:
                logger.warning(f"Skipping row due to parsing error: {parse_error} - Row: {row}")
                continue # Skip malformed rows

        # --- Store result in cache ---
        expiry_time = now + timedelta(minutes=CACHE_TTL_MINUTES)
        cache[cache_entry_key] = {'result': total, 'expiry': expiry_time}
        logger.info(f"Stored result in cache for key: {cache_entry_key}, expires: {expiry_time}")

        # --- Send Response ---
        response = f"Total expenses in {month_display}: ${total:.2f}"
        if category:
            response = f"You spent ${total:.2f} on {cache_category} in {month_display}."
        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error processing query_expense: {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, I encountered an error trying to answer your query: {str(e)}")