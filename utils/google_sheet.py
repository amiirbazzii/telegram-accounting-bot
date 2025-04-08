import os
import json
import gspread
from google.oauth2.service_account import Credentials

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