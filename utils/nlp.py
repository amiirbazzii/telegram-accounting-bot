# utils/nlp.py
import spacy
from datetime import datetime, timedelta
import re
import logging
from typing import Union

# Helper function to parse relative weekdays
def parse_relative_weekday(text: str) -> Union[datetime, None]:
    today = datetime.now().date()
    text_lower = text.lower()
    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    match = re.search(r'(last|this|next)?\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', text_lower)
    if not match:
        return None

    modifier, weekday_str = match.groups()
    target_weekday = weekday_map.get(weekday_str)
    if target_weekday is None:
        return None

    current_weekday = today.weekday()
    
    if modifier == "last":
        days_ago = (current_weekday - target_weekday + 7) % 7
        if days_ago == 0: days_ago = 7 # Ensure it's actually *last* week
        target_date = today - timedelta(days=days_ago)
    elif modifier == "next":
        days_ahead = (target_weekday - current_weekday + 7) % 7
        if days_ahead == 0: days_ahead = 7 # Ensure it's actually *next* week
        target_date = today + timedelta(days=days_ahead)
    else: # Defaults to "this" or no modifier
        days_diff = target_weekday - current_weekday
        target_date = today + timedelta(days=days_diff)
        # If "this Friday" was mentioned on a Saturday, it means *next* Friday usually
        # However, for simplicity, we'll treat "this" as the current week or upcoming day.
        # More complex date interpretation can be added later.

    return datetime.combine(target_date, datetime.min.time())

nlp = spacy.load("en_core_web_sm")
logger = logging.getLogger(__name__)

