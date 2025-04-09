import logging
import asyncio
import gspread # Import gspread to catch its specific exceptions
from telegram.ext import ContextTypes
from .google_sheet import get_google_sheet # Assuming relative import works

# Define the key used in bot_data
PENDING_EXPENSES_KEY = 'pending_expenses'
# Define how often to flush (in seconds)
FLUSH_INTERVAL_SECONDS = 30
# Define max batch size to avoid overly large requests or hitting API limits
MAX_BATCH_SIZE = 100
# Define the cache key used by the query command
QUERY_CACHE_KEY = 'query_cache' # Needs to match the key in commands/query.py

async def flush_expenses_to_sheet(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job callback function to write pending expenses from bot_data to Google Sheets.
    Handles batching, error logging, and cache invalidation.
    """
    if PENDING_EXPENSES_KEY not in context.bot_data:
        # This case might happen if the bot restarts and the job runs before initialization
        # or if bot_data persistence isn't used. Initialize defensively.
        logging.warning(f"'{PENDING_EXPENSES_KEY}' not found in bot_data during flush. Initializing.")
        context.bot_data[PENDING_EXPENSES_KEY] = []
        return # Nothing to flush

    pending_expenses = context.bot_data.get(PENDING_EXPENSES_KEY, [])

    if not pending_expenses:
        # No expenses waiting to be written.
        return

    # Take up to MAX_BATCH_SIZE expenses to write in this batch
    expenses_to_write = pending_expenses[:MAX_BATCH_SIZE]
    remaining_expenses = pending_expenses[MAX_BATCH_SIZE:]

    logging.info(f"Attempting to flush {len(expenses_to_write)} expenses to Google Sheet.")

    try:
        # Crucial: Update bot_data *before* the I/O operation.
        # This minimizes the chance of writing duplicate data if the flush fails partway
        # but means data might be lost if the flush fails permanently.
        # More robust error handling (e.g., retry queues, dead-letter queues) could be added.
        context.bot_data[PENDING_EXPENSES_KEY] = remaining_expenses

        sheet = await asyncio.to_thread(get_google_sheet)
        # Use append_rows for batch writing. value_input_option='USER_ENTERED' mimics typing.
        await asyncio.to_thread(sheet.append_rows, values=expenses_to_write, value_input_option='USER_ENTERED')
        logging.info(f"Successfully flushed {len(expenses_to_write)} expenses.")

        # --- Cache Invalidation ---
        # Clear the query cache since data has changed
        if QUERY_CACHE_KEY in context.bot_data:
            context.bot_data[QUERY_CACHE_KEY] = {}
            logging.info(f"Cleared query cache ('{QUERY_CACHE_KEY}') due to successful expense flush.")
        # ------------------------

        # If there were more expenses than the batch size allowed,
        # schedule an immediate run to process the next chunk.
        if remaining_expenses:
             logging.info(f"{len(remaining_expenses)} expenses remaining. Scheduling immediate flush.")
             # Use a unique name to avoid conflicts if the periodic job also runs.
             context.job_queue.run_once(flush_expenses_to_sheet, when=0, name=f"immediate_flush_{hash(tuple(map(tuple, remaining_expenses)))}")

    except gspread.exceptions.APIError as api_err:
         logging.error(f"Google Sheets API Error during flush: {api_err}")
         # Consider putting expenses back if it's a rate limit error, otherwise log and discard.
         # For simplicity now, we log the error and they remain removed from bot_data.
         logging.error(f"Discarding {len(expenses_to_write)} expenses due to API error.")
    except Exception as e:
        logging.error(f"Unexpected error during expense flush: {e}", exc_info=True)
        # Discarding to prevent potential infinite loops on faulty data or persistent errors.
        logging.error(f"Discarding {len(expenses_to_write)} expenses due to unexpected error.")


def add_expense_to_batch(context: ContextTypes.DEFAULT_TYPE, expense_row: list):
    """Safely adds a single expense row to the pending batch list in bot_data."""
    if PENDING_EXPENSES_KEY not in context.bot_data:
        # Initialize if this is the first expense added since bot start/restart
        context.bot_data[PENDING_EXPENSES_KEY] = []
    context.bot_data[PENDING_EXPENSES_KEY].append(expense_row)
    logging.debug(f"Added expense to batch. Current batch size: {len(context.bot_data[PENDING_EXPENSES_KEY])}") 