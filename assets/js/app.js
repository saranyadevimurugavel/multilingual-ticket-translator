/**
 * app.js — Shared utilities used by every page.
 * Provides: API_BASE, apiCall(), getToken(), saveToken(), logout()
 */

'use strict';

// ── API Base URL ──────────────────────────────────────────────────────────────
// Automatically uses the Render backend in production, localhost in development
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:5000/api'
  : 'https://multilingual-ticket-translator.onrender.com/api';

// ── Token storage (localStorage) ─────────────────────────────────────────────
const getToken  = () => localStorage.getItem('mtt_token');
const getUser   = () => JSON.parse(localStorage.getItem('mtt_user') || 'null');
const saveAuth  = (token, user) => {
  localStorage.setItem('mtt_token', token);
  localStorage.setItem('mtt_user',  JSON.stringify(user));
};
const clearAuth = () => {
  localStorage.removeItem('mtt_token');
  localStorage.removeItem('mtt_user');
};

// ── Central fetch wrapper ─────────────────────────────────────────────────────
async function apiCall(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    // Throw the server's error message so callers can read it
    const err = new Error(data.error || `Request failed (${response.status})`);
    err.status = response.status;
    err.data   = data;
    throw err;
  }
  return data;
}

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
  clearAuth();
  window.location.href = '/index.html';
}

// ── Show toast / alert helper ─────────────────────────────────────────────────
function showAlert(message, type = 'success') {
  // Simple inline alert — works without any extra library
  const existing = document.getElementById('mtt-alert');
  if (existing) existing.remove();

  const div = document.createElement('div');
  div.id = 'mtt-alert';
  div.style.cssText = `
    position:fixed; top:20px; right:20px; z-index:9999;
    padding:14px 22px; border-radius:8px; font-weight:600;
    background:${type === 'success' ? '#22c55e' : '#ef4444'};
    color:#fff; box-shadow:0 4px 12px rgba(0,0,0,.2);
    transition:opacity .4s;
  `;
  div.textContent = message;
  document.body.appendChild(div);
  setTimeout(() => { div.style.opacity = '0'; setTimeout(() => div.remove(), 400); }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('MTT App initialised');
});
