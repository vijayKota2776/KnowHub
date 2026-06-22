/**
 * KnowHub API Client
 * Centralised fetch wrapper that auto-injects Bearer tokens,
 * handles errors, and returns parsed JSON.
 */

const BASE_URL = '/api/v1';

function getToken() {
  return localStorage.getItem('kh_token');
}

async function request(method, path, body = null, requireAuth = false) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  } else if (requireAuth) {
    throw new Error('Not authenticated');
  }

  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, options);

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {}
    throw new Error(detail);
  }

  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────
export const api = {
  auth: {
    register: (data) => request('POST', '/auth/register', data),
    login: (data) => request('POST', '/auth/login', data),
  },

  // ── Users ──────────────────────────────────────────────────
  users: {
    me: () => request('GET', '/users/me', null, true),
    profile: (id) => request('GET', `/users/${id}`, null, true),
    follow: (id) => request('POST', `/users/${id}/follow`, null, true),
  },

  // ── Topics ─────────────────────────────────────────────────
  topics: {
    list: () => request('GET', '/topics'),
    create: (data) => request('POST', '/topics', data, true),
    follow: (id) => request('POST', `/topics/${id}/follow`, null, true),
  },

  // ── Questions ──────────────────────────────────────────────
  questions: {
    create: (data) => request('POST', '/questions', data, true),
    get: (id) => request('GET', `/questions/${id}`),
    comments: (id) => request('GET', `/questions/${id}/comments`),
    addComment: (id, data) => request('POST', `/questions/${id}/comments`, data, true),
  },

  // ── Answers ────────────────────────────────────────────────
  answers: {
    create: (questionId, data) => request('POST', `/questions/${questionId}/answers`, data, true),
    vote: (questionId, answerId, voteType) =>
      request('POST', `/questions/${questionId}/answers/${answerId}/vote`, { vote_type: voteType }, true),
  },

  // ── Feed ───────────────────────────────────────────────────
  feed: {
    get: (limit = 20) => request('GET', `/feed?limit=${limit}`, null, true),
  },

  // ── Search ─────────────────────────────────────────────────
  search: {
    query: (q, topK = 10) => request('GET', `/search?q=${encodeURIComponent(q)}&top_k=${topK}`),
  },

  // ── Recommendations ────────────────────────────────────────
  recommendations: {
    topics: () => request('GET', '/recommendations/topics', null, true),
  },
};
