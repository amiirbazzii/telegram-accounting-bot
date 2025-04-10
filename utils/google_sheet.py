# utils/google_sheet.py
import os
import gspread
import logging
import json # Import json module

logger = logging.getLogger(__name__)

SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Expenses") # Use env var or default
WORKSHEET_INDEX = 0

# Get the service account credentials (could be path or JSON string)
GOOGLE_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

def get_google_sheet():
    if not GOOGLE_CREDS:
        logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
        
    try:
        client = None
        # Check if GOOGLE_CREDS looks like a file path or JSON content
        if '{' in GOOGLE_CREDS and '}' in GOOGLE_CREDS and '"private_key"' in GOOGLE_CREDS:
            # Assume it's JSON content
            try:
                logger.debug("Attempting to authorize gspread using JSON credentials from env var...")
                creds_dict = json.loads(GOOGLE_CREDS)
                client = gspread.service_account_from_dict(creds_dict)
                logger.info("gspread client authorized successfully using JSON credentials.")
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse JSON from GOOGLE_APPLICATION_CREDENTIALS: {json_err}")
                raise ValueError(f"Invalid JSON content in GOOGLE_APPLICATION_CREDENTIALS: {json_err}")
            except Exception as auth_err:
                logger.error(f"Error authorizing with JSON credentials: {auth_err}", exc_info=True)
                raise ConnectionError(f"Failed to authorize with JSON credentials: {auth_err}")
        else:
            # Assume it's a file path
            logger.debug(f"Attempting to authorize gspread using service account file: {GOOGLE_CREDS}")
            if not os.path.exists(GOOGLE_CREDS):
                 logger.error(f"Service account file not found at path: {GOOGLE_CREDS}")
                 raise FileNotFoundError(f"Service account file not found: {GOOGLE_CREDS}")
            try:
                client = gspread.service_account(filename=GOOGLE_CREDS)
                logger.info("gspread client authorized successfully using service account file.")
            except Exception as auth_err:
                 logger.error(f"Error authorizing with service account file {GOOGLE_CREDS}: {auth_err}", exc_info=True)
                 raise ConnectionError(f"Failed to authorize with service account file: {auth_err}")

        # If client is still None after checks, something went wrong
        if client is None:
             logger.critical("Could not initialize gspread client. Check credentials configuration.")
             raise ConnectionError("Failed to initialize gspread client.")
             
        # Open the sheet and select the worksheet
        spreadsheet = client.open(SHEET_NAME)
        logger.info(f"Successfully opened spreadsheet: '{SHEET_NAME}'")
        sheet = spreadsheet.get_worksheet(WORKSHEET_INDEX)
        logger.info(f"Successfully accessed worksheet index {WORKSHEET_INDEX} (Name: {sheet.title})")
        return sheet

    except Exception as e:
        # Log the specific error during authorization or sheet access
        logger.error(f"Error accessing Google Sheet '{SHEET_NAME}': {e}", exc_info=True)
        # Check if the original env var was set (useful for context)
        if not GOOGLE_CREDS:
            logger.error("Hint: Ensure the GOOGLE_APPLICATION_CREDENTIALS environment variable is set to the path of your service account key file OR the JSON content itself.")
        # Check if the sheet name is set
        if not SHEET_NAME:
            logger.error("Hint: Ensure the GOOGLE_SHEET_NAME environment variable is set.")
            
        raise ConnectionError(f"Failed to get Google Sheet '{SHEET_NAME}'. Check logs for details.")