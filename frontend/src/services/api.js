import axios from "axios";

// ----------------------------------------------------------------
// Token storage helpers — single source of truth.
// localStorage is JavaScript-accessible and intentionally chosen
// for this development phase. A production deployment must migrate
// to HttpOnly Secure cookie transport with CSRF protection.
// ----------------------------------------------------------------
const TOKEN_KEY = "arxiv_gpt_token";

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

// ----------------------------------------------------------------
// Axios instance — same-origin calls, dynamic Authorization header.
// ----------------------------------------------------------------
const API = axios.create({ baseURL: "/" });

// Request interceptor: attach Bearer token when one exists.
API.interceptors.request.use((config) => {
  const token = tokenStorage.get();
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

// ----------------------------------------------------------------
// Auth endpoints
// Response shape for /auth/register and /auth/login:
//   { access_token, token_type, user: { id, email, full_name, is_active, created_at } }
// Response shape for /auth/me:
//   { id, email, full_name, is_active, created_at }
// ----------------------------------------------------------------

export const registerUser = (email, password, fullName) =>
  API.post("/auth/register", {
    email,
    password,
    full_name: fullName || undefined,
  });

export const loginUser = (email, password) =>
  API.post("/auth/login", { email, password });

export const fetchCurrentUser = () =>
  API.get("/auth/me");

// ----------------------------------------------------------------
// Research endpoints
// POST /search response: { papers: [...], query: string, pdf_filename: string|null }
// GET  /history response: [{ id, query, timestamp, pdf_filename, papers: [...] }, ...]
// ----------------------------------------------------------------

export const searchPapers = (data) =>
  API.post("/search", data);

export const fetchHistory = () =>
  API.get("/history");

export const downloadPdfUrl = (filename) =>
  `/download_pdf?filename=${encodeURIComponent(filename)}`;
