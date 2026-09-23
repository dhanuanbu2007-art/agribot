"""
Language detector for AgriGuide.

Detects whether a question is primarily Tamil, English, or mixed.
This drives the response language instruction sent to Gemini.
"""

import re


def detect_language(question):
    """
    Detect the primary language of the question.

    Returns one of: "tamil", "english", "mixed_tamil", "mixed_english"

    Rules:
    - Count Tamil Unicode characters and Latin characters separately.
    - If Tamil chars dominate (>30% of non-space chars) → Tamil-primary
    - If Tamil chars present but English dominates → mixed_english
    - If mostly English → English
    """
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', question))
    latin_chars = len(re.findall(r'[a-zA-Z]', question))
    total_relevant = tamil_chars + latin_chars

    if total_relevant == 0:
        return "english"  # Numbers/symbols only → default to English

    tamil_ratio = tamil_chars / total_relevant

    if tamil_ratio >= 0.60:
        return "tamil"
    elif tamil_ratio >= 0.20:
        # Mixed — determine primary direction
        # If the sentence structure appears Tamil (starts with Tamil words)
        first_char = question.strip()[0] if question.strip() else ""
        if "\u0B80" <= first_char <= "\u0BFF":
            return "mixed_tamil"   # Tamil-primary mixed
        else:
            return "mixed_english"  # English-primary mixed
    else:
        return "english"


def get_response_language_instruction(lang_code):
    """
    Return a Gemini system instruction snippet that enforces
    the detected language for the response.
    """
    instructions = {
        "tamil": (
            "IMPORTANT LANGUAGE RULE: The user has asked their question in Tamil. "
            "You MUST respond ENTIRELY in Tamil (தமிழ்). "
            "Do NOT respond in English. "
            "Use natural, farmer-friendly conversational Tamil. "
            "Technical terms (like fertilizer names, chemical names) may remain in "
            "English within an otherwise Tamil response if there is no good Tamil equivalent. "
            "Agricultural measurements and numbers may be written in digits. "
            "Your ENTIRE answer must be in Tamil script."
        ),
        "mixed_tamil": (
            "IMPORTANT LANGUAGE RULE: The user's question is primarily in Tamil with some English words. "
            "You MUST respond primarily in Tamil (தமிழ்). "
            "Technical terms may remain in English naturally. "
            "Your response should feel natural and farmer-friendly in Tamil."
        ),
        "mixed_english": (
            "IMPORTANT LANGUAGE RULE: The user's question is primarily in English with some Tamil words. "
            "Respond primarily in English. "
            "You may include Tamil terms naturally where appropriate."
        ),
        "english": (
            "IMPORTANT LANGUAGE RULE: The user has asked in English. "
            "Respond in clear, simple, farmer-friendly English."
        ),
    }
    return instructions.get(lang_code, instructions["english"])