CATEGORIES = {
    "food": {
        "keywords": ["food", "lunch", "dinner", "restaurant", "meal", "snack"],
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

    # Extract intent using keywords
    for intent_name, keywords in INTENT_KEYWORDS.items():
        if any(keyword in text.lower() for keyword in keywords):
            intent = intent_name
            break

    # Extract amount using regex
    amount_match = re.search(r'(\d+\.?\d*)\s*(?:\$|dollars|bucks)?', text)
    if amount_match:
        try:
            amount = float(amount_match.group(1))
        except ValueError:
            amount = None

    # Extract description and category using spacy tokens and keyword lists
    found_desc_cat = False
    for token in doc:
        token_text = token.text
        for main_cat, details in CATEGORIES.items():
            if token_text in details["keywords"]:
                description = token_text
                category = main_cat
                found_desc_cat = True; break
            for sub_cat, items in details["subcategories"].items():
                if token_text in items:
                    description = token_text
                    category = main_cat
                    found_desc_cat = True; break
        if found_desc_cat: break

    # Fallback logic for category based on terms in the text
    if not category:
        text_lower = text.lower()
        edible_terms = ["ate", "bought", "food", "edible"]
        gift_terms = ["for", "gift", "present"]
        
        is_edible = any(term in text_lower for term in edible_terms)
        if is_edible:
            food_items_flat = [item for sublist in CATEGORIES["food"]["subcategories"].values() for item in sublist]
            found_specific_food = False
            for token in doc:
                if token.text in food_items_flat:
                    description = token.text
                    category = "food"
                    found_specific_food = True
                    break
            if not found_specific_food:
                description = "food"
                category = "food"
        
        if not category and any(term in text_lower for term in gift_terms):
            for token in doc:
                if token.text in CATEGORIES["gift"]["keywords"]:
                    description = token.text
                    category = "gift"
                    break

    # Extract date using spacy entities with fallback for common date terms
    date_terms = []
    common_date_terms = ["today", "yesterday", "tomorrow", "last month"]  # Add more as needed
    logger.debug("Starting DATE entity extraction...")
    date_found = False
    parsed_date_obj = None # Store parsed date object

    # Attempt 1: Try parsing relative weekdays first
    parsed_date_obj = parse_relative_weekday(text)
    if parsed_date_obj:
        date_found = True
        logger.debug(f"Parsed relative weekday: {parsed_date_obj.strftime('%Y-%m-%d')}")

    # Attempt 2: If not found, try spaCy DATE entities
    if not date_found:
        for ent in doc.ents:
            logger.debug(f"Found entity: '{ent.text}', Label: {ent.label_}")
            if ent.label_ == "DATE":
                date_text = ent.text.lower()
                date_terms.extend(date_text.split())
                logger.debug(f"Added DATE terms from entity: {date_text.split()}, current date_terms: {date_terms}")
                
                # Handle specific DATE entities recognized by spaCy
                # Note: spaCy's date parsing is complex, this handles simple cases
                if "yesterday" in date_text:
                    parsed_date_obj = datetime.now() - timedelta(days=1)
                elif "last month" in date_text: # Approximate
                    parsed_date_obj = datetime.now() - timedelta(days=30)
                elif date_text in ["january", "february", "march", "april", "may", "june",
                                   "july", "august", "september", "october", "november", "december"]:
                    try:
                        current_year = datetime.now().year
                        parsed_date_obj = datetime.strptime(f"{current_year} {date_text}", "%Y %B")
                    except ValueError:
                        pass # Ignore if parsing fails
                # Add more specific spaCy DATE entity parsing here if needed
                
                if parsed_date_obj: 
                    date_found = True
                    logger.debug(f"Parsed date from spaCy DATE entity '{date_text}': {parsed_date_obj.strftime('%Y-%m-%d')}")
                    break # Stop after first successful DATE entity parse
    
    # Attempt 3: Fallback to common date terms if still not found
    if not date_found:
        text_lower = text.lower()
        for term in common_date_terms:
            if term in text_lower:
                date_terms.append(term)
                logger.debug(f"Added common date term: '{term}', current date_terms: {date_terms}")
                if term == "yesterday":
                    parsed_date_obj = datetime.now() - timedelta(days=1)
                elif term == "today":
                    parsed_date_obj = datetime.now()
                elif term == "tomorrow":
                    parsed_date_obj = datetime.now() + timedelta(days=1)
                elif term == "last month": # Approximate
                    parsed_date_obj = datetime.now() - timedelta(days=30)
                
                if parsed_date_obj:
                    date_found = True
                    logger.debug(f"Parsed date from common term '{term}': {parsed_date_obj.strftime('%Y-%m-%d')}")
                    break # Stop after first common term match

    logger.debug(f"Final date_terms list associated with found DATE entity/term: {date_terms}")
    
    # Format the final date string if a date was successfully parsed
    if parsed_date_obj:
        date = parsed_date_obj.strftime("%Y-%m-%d")
    else:
        date = datetime.now().strftime("%Y-%m-%d") # Default to today if nothing found
        logger.debug("No specific date found, defaulting to today.")

    # Extract "Related to" after amount
    if amount_match and description:
        post_amount_text = text[amount_match.end():].lower()
        post_amount_doc = nlp(post_amount_text)
        potential_related_to = None
        
        for i, token in enumerate(post_amount_doc):
            logger.debug(f"  RelatedToOuterLoop: Token='{token.text}'")
            if token.text == "for" and i + 1 < len(post_amount_doc):
                related_to_start_index = i + 1
                temp_parts = []
                logger.debug(f"    Found 'for', starting inner loop from index {related_to_start_index}")
                
                for t in post_amount_doc[related_to_start_index:]:
                    is_date_term = t.text in date_terms
                    is_prep_verb = t.pos_ in ["PREP", "VERB"] and t.text != "for"
                    logger.debug(f"      RelatedToInnerLoop: Token='{t.text}', POS='{t.pos_}', IsDateTerm={is_date_term}, IsPrepVerb={is_prep_verb}")
                    
                    if is_date_term or is_prep_verb:
                        logger.debug(f"        Breaking inner loop: Condition met (IsDateTerm={is_date_term}, IsPrepVerb={is_prep_verb})")
                        break
                    
                    temp_parts.append(t.text)
                    candidate_phrase = " ".join(temp_parts)
                    
                    if description in candidate_phrase:
                        logger.debug(f"        Skipping phrase: Description '{description}' found in candidate '{candidate_phrase}'")
                        temp_parts = []
                        break
                
                if temp_parts:
                    potential_related_to = " ".join(temp_parts).strip()
                    logger.debug(f"    Potential 'Related To' phrase found: '{potential_related_to}'")
        
        # Final validation
        if potential_related_to and description not in potential_related_to:
            related_to = potential_related_to
            logger.debug(f"  Final 'Related To' set to: '{related_to}'")
        elif potential_related_to:
            logger.debug(f"  Potential 'Related To' ('{potential_related_to}') discarded because it contains description ('{description}')")

    # Apply defaults if entities were not found
    if not description:
        description = "item"
    if not category:
        category = "misc"

    logger.debug(f"Final extracted entities: Intent={intent}, Amount={amount}, Desc={description}, Cat={category}, Rel={related_to}, Date={date}")
    return intent, amount, description, category, related_to, date

# Test block
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    test_inputs = [
        "Paid $10 for a banana yesterday",
        "I bought a purse for $20 for my wife today",
        "I spent $15 on a taxi for my friend",
        "I spent $5 on fruit",
    ]
    print("Running test cases with updated NLP logic...")
    for input_text in test_inputs:
        print(f"\n--- Processing Input: {input_text} ---")
        intent, amount, desc, cat, rel, date = extract_entities_and_intent(input_text)
        print(f"---> Result: Intent: {intent}, Amount: {amount}, Description: {desc}, Category: {cat}, Related to: {rel}, Date: {date}")



        