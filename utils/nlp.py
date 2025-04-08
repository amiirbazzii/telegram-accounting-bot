# utils/nlp.py
import spacy
from datetime import datetime, timedelta
import re

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

# Define common categories and their keywords
CATEGORIES = {
    "food": ["lunch", "dinner", "restaurant", "groceries", "meal"],
    "travel": ["travel", "flight", "train", "bus", "taxi"],
    "utilities": ["utilities", "electricity", "water", "internet"],
    "misc": ["stuff", "things", "other"]
}

# Define intent keywords
INTENT_KEYWORDS = {
    "log": ["spent", "paid", "bought", "cost"],
    "query": ["how much", "what", "total", "spent on"]
}

def extract_entities_and_intent(text):
    """
    Extract amount, category, date, and intent from user input.
    Returns: (intent, amount, category, date)
    """
    doc = nlp(text.lower())
    
    # Initialize variables
    intent = None
    amount = None
    category = None
    date = datetime.now().strftime("%Y-%m-%d")  # Default to today

    # Extract intent
    for intent_name, keywords in INTENT_KEYWORDS.items():
        if any(keyword in text.lower() for keyword in keywords):
            intent = intent_name
            break

    # Extract amount using regex (e.g., "$50", "50 dollars", "50 bucks")
    amount_match = re.search(r'(\d+\.?\d*)\s*(?:\$|dollars|bucks)?', text)
    if amount_match:
        amount = float(amount_match.group(1))

    # Extract category
    for token in doc:
        for cat, keywords in CATEGORIES.items():
            if token.text in keywords or token.text == cat:
                category = cat
                break
        if category:
            break

    # Extract date (relative or explicit)
    for ent in doc.ents:
        if ent.label_ == "DATE":
            date_text = ent.text.lower()
            if "yesterday" in date_text:
                date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            elif "last month" in date_text:
                date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            elif date_text in ["january", "february", "march", "april", "may", "june",
                               "july", "august", "september", "october", "november", "december"]:
                date = datetime.strptime(f"2025 {date_text}", "%Y %B").strftime("%Y-%m-%d")
            break

    return intent, amount, category, date

# Example usage (for testing):
if __name__ == "__main__":
    test_inputs = [
        "I spent $30 on lunch yesterday",
        "How much did I spend on travel last month?",
        "Paid 50 bucks for groceries",
    ]
    for input_text in test_inputs:
        intent, amount, category, date = extract_entities_and_intent(input_text)
        print(f"Input: {input_text}")
        print(f"Intent: {intent}, Amount: {amount}, Category: {category}, Date: {date}\n")