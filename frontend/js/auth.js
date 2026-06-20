import { auth, users, setTokens, clearTokens, getTokens, sanitizeHtml } from './api.js';

export async function handleSignup(event) {
  event.preventDefault();

  const form = event.target;
  const fullName = form.querySelector('#full-name')?.value.trim();
  const email = form.querySelector('#email')?.value.trim().toLowerCase();
  const password = form.querySelector('#password')?.value;
  const roleInput = form.querySelector('input[name="user-role"]:checked');
  const termsChecked = form.querySelector('#terms')?.checked;

  if (!fullName || !email || !password || !roleInput) {
    showError(form, 'Please fill out all required fields.');
    return;
  }

  if (password.length < 8) {
    showError(form, 'Password must be at least 8 characters.');
    return;
  }

  if (!termsChecked) {
    showError(form, 'You must agree to the terms and privacy policy.');
    return;
  }

  try {
    const result = await auth.signup({ full_name: fullName, email, password, role: roleInput.value });
    setTokens(result.access_token, result.refresh_token);
    localStorage.setItem('jetstark_user', JSON.stringify(result.user));
    window.location.href = '/dashboard.html';
  } catch (err) {
    showError(form, err.message);
  }
}

export async function handleLogin(event) {
  event.preventDefault();

  const form = event.target;
  const email = form.querySelector('#email-login')?.value.trim().toLowerCase();
  const password = form.querySelector('#password-login')?.value;

  if (!email || !password) {
    showError(form, 'Enter both email and password to continue.');
    return;
  }

  try {
    const result = await auth.login({ email, password });
    setTokens(result.access_token, result.refresh_token);
    localStorage.setItem('jetstark_user', JSON.stringify(result.user));
    window.location.href = '/dashboard.html';
  } catch (err) {
    showError(form, err.message);
  }
}

export async function handleLogout() {
  clearTokens();
  window.location.href = '/login.html';
}

export function setupHeader() {
  const userData = localStorage.getItem('jetstark_user');
  if (!userData) return;

  try {
    const user = JSON.parse(userData);
    const nameEl = document.getElementById('header-user-name');
    const initialsEl = document.getElementById('user-initials');
    const userNameEl = document.getElementById('user-name');

    if (nameEl) nameEl.textContent = sanitizeHtml(user.full_name);
    if (userNameEl) userNameEl.textContent = sanitizeHtml(user.full_name);
    if (initialsEl) {
      const parts = user.full_name.split(' ');
      initialsEl.textContent = ((parts[0]?.[0] || '') + (parts[1]?.[0] || '')).toUpperCase();
    }
  } catch {}
}

export function setupPublicHeader() {
  const { access } = getTokens();
  const authActions = document.querySelector('.auth-actions');
  if (!authActions) return;

  authActions.hidden = !!access;
  if (!access) return;

  const userData = localStorage.getItem('jetstark_user');
  if (!userData) return;
  let user;
  try { user = JSON.parse(userData); } catch { return; }

  const headerInner = authActions.closest('.header-inner');
  if (!headerInner) return;

  if (headerInner.querySelector('.user-panel')) return;

  const panel = document.createElement('div');
  panel.className = 'header-right';
  panel.innerHTML = `
    <div class="user-panel">
      <div class="user-avatar" id="user-initials">${((user.full_name?.split(' ')[0]?.[0] || '') + (user.full_name?.split(' ')[1]?.[0] || '')).toUpperCase()}</div>
      <div class="user-name" id="header-user-name">${sanitizeHtml(user.full_name || 'User')}</div>
    </div>
    <button class="header-dashboard-btn" onclick="window.location.href='/dashboard.html'">Dashboard</button>
    <button class="header-logout-btn" onclick="sessionStorage.clear();localStorage.removeItem('jetstark_user');window.location.href='/login.html'">Log out</button>
  `;
  headerInner.appendChild(panel);
}

function showError(form, message) {
  const errorEl = form.querySelector('.error-message') || form.querySelector('#login-error');
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.hidden = false;
  } else {
    alert(message);
  }
}

export function requireAuth() {
  const { access } = getTokens();
  if (!access) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}
