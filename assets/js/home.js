/**
 * home.js — Login handler for both client and admin login pages.
 *
 * Role enforcement:
 *   - Client login page  → only allows role === 'client'
 *                          admin credentials are REJECTED with an error
 *   - Admin login page   → only allows role === 'admin'
 *                          client credentials are REJECTED with an error
 *
 * Which page we are on is detected by reading the <title> tag.
 */

'use strict';

// Detect current page role from the <title>
// client/login.html  has <title>Client Login</title>
// admin/login.html   has <title>Admin Login</title>
const PAGE_ROLE = document.title.toLowerCase().includes('admin') ? 'admin' : 'client';

document.addEventListener('DOMContentLoaded', () => {

  const loginBtn = document.querySelector('.btn-primary');
  if (!loginBtn) return;

  loginBtn.addEventListener('click', handleLogin);

  // Allow Enter key in password field
  const pwdInput = document.querySelector('input[type="password"]');
  if (pwdInput) {
    pwdInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleLogin();
    });
  }
});

async function handleLogin() {
  const emailInput = document.querySelector('input[type="email"]');
  const pwdInput   = document.querySelector('input[type="password"]');
  const btn        = document.querySelector('.btn-primary');

  const email    = (emailInput?.value || '').trim();
  const password = (pwdInput?.value  || '').trim();

  if (!email || !password) {
    showInlineError('Please enter your email and password.');
    return;
  }

  btn.textContent = 'Logging in…';
  btn.disabled    = true;

  try {
    const data = await apiCall('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    const returnedRole = data.user.role;

    // ── Role enforcement ────────────────────────────────────────────────────
    if (PAGE_ROLE === 'client' && returnedRole !== 'client') {
      // Admin credentials entered on the Client portal — show generic error
      // (don't reveal that the account exists but has a different role)
      clearAuth();
      showInlineError('Incorrect email or password.');
      btn.textContent = 'Login';
      btn.disabled    = false;
      return;
    }

    if (PAGE_ROLE === 'admin' && returnedRole !== 'admin') {
      // Client credentials entered on the Admin portal — show generic error
      clearAuth();
      showInlineError('Incorrect email or password.');
      btn.textContent = 'Login';
      btn.disabled    = false;
      return;
    }
    // ── End role enforcement ────────────────────────────────────────────────

    // Credentials are valid AND role matches this portal
    saveAuth(data.token, data.user);
    showAlert('Login successful! Redirecting…', 'success');

    setTimeout(() => {
      if (returnedRole === 'admin') {
        window.location.href = '../../pages/admin/dashboard.html';
      } else {
        window.location.href = '../../pages/client/submit-ticket.html';
      }
    }, 800);

  } catch (err) {
    showInlineError('Incorrect email or password.');
    btn.textContent = 'Login';
    btn.disabled    = false;
  }
}

function showInlineError(message) {
  let el = document.getElementById('login-error');
  if (!el) {
    el = document.createElement('p');
    el.id = 'login-error';
    el.style.cssText = `
      color: #ef4444;
      font-size: .9rem;
      margin-top: 10px;
      text-align: center;
      font-weight: 600;
    `;
    document.querySelector('.btn-primary').insertAdjacentElement('afterend', el);
  }
  el.textContent = message;
}
