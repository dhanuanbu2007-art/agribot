"""
Query resolver for AgriGuide.

Converts follow-up questions into standalone search queries
suitable for Gemini Embedding 2 / Qdrant retrieval.

Supports:
- Tamil follow-up questions
- English follow-up questions
- Tamil-English mixed questions
- Context-aware query expansion
"""


import re


# -------------------------------------------------------------------
# Tamil follow-up word/phrase patterns
# These are phrases that indicate the question is a follow-up
# and needs context enrichment.
# -------------------------------------------------------------------
TAMIL_FOLLOWUP_PATTERNS = [
    # "அதுக்கப்புறம்" = "after that"
    "அதுக்கப்புறம்",
    "அதற்குப்பிறகு",
    "அதுக்கப்புறம் என்ன",
    "அப்புறம் என்ன",
    "பிறகு என்ன",
    # "இதுக்கு" = "for this"
    "இதுக்கு",
    "இதற்கு",
    # "அதை" = "that"
    "அதை எப்படி",
    "அதை",
    # "முதல்ல" = "first"
    "முதல்ல என்ன",
    "முதலில் என்ன",
    # Follow-up question starters without agriculture words
    "எப்போ போட",
    "எப்போ விதை",
    "எவ்வளவு போட",
    "எந்த உரம்",
    "எந்த பூச்சி",
    "எந்த மருந்து",
    "எப்படி தயார்",
    "எப்படி கட்டுப்படுத்த",
    "எப்படி தடுக்க",
    "ஏதாவது திட்டம்",
    "ஏதாவது scheme",
    "apply பண்ண",
    "apply பண்ணணும்",
]

# English follow-up starters that need context enrichment
ENGLISH_FOLLOWUP_STARTS = [
    "what about",
    "how about",
    "what next",
    "then what",
    "after that",
    "what should i do next",
    "what should i do after",
    "and then",
    "how much",
    "how many",
    "how often",
    "when should i",
    "when do i",
    "is there any scheme",
    "are there any scheme",
    "any scheme",
    "any government",
    "how to apply",
    "how can i apply",
    "what are the benefits",
    "what is the dose",
    "how to control",
    "how to prevent",
    "how to manage",
]


def _contains_tamil(text):
    """Return True if text has Tamil Unicode characters."""
    return bool(re.search(r'[\u0B80-\u0BFF]', text))


def _is_tamil_followup(question):
    """Check if a Tamil question is a follow-up pattern."""
    for pattern in TAMIL_FOLLOWUP_PATTERNS:
        if pattern in question:
            return True
    return False


def _is_english_followup(question_lower):
    """Check if an English question is a follow-up pattern."""
    for phrase in ENGLISH_FOLLOWUP_STARTS:
        if question_lower.startswith(phrase):
            return True
    return False


def _is_short_question(question, max_words=7):
    """Short questions without specific topic are usually follow-ups."""
    return len(question.split()) <= max_words


def _build_english_search_query(question, crop, subtopic):
    """
    Build an English search query from the question + context.

    The query is used for vector search. English works well
    because the documents are in English.
    """
    parts = []

    if crop:
        parts.append(crop)

    if subtopic:
        # Map subtopic tag to readable English search phrase
        subtopic_phrases = {
            "cultivation":      "cultivation practices",
            "land_preparation": "land preparation",
            "fertilizer":       "fertilizer nutrient management",
            "irrigation":       "irrigation water management",
            "pest_management":  "pest management control",
            "disease_management": "disease management treatment",
            "weed_management":  "weed management",
            "harvest":          "harvest yield",
            "government_scheme": "government scheme subsidy",
            "general_info":     "general information",
        }
        phrase = subtopic_phrases.get(subtopic, subtopic.replace("_", " "))
        parts.append(phrase)

    # Always include the original question for semantic richness
    parts.append(question)

    return " ".join(parts)


def resolve_search_query(question, conversation_topic=None, conversation_state=None):
    """
    Convert the user's question (possibly Tamil, follow-up, or short)
    into an enriched standalone search query for vector retrieval.


    Parameters
    ----------
    question           : str  – raw user question
    conversation_topic : str  – legacy: crop name (kept for compat.)
    conversation_state : ConversationState | None – richer state object
    """
    q_stripped = question.strip()
    q_lower = q_stripped.lower()
    is_tamil = _contains_tamil(q_stripped)

    # Resolve crop and subtopic from the richer state object if available
    crop = None
    subtopic = None

    if conversation_state is not None:
        crop = conversation_state.crop
        subtopic = conversation_state.subtopic
    elif conversation_topic:
        crop = conversation_topic

    # No context at all → send the question as-is
    if not crop and not subtopic:
        return q_stripped

    # -----------------------------------------------------------------
    # Determine if this is a follow-up that needs context enrichment
    # -----------------------------------------------------------------
    is_followup = False

    if is_tamil:
        if _is_tamil_followup(q_stripped):
            is_followup = True
        elif _is_short_question(q_stripped, max_words=8) and crop:
            is_followup = True
    else:
        if _is_english_followup(q_lower):
            is_followup = True
        elif _is_short_question(q_stripped, max_words=6) and crop:
            is_followup = True

    # -----------------------------------------------------------------
    # Build the search query
    # -----------------------------------------------------------------
    if is_followup:
        return _build_english_search_query(q_stripped, crop, subtopic)

    # Not a follow-up — but still include crop context if question
    # doesn't already mention a crop (avoids duplicate "paddy paddy ...")
    if crop and crop not in q_lower:
        return f"{crop} {q_stripped}"

    return q_stripped