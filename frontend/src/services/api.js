const LOCAL_API_URL = "http://127.0.0.1:8000";
const PROD_API_URL = "https://agriguide-backend-mzok.onrender.com";

const PROXY_ENABLED = import.meta.env.DEV;

const CONFIGURED_API_URL = (
  import.meta.env.VITE_API_URL || ""
).trim();

const BASE_URL = PROXY_ENABLED
  ? ""
  : (CONFIGURED_API_URL || PROD_API_URL);


// --------------------------------------------------
// Helper
// --------------------------------------------------

async function parseResponse(response) {
  let data = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message =
      data?.detail ||
      data?.message ||
      `Request failed with status ${response.status}`;

    throw new Error(message);
  }

  return data;
}


// --------------------------------------------------
// Backend health check
// --------------------------------------------------

export async function checkHealth() {
  const response = await fetch(
    `${BASE_URL}/health`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    }
  );

  return parseResponse(response);
}


// --------------------------------------------------
// Send chat message
// --------------------------------------------------

export async function sendChatMessage(
  question,
  conversationId,
  idToken = null
) {
  if (!question || !question.trim()) {
    throw new Error("Question cannot be empty.");
  }

  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  // Firebase authentication token
  if (idToken) {
    headers.Authorization = `Bearer ${idToken}`;
  }

  const response = await fetch(
    `${BASE_URL}/chat`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        question: question.trim(),
        conversation_id: conversationId,
      }),
    }
  );

  return parseResponse(response);
}

// --------------------------------------------------
// History Management
// --------------------------------------------------

export async function getHistory(idToken) {
  const headers = { Accept: "application/json" };
  if (idToken) headers.Authorization = `Bearer ${idToken}`;

  const response = await fetch(`${BASE_URL}/history`, {
    method: "GET",
    headers,
  });
  return parseResponse(response);
}

export async function saveHistory(conversations, idToken) {
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (idToken) headers.Authorization = `Bearer ${idToken}`;

  const response = await fetch(`${BASE_URL}/history`, {
    method: "POST",
    headers,
    body: JSON.stringify(conversations),
  });
  return parseResponse(response);
}


// --------------------------------------------------
// TTS Management
// --------------------------------------------------

export async function generateTamilTTS(text, idToken = null) {
  if (!text || !text.trim()) {
    throw new Error("Text cannot be empty.");
  }

  const headers = {
    "Content-Type": "application/json",
  };

  if (idToken) {
    headers.Authorization = `Bearer ${idToken}`;
  }

  const response = await fetch(`${BASE_URL}/tts/tamil`, {
    method: "POST",
    headers,
    body: JSON.stringify({ text: text.trim() }),
  });

  if (!response.ok) {
    let errMsg = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      errMsg = data?.detail || data?.message || errMsg;
    } catch {}
    throw new Error(errMsg);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}


// --------------------------------------------------
// Export API configuration
// --------------------------------------------------

export const API_BASE_URL = BASE_URL;