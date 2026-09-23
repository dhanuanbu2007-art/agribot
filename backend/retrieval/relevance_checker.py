"""
Relevance checker for AgriGuide.

Supports:
- English agriculture keywords
- Tamil agriculture keywords and phrases
- Tamil-English mixed questions
- Contextual follow-up questions (when conversation is already agricultural)
"""

import re

# -------------------------------------------------------------------
# English agriculture keywords
# -------------------------------------------------------------------
ENGLISH_AGRICULTURE_KEYWORDS = [
    "agriculture", "agricultural", "agri",
    "crop", "crops", "cultivate", "cultivation", "cultivating",
    "farming", "farmer", "farm", "farmland",
    "sowing", "sow", "seed", "seeds", "seedling", "nursery",
    "fertilizer", "fertiliser", "manure", "compost", "nutrient",
    "irrigation", "water", "watering",
    "soil", "land", "field", "plot",
    "pest", "pests", "pesticide", "insecticide", "herbicide", "fungicide",
    "disease", "diseases", "infection", "pathogen",
    "weed", "weeds",
    "harvest", "harvesting", "yield", "produce",
    "rice", "paddy", "wheat", "maize", "corn",
    "black gram", "green gram", "groundnut",
    "cotton", "sesame", "tomato", "brinjal", "chilli", "okra",
    "sorghum", "millet", "soybean", "sugarcane",
    "pulse", "pulses", "legume",
    "government scheme", "agricultural scheme", "subsidy", "loan",
    "crop variety", "variety", "hybrid",
    "plant", "plants", "planting", "transplant",
    "organic", "organic farming",
    "spray", "spraying", "apply", "application",
    "nitrogen", "phosphorus", "potassium", "urea", "dap",
    "root", "leaf", "leaves", "stem", "flower", "fruit",
    "yellowing", "wilting", "blight", "rot", "rust", "spot",
    "insect", "bug", "larvae", "larva",
    "drip", "sprinkler", "canal",
    "spacing", "depth", "germination",
    "basal", "top dressing", "foliar",
    "season", "kharif", "rabi", "zaid",
]

# -------------------------------------------------------------------
# Tamil agriculture keywords (Unicode Tamil script)
# -------------------------------------------------------------------
TAMIL_AGRICULTURE_KEYWORDS = [
    # Crops
    "நெல்", "நெல்லு", "நெல்லை", "நெல்லுக்கு",
    "கோதுமை", "மக்காச்சோளம்", "சோளம்",
    "கடலை", "நிலக்கடலை", "உளுந்து", "பாசிப்பயிறு",
    "பருத்தி", "எள்ளு", "தக்காளி", "கத்தரி", "மிளகாய்", "வெண்டை",
    "கரும்பு", "மஞ்சள்", "வாழை", "தென்னை", "மாமரம்",
    # Cultivation
    "சாகுபடி", "பயிர்", "பயிரி", "விதை", "நாற்று",
    "நட்டல்", "விதைத்தல்", "விதைக்க", "விதைக்கணும்",
    "நட்டு", "நாற்றுவித்தல்", "நாற்றங்கால்",
    "நடவு", "நடவு செய்",
    # Soil & Land
    "நிலம்", "மண்", "வயல்", "தோட்டம்", "புலம்",
    "நிலத்தை", "நிலத்தில்", "மண்ணை",
    # Fertilizer & Nutrients
    "உரம்", "உரத்தை", "உரங்கள்", "உரங்களை",
    "இயற்கை உரம்", "ரசாயன உரம்",
    "சத்து", "தழைச்சத்து", "மணிச்சத்து", "சாம்பல்சத்து",
    "யூரியா", "டிஏபி",
    # Irrigation & Water
    "நீர்", "நீர்ப்பாசனம்", "பாசனம்", "தண்ணீர்",
    "சொட்டு நீர்", "தெளிப்பு",
    # Pest & Disease
    "பூச்சி", "பூச்சிகள்", "பூச்சி மேலாண்மை",
    "நோய்", "நோய்கள்", "தாக்குதல்",
    "பூஞ்சை", "வைரஸ்", "பாக்டீரியா",
    "களை", "களைகள்",
    # Farming operations
    "அறுவடை", "மகசூல்",
    "உழவு", "உழுதல்", "உழவர்",
    "விவசாயம்", "விவசாயி", "விவசாயிகள்",
    "தோட்டக்கலை",
    # Symptoms
    "மஞ்சளா", "மஞ்சள்", "காய்தல்", "வாடுதல்",
    "இலை", "இலைகள்", "தண்டு", "வேர்",
    # Schemes
    "திட்டம்", "திட்டங்கள்", "அரசு திட்டம்",
    "மானியம்", "கடன்",
    # Actions / Verbs common in agriculture context
    "போடணும்", "போடலாம்", "போட வேண்டும்",
    "தெளிக்கணும்", "தெளிக்கலாம்",
    "கட்டுப்படுத்த", "கட்டுப்படுத்தல்", "கட்டுப்படுத்துறது",
    "தடுக்கலாம்", "தடுக்க", "தடுப்பு",
    "மேலாண்மை", "நிர்வாகம்",
    "பண்ணலாம்", "பண்ணணும்",
]

