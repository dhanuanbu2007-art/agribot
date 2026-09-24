const DIRECT_API_URL = "http://127.0.0.1:8000";

const PROXY_ENABLED = import.meta.env.DEV;

const CONFIGURED_API_URL = (
  import.meta.env.VITE_API_URL || ""
).trim();

const BASE_URL = PROXY_ENABLED
  ? ""
  : (CONFIGURED_API_URL || DIRECT_API_URL);


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
      }),
    }
  );

  return parseResponse(response);
}


// --------------------------------------------------
// Export API configuration
// --------------------------------------------------

export const API_BASE_URL = BASE_URL;