"""
Conversation state tracker for AgriGuide.

Tracks:
- Detected crop (English and Tamil names)
- Current conversation topic/subtopic
- Recent question history for follow-up resolution
"""

import re
import unicodedata


# -------------------------------------------------------------------
# Crop name map: English canonical name → list of recognizable forms
# (including Tamil script forms)
# -------------------------------------------------------------------
CROP_VARIATIONS = {
    "paddy": [
        "paddy",
        "rice",
        "நெல்",
        "நெல்லு",
        "நெல்லை",
        "நெல்லுக்கு",
        "நெல் crop",
        "நெல் பயிர்",
    ],

    "black gram": [
        "black gram",
        "urad",
        "ulundu",
        "உளுந்து",
        "உளுந்தங்காய்",
    ],

    "green gram": [
        "green gram",
        "moong",
        "paasi payiru",
        "பாசிப்பயிறு",
        "பச்சைப்பயிறு",
    ],

    "groundnut": [
        "groundnut",
        "peanut",
        "நிலக்கடலை",
        "கடலை",
    ],

    "cotton": [
        "cotton",
        "பருத்தி",
    ],

    "sesame": [
        "sesame",
        "gingelly",
        "எள்ளு",
        "எள்",
    ],

    "tomato": [
        "tomato",
        "தக்காளி",
    ],

    "brinjal": [
        "brinjal",
        "eggplant",
        "கத்தரிக்காய்",
        "கத்தரி",
    ],

    "chilli": [
        "chilli",
        "chili",
        "pepper",
        "மிளகாய்",
    ],

    "okra": [
        "okra",
        "ladyfinger",
        "bhindi",
        "வெண்டைக்காய்",
        "வெண்டை",
    ],

    # "சோளம்" removed from maize because it is also a Tamil
    # variation for sorghum. Use the unambiguous Tamil name
    # "மக்காச்சோளம்" for maize.
    "maize": [
        "maize",
        "corn",
        "மக்காச்சோளம்",
    ],

    "sorghum": [
        "sorghum",
        "jowar",
        "சோளம்",
    ],

    "wheat": [
        "wheat",
        "கோதுமை",
    ],

    "pearl millet": [
        "pearl millet",
        "bajra",
        "கம்பு",
    ],

    "finger millet": [
        "finger millet",
        "ragi",
        "ராகி",
        "கேழ்வரகு",
    ],

    "soybean": [
        "soybean",
        "soya",
        "சோயாபீன்",
    ],

    "sugarcane": [
        "sugarcane",
        "cane",
        "கரும்பு",
    ],

    "pigeon pea": [
        "pigeon pea",
        "tur",
        "red gram",
        "toor",
        "துவரை",
    ],

    "banana": [
        "banana",
        "வாழை",
        "வாழைப்பழம்",
    ],

    "turmeric": [
        "turmeric",
        "மஞ்சள்",
    ],

    "coconut": [
        "coconut",
        "தென்னை",
        "தேங்காய்",
    ],

    "mango": [
        "mango",
        "மாமரம்",
        "மாம்பழம்",
    ],
}


# -------------------------------------------------------------------
# Topic keywords → canonical subtopic tag
# -------------------------------------------------------------------
TOPIC_KEYWORDS = {
    "cultivation": [
        "cultivat",
        "sow",
        "plant",
        "nursery",
        "seedling",
        "transplant",
        "சாகுபடி",
        "விதை",
        "நாற்று",
        "நடவு",
        "பயிர்",
        "விதைக்க",
        "நட்டு",
        "விதைத்தல்",
    ],

    "land_preparation": [
        "land",
        "soil",
        "prepare",
        "plough",
        "till",
        "நிலம்",
        "மண்",
        "உழவு",
        "தயார்",
    ],

    "fertilizer": [
        "fertilizer",
        "fertiliser",
        "manure",
        "nutrient",
        "urea",
        "dap",
        "nitrogen",
        "phosphorus",
        "potassium",
        "compost",
        "organic",
        "basal",
        "top dress",
        "foliar",
        "உரம்",
        "சத்து",
        "யூரியா",
        "டிஏபி",
        "தழைச்சத்து",
        "மணிச்சத்து",
        "சாம்பல்சத்து",
        "இயற்கை உரம்",
    ],

    "irrigation": [
        "irrigation",
        "water",
        "drip",
        "sprinkler",
        "canal",
        "flood",
        "நீர்",
        "பாசனம்",
        "தண்ணீர்",
        "சொட்டு நீர்",
        "தெளிப்பு",
    ],

    "pest_management": [
        "pest",
        "insect",
        "bug",
        "larvae",
        "mite",
        "aphid",
        "pesticide",
        "insecticide",
        "spray",
        "பூச்சி",
        "பூச்சிகள்",
        "தெளிக்க",
        "கட்டுப்படுத்த",
    ],

    "disease_management": [
        "disease",
        "fungal",
        "virus",
        "blight",
        "rot",
        "rust",
        "spot",
        "wilt",
        "yellowing",
        "infection",
        "pathogen",
        "நோய்",
        "மஞ்சள்",
        "வாட்டம்",
        "கருகல்",
        "பூஞ்சை",
        "வைரஸ்",
        "பாக்டீரியா",
    ],

    "weed_management": [
        "weed",
        "herbicide",
        "weedicide",
        "களை",
        "களைகள்",
    ],

    "harvest": [
        "harvest",
        "harvesting",
        "yield",
        "produce",
        "post-harvest",
        "அறுவடை",
        "மகசூல்",
    ],

    "government_scheme": [
        "scheme",
        "subsidy",
        "loan",
        "government",
        "program",
        "benefit",
        "apply",
        "application",
        "registration",
        "திட்டம்",
        "மானியம்",
        "கடன்",
        "அரசு",
        "பதிவு",
        "apply",
    ],

    "general_info": [
        "about",
        "information",
        "details",
        "introduction",
        "overview",
        "பற்றி",
        "தகவல்",
        "விவரம்",
    ],
}