# -------------------------------------------------------------------
# Tamil question-words / contextual cues — short follow-up phrases
# that may not contain agriculture words but are clearly follow-ups
# -------------------------------------------------------------------
TAMIL_FOLLOWUP_CUES = [
    "அதுக்கப்புறம்", "அதற்குப்பிறகு", "அதுக்கு",
    "இதுக்கு", "இதற்கு", "இதை", "இதனால்",
    "அதை", "அதனால்", "அதில்", "அதற்கு",
    "முதல்ல", "முதலில்", "முதலாவது",
    "அப்புறம்", "பிறகு",
    "எப்போ", "எப்பொழுது", "எப்படி",
    "எவ்வளவு", "எந்த",
    "யாரு", "எங்கே",
    "என்ன பண்ணலாம்", "என்ன செய்யலாம்", "என்ன செய்யணும்",
    "என்ன பண்ணணும்",
    "ஏன்", "எதனால்",
    "இன்னும்", "மேலும்",
    "ஏதாவது", "ஏதாவது திட்டம்",
    "scheme இருக்கா", "திட்டம் இருக்கா",
    "apply பண்ணணும்", "apply பண்ணலாம்",
]

# -------------------------------------------------------------------
# English follow-up phrases — contextual questions without agri words
# -------------------------------------------------------------------
ENGLISH_FOLLOWUP_PHRASES = [
    "what should i do",
    "what do i do",
    "what about",
    "how about",
    "what next",
    "what after",
    "after that",
    "then what",
    "how much",
    "how many",
    "how often",
    "when should",
    "when do",
    "how should",
    "how do i",
    "how can i",
    "what is",
    "what are",
    "which one",
    "is there any",
    "are there any",
    "any scheme",
    "any program",
    "can i",
    "should i",
    "do i need",
    "how to",
    "tell me",
    "explain",
    "please help",
    "help me",
    "i want to",
    "i need to",
    "i am planning",
    "i plan to",
    "anything else",
    "what else",
    "next step",
    "first step",
    "what is the",
    "what are the",
    "first",
    "then",
    "also",
    "additionally",
]


def _contains_tamil(text):
    """Check if the text contains Tamil Unicode characters."""
    # Tamil Unicode range: U+0B80–U+0BFF
    return bool(re.search(r'[\u0B80-\u0BFF]', text))


def _check_english_keywords(text_lower):
    """Check for English agriculture keywords."""
    for keyword in ENGLISH_AGRICULTURE_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def _check_tamil_keywords(text):
    """Check for Tamil agriculture keywords."""
    for keyword in TAMIL_AGRICULTURE_KEYWORDS:
        if keyword in text:
            return True
    return False


def _is_contextual_followup(text_lower, text_original, has_active_context):
    """
    Detect if the question is a contextual follow-up that doesn't
    contain explicit agriculture keywords but logically continues
    an ongoing agricultural conversation.
    """
    if not has_active_context:
        return False

    # Check Tamil follow-up cues
    for cue in TAMIL_FOLLOWUP_CUES:
        if cue in text_original:
            return True

    # Check English follow-up phrases
    for phrase in ENGLISH_FOLLOWUP_PHRASES:
        if text_lower.startswith(phrase) or f" {phrase} " in f" {text_lower} ":
            return True

    # Short questions (≤ 8 words) during active context are likely follow-ups
    word_count = len(text_original.split())
    if has_active_context and word_count <= 8:
        # Check for question-starters common in follow-ups
        question_starters = [
            "what", "when", "how", "where", "which", "why",
            "is", "are", "can", "do", "does", "any", "tell",
        ]
        first_word = text_lower.split()[0] if text_lower.split() else ""
        if first_word in question_starters:
            return True

    return False


def is_agriculture_question(question, conversation_topic=None, previous_question=None):
    """
    Determine whether the question is agriculture-related.

    Parameters
    ----------
    question          : str  – current user question
    conversation_topic: str  – current tracked crop/topic (may be None)
    previous_question : str  – last user question (may be None)

    Returns True if the question should be handled by the RAG pipeline.
    """
    # Preserve original for Tamil checks; use lowercased for English checks
    text_original = question.strip()
    text_lower = text_original.lower()

    has_active_context = bool(conversation_topic)

    # 1. Check English agriculture keywords
    if _check_english_keywords(text_lower):
        return True

    # 2. Check Tamil agriculture keywords
    if _check_tamil_keywords(text_original):
        return True

    # 3. Check contextual follow-up (requires active agricultural conversation)
    if _is_contextual_followup(text_lower, text_original, has_active_context):
        return True

    # 4. If the text contains Tamil script AND there is an active context,
    #    treat it as an agriculture question — Tamil farmers rarely write
    #    unrelated questions in this domain-specific tool
    if _contains_tamil(text_original) and has_active_context:
        return True

    # 5. Very short Tamil-script messages with active context
    if _contains_tamil(text_original) and len(text_original.split()) <= 10:
        # Could still be a first agriculture question in Tamil
        # Allow it through — the RAG will handle irrelevance at retrieval time
        return True

    return False