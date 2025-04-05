import os
import json
from google.oauth2.service_account import Credentials
import gspread

# Load credentials
creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not creds_json:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")

try:
    creds_dict = json.loads(creds_json)
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open("Expenses").sheet1
    print("Authentication successful!")
except Exception as e:
    print("Authentication failed:", str(e))