# -------------------------------------------------------------------
# Unicode normalization helper
# -------------------------------------------------------------------
def _normalize_text(text):
    """
    Normalize text for safer Unicode comparison.

    NFC keeps canonically equivalent Unicode sequences in a
    consistent composed form.
    """
    if not text:
        return ""

    return unicodedata.normalize("NFC", text.strip())


# -------------------------------------------------------------------
# Crop detection
# -------------------------------------------------------------------
def detect_crop(question):
    """
    Detect a crop name from the question.

    Checks all known crop variations including Tamil.
    Returns the canonical English crop name or None.
    """
    q = _normalize_text(question)
    q_lower = q.casefold()

    for canonical_name, variations in CROP_VARIATIONS.items():
        for variant in variations:
            normalized_variant = _normalize_text(variant)
            variant_lower = normalized_variant.casefold()

            if variant_lower in q_lower:
                return canonical_name

    return None


# -------------------------------------------------------------------
# Subtopic detection
# -------------------------------------------------------------------
def detect_subtopic(question):
    """
    Detect the agricultural subtopic from the question text.

    Returns a topic tag string or None.
    """
    question = _normalize_text(question)
    q_lower = question.casefold()

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            normalized_keyword = _normalize_text(keyword)
            keyword_lower = normalized_keyword.casefold()

            if keyword_lower in q_lower:
                return topic

    return None


# -------------------------------------------------------------------
# Conversation state
# -------------------------------------------------------------------
class ConversationState:
    """
    Tracks the running state of the agricultural conversation.

    Attributes
    ----------
    crop:
        Canonical crop name detected, e.g. "paddy".

    subtopic:
        Most recent agricultural subtopic, e.g. "fertilizer".

    question_history:
        List of recent user questions.
    """

    def __init__(self):
        self.crop = None
        self.subtopic = None
        self.question_history = []

    @property
    def has_context(self):
        """
        Return True when an agricultural crop/topic is active.
        """
        return self.crop is not None

    def update(self, question):
        """
        Update the conversation state using the new question.

        Existing crop/subtopic information is preserved when the
        new question does not explicitly mention a replacement.

        Returns self for chaining.
        """
        question = _normalize_text(question)

        detected_crop = detect_crop(question)
        detected_subtopic = detect_subtopic(question)

        if detected_crop:
            self.crop = detected_crop

        if detected_subtopic:
            self.subtopic = detected_subtopic

        self.question_history.append(question)

        # Keep only the last 6 questions.
        self.question_history = self.question_history[-6:]

        return self

    def get_context_summary(self):
        """
        Return a human-readable summary of the current context.
        """
        parts = []

        if self.crop:
            parts.append(f"crop={self.crop}")

        if self.subtopic:
            parts.append(f"subtopic={self.subtopic}")

        return ", ".join(parts) if parts else "no context"

    def reset(self):
        """
        Clear the current conversation state.
        """
        self.crop = None
        self.subtopic = None
        self.question_history = []


# -------------------------------------------------------------------
# Legacy function — kept for backward compatibility with chat.py
# -------------------------------------------------------------------
def update_conversation_topic(question, current_topic=None):
    """
    Simplified interface used by chat.py.

    Returns the detected crop name to use as the conversation topic.
    Falls back to current_topic if no crop is detected.
    """
    detected = detect_crop(question)

    if detected:
        return detected

    return current_topic