#!/usr/bin/env python3
# test_bot.py - Test file for NLP and command functionality

import os
import logging
from dotenv import load_dotenv
from utils.nlp import extract_entities_and_intent
from utils.google_sheet import get_google_sheet

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_nlp():
    """Test NLP entity extraction functionality."""
    test_phrases = [
        "I spent $20 on coffee yesterday",
        "Paid 50 dollars for dinner with John",
        "How much did I spend on groceries?",
        "Show me expenses from last week",
        "$120.50 for new shoes today",
        "Show total expenses in March",
        "Spent 15€ on bus tickets",
        "200 for rent"
    ]
    
    print("\n=== Testing NLP Entity Extraction ===")
    for phrase in test_phrases:
        intent, amount, description, category, related_to, date = extract_entities_and_intent(phrase)
        print(f"\nInput: '{phrase}'")
        print(f"  Intent: {intent}")
        print(f"  Amount: {amount}")
        print(f"  Description: {description}")
        print(f"  Category: {category}")
        print(f"  Related to: {related_to}")
        print(f"  Date: {date}")

def test_google_sheet_connection():
    """Test connection to Google Sheets."""
    print("\n=== Testing Google Sheets Connection ===")
    try:
        sheet = get_google_sheet()
        print(f"Successfully connected to Google Sheet: {sheet.title}")
        # Optional: Display first few rows
        rows = sheet.get_all_values()
        if rows:
            print(f"First row (headers): {rows[0]}")
            if len(rows) > 1:
                print(f"Second row (data): {rows[1]}")
        else:
            print("Sheet is empty")
        return True
    except Exception as e:
        print(f"Failed to connect to Google Sheet: {e}")
        return False

def manual_test_menu():
    """Provide a menu for manual testing."""
    while True:
        print("\n=== Manual Testing Options ===")
        print("1. Test NLP functionality")
        print("2. Test Google Sheet connection")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            test_phrase = input("Enter a test phrase (e.g., 'I spent $20 on coffee'): ")
            intent, amount, description, category, related_to, date = extract_entities_and_intent(test_phrase)
            print(f"\nInput: '{test_phrase}'")
            print(f"  Intent: {intent}")
            print(f"  Amount: {amount}")
            print(f"  Description: {description}")
            print(f"  Category: {category}")
            print(f"  Related to: {related_to}")
            print(f"  Date: {date}")
        
        elif choice == "2":
            test_google_sheet_connection()
        
        elif choice == "3":
            print("Exiting test menu.")
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def main():
    """Run all tests."""
    print("=== Telegram Bot Test Suite ===")
    
    # Check environment variables
    required_vars = ["BOT_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS", "SPREADSHEET_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Some tests may fail. Make sure you have a .env file with these variables.")
    
    choice = input("\nRun all tests automatically? (y/n): ")
    
    if choice.lower() == 'y':
        # Run automated tests
        test_nlp()
        test_google_sheet_connection()
    else:
        # Run interactive menu
        manual_test_menu()

if __name__ == "__main__":
    main() 