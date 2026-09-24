"""
Language detector for AgriGuide.

Detects whether a question is primarily:
- Tamil
- English
- Tamil-English mixed
- English-Tamil mixed

This drives the response language instruction sent to Gemini.
"""

import re
import unicodedata


# -------------------------------------------------------------------
# Unicode / text normalization
# -------------------------------------------------------------------
def _normalize_text(text):
    """
    Normalize Unicode text and remove unnecessary surrounding spaces.
    """
    if not text:
        return ""

    return unicodedata.normalize("NFC", text.strip())


# -------------------------------------------------------------------
# Character detection helpers
# -------------------------------------------------------------------
def _count_tamil_chars(text):
    """
    Count Tamil Unicode characters.

    Tamil Unicode block:
    U+0B80 - U+0BFF
    """
    return len(re.findall(r"[\u0B80-\u0BFF]", text))


def _count_latin_chars(text):
    """
    Count English/Latin alphabet characters.
    """
    return len(re.findall(r"[a-zA-Z]", text))


def _has_tamil_script(text):
    """
    Return True when the text contains Tamil script.
    """
    return bool(re.search(r"[\u0B80-\u0BFF]", text))


def _has_latin_script(text):
    """
    Return True when the text contains Latin characters.
    """
    return bool(re.search(r"[a-zA-Z]", text))


# -------------------------------------------------------------------
# Detect primary language
# -------------------------------------------------------------------
def detect_language(question):
    """
    Detect the primary language of the question.

    Returns one of:

        "tamil"
        "english"
        "mixed_tamil"
        "mixed_english"

    Rules:
    - Mostly Tamil script       -> tamil
    - Mostly English/Latin      -> english
    - Both scripts present      -> mixed
    - Mixed questions are classified according to which script
      appears to dominate.
    """

    question = _normalize_text(question)

    if not question:
        return "english"

    tamil_chars = _count_tamil_chars(question)
    latin_chars = _count_latin_chars(question)

    total_relevant = tamil_chars + latin_chars

    # No Tamil or Latin characters.
    # Examples:
    # "12345"
    # "???"
    # "100 kg"
    if total_relevant == 0:
        return "english"

    # Only Tamil script.
    if tamil_chars > 0 and latin_chars == 0:
        return "tamil"

    # Only Latin script.
    if latin_chars > 0 and tamil_chars == 0:
        return "english"

    # Both Tamil and Latin are present.
    tamil_ratio = tamil_chars / total_relevant

    # Strong Tamil dominance.
    if tamil_ratio >= 0.60:
        return "mixed_tamil"

    # Strong English dominance.
    if tamil_ratio < 0.20:
        return "mixed_english"

    # Balanced mixed-language question.
    #
    # Look at the first meaningful character to determine
    # which language the sentence appears to start with.
    first_meaningful_char = ""

    for char in question:
        if char.isalnum():
            first_meaningful_char = char
            break

    if first_meaningful_char:
        if "\u0B80" <= first_meaningful_char <= "\u0BFF":
            return "mixed_tamil"

    return "mixed_english"


# -------------------------------------------------------------------
# Response language instructions
# -------------------------------------------------------------------
def get_response_language_instruction(lang_code):
    """
    Return the Gemini instruction that controls the response language.
    """

    instructions = {

        # -----------------------------------------------------------
        # Tamil
        # -----------------------------------------------------------
        "tamil": (
            "IMPORTANT LANGUAGE RULE: "
            "The user has asked their question in Tamil. "
            "You MUST respond ENTIRELY in Tamil (தமிழ்). "
            "Do NOT respond in English. "
            "Use natural, farmer-friendly conversational Tamil. "
            "Technical terms such as fertilizer names, chemical names, "
            "crop names, disease names, and scientific terms may remain "
            "in English when there is no natural Tamil equivalent. "
            "Agricultural measurements and numbers may be written using digits. "
            "The explanation itself must be primarily in Tamil script."
        ),

        # -----------------------------------------------------------
        # Tamil + English
        # -----------------------------------------------------------
        "mixed_tamil": (
            "IMPORTANT LANGUAGE RULE: "
            "The user's question contains both Tamil and English, "
            "but Tamil is the primary language. "
            "Respond primarily in Tamil (தமிழ்). "
            "Technical agriculture terms may remain in English naturally "
            "when that is clearer for the farmer. "
            "Do not unnecessarily translate technical terms. "
            "Keep the response natural, conversational, and farmer-friendly."
        ),

        # -----------------------------------------------------------
        # English + Tamil
        # -----------------------------------------------------------
        "mixed_english": (
            "IMPORTANT LANGUAGE RULE: "
            "The user's question contains both English and Tamil, "
            "but English is the primary language. "
            "Respond primarily in clear, simple English. "
            "Tamil agricultural terms may be included naturally when useful. "
            "Do not unnecessarily switch the entire response to Tamil."
        ),

        # -----------------------------------------------------------
        # English
        # -----------------------------------------------------------
        "english": (
            "IMPORTANT LANGUAGE RULE: "
            "The user has asked their question in English. "
            "Respond in clear, simple, farmer-friendly English. "
            "Use practical explanations and avoid unnecessary jargon."
        ),
    }

    return instructions.get(
        lang_code,
        instructions["english"]
    )