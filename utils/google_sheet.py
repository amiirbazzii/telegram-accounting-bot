import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_google_sheet():
    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_json:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")

    try:
        creds_dict = json.loads(creds_json)
        print("Parsed Credentials:", creds_dict)  # Debugging
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        print("Scopes:", scopes)  # Debugging
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Expenses").sheet1
        return sheet
    except Exception as e:
        print(f"An error occurred while loading Google Sheets credentials: {str(e)}")
        raise ValueError(f"Failed to load Google Sheets credentials: {str(e)}")