"""
Offline logic test for AgriGuide's relevance checker,
conversation state, query resolver, and language detector.

Does NOT require Qdrant or Gemini to be running.
Run from the project root:
    python backend/test/test_offline_logic.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.retrieval.relevance_checker import is_agriculture_question
from backend.retrieval.conversation_state import ConversationState
from backend.retrieval.query_resolver import resolve_search_query
from backend.retrieval.language_detector import detect_language

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

def check(label, result, expected=True):
    status = PASS if result == expected else FAIL
    print(f"  [{status}] {label}")
    if result != expected:
        print(f"         got: {result!r}, expected: {expected!r}")

# ===================================================================
# SECTION 1: Relevance checker - no context
# ===================================================================
print("\n=== Relevance Checker (no context) ===")

check("English: paddy cultivation",
      is_agriculture_question("I want to cultivate paddy"))
check("English: fertilizer",
      is_agriculture_question("How should fertilizer be managed?"))
check("Tamil: நெல் விதை",
      is_agriculture_question("நான் நெல் விதைக்கணும்"))
check("Tamil: சாகுபடி",
      is_agriculture_question("நான் நெல் சாகுபடி பண்ணலாம்னு இருக்கேன். முதல்ல என்ன பண்ணணும்?"))
check("Tamil: உரம்",
      is_agriculture_question("உரம் எப்போ போடணும்?"))
check("Tamil: பூச்சி",
      is_agriculture_question("பூச்சி இருக்கு. அதை எப்படி கட்டுப்படுத்துறது?"))
check("Tamil: இலை மஞ்சள்",
      is_agriculture_question("என் நெல் இலை மஞ்சளா மாறுது. என்ன பண்ணலாம்?"))
check("Tamil: திட்டம்",
      is_agriculture_question("இதுக்கு ஏதாவது அரசு திட்டம் இருக்கா?"))
check("Mixed: fertilizer in Tamil sentence",
      is_agriculture_question("நெல்லுக்கு எந்த fertilizer போடணும்?"))
check("Non-agri: weather",
      is_agriculture_question("What is today's weather?"), expected=False)
check("Non-agri: cinema",
      is_agriculture_question("What movie should I watch?"), expected=False)

# ===================================================================
# SECTION 2: Relevance checker - WITH context (follow-up questions)
# ===================================================================
print("\n=== Relevance Checker (with active paddy context) ===")

state = ConversationState()
state.update("நான் நெல் சாகுபடி பண்ணலாம்னு இருக்கேன்.")
crop = state.crop

check("Tamil follow-up: அதுக்கப்புறம் என்ன",
      is_agriculture_question("அதுக்கப்புறம் என்ன செய்யணும்?", conversation_topic=crop))
check("Tamil follow-up: எப்போ விதைக்கணும்",
      is_agriculture_question("எப்போ விதைக்கணும்?", conversation_topic=crop))
check("Tamil follow-up: எவ்வளவு போடணும்",
      is_agriculture_question("எவ்வளவு போடணும்?", conversation_topic=crop))
check("Tamil follow-up: இதுக்கு திட்டம்",
      is_agriculture_question("இதுக்கு ஏதாவது திட்டம் இருக்கா?", conversation_topic=crop))
check("English follow-up: what should I do after",
      is_agriculture_question("What should I do after that?", conversation_topic=crop))
check("English follow-up: how much",
      is_agriculture_question("How much should I apply?", conversation_topic=crop))
check("English follow-up: any scheme",
      is_agriculture_question("Is there any government scheme for this?", conversation_topic=crop))
check("English follow-up: what next",
      is_agriculture_question("What next?", conversation_topic=crop))
check("Short Tamil: apply பண்ணணும்",
      is_agriculture_question("apply பண்ணணும்", conversation_topic=crop))

# ===================================================================
# SECTION 3: Conversation State - crop detection (Tamil + English)
# ===================================================================
print("\n=== Conversation State: Crop Detection ===")

def test_crop(question, expected_crop):
    s = ConversationState()
    s.update(question)
    check(f"Crop from: '{question[:50]}'", s.crop, expected_crop)

test_crop("I want to cultivate paddy", "paddy")
test_crop("நான் நெல் சாகுபடி பண்ணலாம்னு இருக்கேன்.", "paddy")
test_crop("நெல்லுக்கு எந்த fertilizer போடணும்?", "paddy")
test_crop("Black gram cultivation advice", "black gram")
test_crop("உளுந்து எப்படி பயிரிடுவது?", "black gram")
test_crop("Groundnut pest control", "groundnut")
test_crop("நிலக்கடலை நோய் கட்டுப்பாடு", "groundnut")

# ===================================================================
# SECTION 4: Conversation State - subtopic detection
# ===================================================================
print("\n=== Conversation State: Subtopic Detection ===")

def test_subtopic(question, expected_subtopic):
    s = ConversationState()
    s.update(question)
    check(f"Subtopic from: '{question[:50]}'", s.subtopic, expected_subtopic)

test_subtopic("How should fertilizer be applied?", "fertilizer")
test_subtopic("உரம் எப்போ போடணும்?", "fertilizer")
test_subtopic("Pest management for paddy", "pest_management")
test_subtopic("பூச்சி மேலாண்மை என்ன?", "pest_management")
test_subtopic("What government scheme is available?", "government_scheme")
test_subtopic("அரசு திட்டம் இருக்கா?", "government_scheme")
test_subtopic("How to harvest the crop?", "harvest")
test_subtopic("Irrigation for paddy", "irrigation")

# ===================================================================
# SECTION 5: Query Resolver - search query building
# ===================================================================
print("\n=== Query Resolver: Search Queries ===")

def test_query(question, state_updates=None, expected_contains=None):
    s = ConversationState()
    if state_updates:
        for q in state_updates:
            s.update(q)
    query = resolve_search_query(question, conversation_state=s)
    print(f"  Q: '{question[:55]}'")
    print(f"  → '{query[:80]}'")
    if expected_contains:
        ok = all(e.lower() in query.lower() for e in expected_contains)
        status = PASS if ok else FAIL
        print(f"  [{status}] contains {expected_contains}")
    print()

test_query("அதுக்கப்புறம் என்ன செய்யணும்?",
           state_updates=["நான் நெல் சாகுபடி பண்ணலாம்னு இருக்கேன்."],
           expected_contains=["paddy"])

test_query("எவ்வளவு போடணும்?",
           state_updates=["நான் நெல் சாகுபடி பண்ணலாம்.", "உரம் எப்போ போடணும்?"],
           expected_contains=["paddy", "fertilizer"])

test_query("What should I do after that?",
           state_updates=["I want to cultivate paddy."],
           expected_contains=["paddy"])

test_query("Is there any government scheme?",
           state_updates=["Paddy cultivation", "Fertilizer management"],
           expected_contains=["paddy", "government"])

test_query("I want to cultivate paddy. What should I do first?",
           state_updates=[],
           expected_contains=["paddy"])

# ===================================================================
# SECTION 6: Language Detector
# ===================================================================
print("\n=== Language Detector ===")

def test_lang(question, expected):
    result = detect_language(question)
    check(f"Lang of: '{question[:55]}'", result, expected)

test_lang("நான் நெல் சாகுபடி பண்ணலாம்னு இருக்கேன்.", "tamil")
test_lang("அதுக்கப்புறம் என்ன செய்யணும்?", "tamil")
test_lang("உரம் எப்போ போடணும்?", "tamil")
test_lang("How should I cultivate paddy?", "english")
test_lang("What is the best fertilizer for rice?", "english")
test_lang("நெல்லுக்கு எந்த fertilizer போடணும்?", "mixed_tamil")
test_lang("நெல் cropக்கு என்ன fertilizer பயன்படுத்தலாம்?", "mixed_tamil")

print("\n=== All tests complete ===\n")
