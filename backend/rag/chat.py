from backend.retrieval.conversation_state import ConversationState, update_conversation_topic
from backend.retrieval.query_resolver import resolve_search_query
from backend.retrieval.retriever import retrieve_relevant_chunks
from backend.retrieval.relevance_checker import is_agriculture_question
from backend.generation.gemini_generator import generate_answer


# Off-topic rejection messages in both languages
_OFF_TOPIC_ENGLISH = (
    "I'm AgriGuide, an agriculture-focused assistant. "
    "I can help you with crops, cultivation, fertilizers, "
    "irrigation, pests, diseases, and agricultural schemes. "
    "Please ask me anything related to farming!"
)

_OFF_TOPIC_TAMIL = (
    "நான் AgriGuide, ஒரு விவசாய உதவியாளர். "
    "பயிர் சாகுபடி, உரம், நீர்ப்பாசனம், பூச்சி மேலாண்மை, "
    "நோய் கட்டுப்பாடு, மற்றும் அரசு திட்டங்கள் பற்றி "
    "என்னிடம் கேளுங்கள்!"
)

# Natural greeting responses — short, friendly, inviting
_GREETING_ENGLISH = (
    "Hello! I'm AgriGuide, your agriculture assistant. "
    "You can ask me anything about crops, cultivation, fertilizers, "
    "irrigation, pest or disease management, or government schemes. "
    "How can I help you today?"
)

_GREETING_TAMIL = (
    "வணக்கம்! நான் AgriGuide, உங்கள் விவசாய உதவியாளர். "
    "பயிர் சாகுபடி, உரம், நீர்ப்பாசனம், பூச்சி மேலாண்மை, "
    "நோய் கட்டுப்பாடு அல்லது அரசு திட்டங்கள் பற்றி கேளுங்கள். "
    "இன்று நான் எப்படி உதவலாம்?"
)

# Exact greeting tokens — English (lowercase) and Tamil
_GREETING_TOKENS_EN = {
    "hi", "hello", "hey", "howdy", "greetings", "hai",
    "good morning", "good afternoon", "good evening", "good day",
}

_GREETING_TOKENS_TA = {
    "வணக்கம்", "ஹாய்", "ஹலோ",
    "காலை வணக்கம்", "மாலை வணக்கம்", "இரவு வணக்கம்",
}


def _contains_tamil(text):
    import re
    return bool(re.search(r'[\u0B80-\u0BFF]', text))


def _is_pure_greeting(text):
    """
    Return True only when the entire message is a greeting with no
    agriculture content mixed in.

    Examples that return True:  "Hi", "Hello!", "வணக்கம்", "Hey there"
    Examples that return False: "Hello, how do I grow paddy?", "வணக்கம் நெல் சாகுபடி"
    """
    stripped = text.strip()
    normalized = stripped.lower().strip("!.,? ")

    # Check English greeting tokens (exact match after stripping punctuation)
    for token in _GREETING_TOKENS_EN:
        if normalized == token:
            return True
        # Allow "hey there", "hi there", "hello there"
        if normalized == f"{token} there":
            return True

    # Check Tamil greeting tokens
    for token in _GREETING_TOKENS_TA:
        remainder = stripped.replace(token, "").strip("!.,? ")
        if not remainder:
            return True

    return False


class AgriGuideChat:

    def __init__(self):
        # Use the new richer ConversationState
        self.state = ConversationState()
        self.previous_interaction_id = None

        # Legacy attribute kept for compatibility
        self.conversation_topic = None

    def chat(self, question):

        # -------------------------------------------------------
        # 0. Handle pure greetings naturally before anything else
        #    "Hi", "Hello", "வணக்கம்" etc. get a friendly welcome.
        #    Mixed messages ("Hello, how do I grow paddy?") fall
        #    through to the normal RAG pipeline below.
        # -------------------------------------------------------
        if _is_pure_greeting(question):
            if _contains_tamil(question):
                return _GREETING_TAMIL
            return _GREETING_ENGLISH

        # -------------------------------------------------------
        # 1. Check whether the question is agriculture-related
        #    Pass conversation state so follow-ups are accepted
        # -------------------------------------------------------
        if not is_agriculture_question(
            question,
            conversation_topic=self.state.crop,
            previous_question=(
                self.state.question_history[-1]
                if self.state.question_history else None
            ),
        ):
            # Return rejection message in the user's language
            if _contains_tamil(question):
                return _OFF_TOPIC_TAMIL
            return _OFF_TOPIC_ENGLISH

        # -------------------------------------------------------
        # 2. Update the conversation state (crop, subtopic, history)
        # -------------------------------------------------------
        self.state.update(question)

        # Keep legacy attribute in sync
        self.conversation_topic = self.state.crop

        print(f"\n[Conversation context]: {self.state.get_context_summary()}")

        # -------------------------------------------------------
        # 3. Resolve the search query for vector retrieval
        # -------------------------------------------------------
        search_query = resolve_search_query(
            question=question,
            conversation_topic=self.conversation_topic,
            conversation_state=self.state,
        )

        print(f"\n[Search query]: {search_query}")

        # -------------------------------------------------------
        # 4. Retrieve relevant agricultural information from Qdrant
        # -------------------------------------------------------
        retrieved_chunks = retrieve_relevant_chunks(
            search_query,
            top_k=5
        )

        # -------------------------------------------------------
        # 5. Generate answer using Gemini with language awareness
        # -------------------------------------------------------
        interaction = generate_answer(
            question=question,
            retrieved_chunks=retrieved_chunks,
            previous_interaction_id=self.previous_interaction_id,
            conversation_state=self.state,
        )

        # -------------------------------------------------------
        # 6. Save conversation memory
        # -------------------------------------------------------
        self.previous_interaction_id = interaction.id

        return interaction.output_text