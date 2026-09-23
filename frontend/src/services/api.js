/**
 * Centralized API Service for AgriGuide
 * Connects directly to the existing FastAPI backend.
 */

// In development, the Vite server proxies /chat and /health to http://127.0.0.1:8000
// to seamlessly navigate browser CORS without modifying the backend.
const DIRECT_API_URL = 'http://127.0.0.1:8000';
const PROXY_ENABLED = true;

const BASE_URL = PROXY_ENABLED ? '' : DIRECT_API_URL;

/**
 * Check backend health status
 * @returns {Promise<{ online: boolean, data?: any }>}
 */
export async function checkBackendHealth() {
  try {
    const url = `${BASE_URL}/health`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      return { online: true, data };
    }
    return { online: false };
  } catch (error) {
    console.warn('[AgriGuide API] Health check failed:', error.message);
    return { online: false, error: error.message };
  }
}

/**
 * Send a user question to the AgriGuide RAG backend
 * @param {string} question
 * @returns {Promise<{ question: string, answer: string }>}
 */
export async function sendChatMessage(question) {
  if (!question || !question.trim()) {
    throw new Error('Question cannot be empty');
  }

  const endpoint = `${BASE_URL}/chat`;

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ question: question.trim() }),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      console.error('[AgriGuide API] Server error response:', response.status, errorText);
      throw new Error(`Server returned status ${response.status}`);
    }

    const data = await response.json();

    if (!data || typeof data.answer === 'undefined') {
      throw new Error('Unexpected response format from server');
    }

    return {
      question: data.question || question,
      answer: data.answer,
    };
  } catch (error) {
    console.error('[AgriGuide API] Chat request failed:', error);
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error("AgriGuide couldn't connect to the server. Please make sure the FastAPI backend is running.");
    }
    throw error;
  }
}
