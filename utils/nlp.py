# utils/nlp.py
import spacy
from datetime import datetime, timedelta
import re

nlp = spacy.load("en_core_web_sm")

CATEGORIES = {
    "food": {
        "keywords": ["lunch", "dinner", "restaurant", "meal", "snack"],
        "subcategories": {
            "groceries": ["fruit", "apple", "banana", "orange", "vegetable", "potato", "bread", "milk", "egg", "meat", "chicken", "fish"],
            "dining": ["pizza", "burger", "sushi", "sandwich"]
        }
    },
    "travel": {
        "keywords": ["travel", "flight", "train", "bus", "taxi"],
        "subcategories": {}
    },
    "utilities": {
        "keywords": ["utilities", "electricity", "water", "internet"],
        "subcategories": {}
    },
    "gift": {
        "keywords": ["gift", "present", "purse", "jewelry", "toy"],
        "subcategories": {}
    },
    "misc": {
        "keywords": ["stuff", "things", "other"],
        "subcategories": {}
    }
}

INTENT_KEYWORDS = {
    "log": ["spent", "paid", "bought", "cost"],
    "query": ["how much", "what", "total", "spent on"]
}

def extract_entities_and_intent(text):
    """
    Extract intent, amount, description, category, related_to, and date from user input.
    Returns: (intent, amount, description, category, related_to, date)
    """
    doc = nlp(text.lower())
    
    intent = None
    amount = None
    description = None
    category = None
    related_to = None
    date = datetime.now().strftime("%Y-%m-%d")

    # Extract intent
    for intent_name, keywords in INTENT_KEYWORDS.items():
        if any(keyword in text.lower() for keyword in keywords):
            intent = intent_name
            break

    # Extract amount
    amount_match = re.search(r'(\d+\.?\d*)\s*(?:\$|dollars|bucks)?', text)
    if amount_match:
        amount = float(amount_match.group(1))
        amount_pos = amount_match.start()

    # Extract description and category
    for token in doc:
        for main_cat, details in CATEGORIES.items():
            if token.text in details["keywords"]:
                description = token.text
                category = main_cat
                break
            for sub_cat, items in details["subcategories"].items():
                if token.text in items:
                    description = token.text
                    category = main_cat
                    break
            if category:
                break
        if description and category:
            break

    # Fallback for category
    if not category:
        edible_terms = ["ate", "bought", "food", "edible"]
        gift_terms = ["for", "gift", "present"]
        if any(term in text.lower() for term in edible_terms):
            for token in doc:
                food_items = sum(CATEGORIES["food"]["subcategories"].values(), [])
                if token.text in food_items:
                    description = token.text
                    category = "food"
                    break
        elif any(term in text.lower() for term in gift_terms):
            for token in doc:
                if token.text in CATEGORIES["gift"]["keywords"]:
                    description = token.text
                    category = "gift"
                    break

    # Extract date first to exclude it from related_to
    date_terms = []
    for ent in doc.ents:
        if ent.label_ == "DATE":
            date_text = ent.text.lower()
            date_terms.extend(date_text.split())
            if "yesterday" in date_text:
                date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            elif "last month" in date_text:
                date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            elif date_text in ["january", "february", "march", "april", "may", "june",
                               "july", "august", "september", "october", "november", "december"]:
                date = datetime.strptime(f"2025 {date_text}", "%Y %B").strftime("%Y-%m-%d")
            break

    # Extract "Related to" after amount, checking all "for" instances
    if amount_match and description:
        post_amount_text = text[amount_match.end():].lower()
        post_amount_doc = nlp(post_amount_text)
        potential_related_to = None
        for i, token in enumerate(post_amount_doc):
            if token.text == "for" and i + 1 < len(post_amount_doc):
                related_to_start = i + 1
                related_to_parts = []
                skip = False
                for t in post_amount_doc[related_to_start:]:
                    candidate = " ".join(related_to_parts + [t.text])
                    # If description appears in the phrase, skip this "for" entirely
                    if description in candidate:
                        skip = True
                        break
                    if t.text in date_terms or (t.pos_ in ["PREP", "VERB"] and t.text != "for"):
                        break
                    related_to_parts.append(t.text)
                if not skip and related_to_parts:  # Only set if valid and no description overlap
                    potential_related_to = " ".join(related_to_parts)
        # Use the last valid "for" phrase that doesn’t overlap with description
        if potential_related_to and description not in potential_related_to:
            related_to = potential_related_to

    if not description:
        description = "item"
    if not category:
        category = "misc"

    return intent, amount, description, category, related_to, date

# Test
if __name__ == "__main__":
    test_inputs = [
        "Paid $10 for a banana yesterday",
        "I bought a purse for $20 for my wife today",
        "I spent $15 on a taxi for my friend",
        "I spent $5 on fruit",
    ]
    for input_text in test_inputs:
        intent, amount, desc, cat, rel, date = extract_entities_and_intent(input_text)
        print(f"Input: {input_text}")
        print(f"Intent: {intent}, Amount: {amount}, Description: {desc}, Category: {cat}, Related to: {rel}, Date: {date}\n")