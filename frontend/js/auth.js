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
    <nav class="nav-links">
      <a href="/marketplace.html">Marketplace</a>
      <a href="/cart.html">Cart</a>
      <a href="/wishlist.html">Wishlist</a>
    </nav>
    <div class="notification-bell" id="notification-bell">
      <span class="bell-icon" id="bell-icon">&#128276;</span>
      <span class="notification-badge" id="notification-badge" hidden>0</span>
      <div class="notification-dropdown" id="notification-dropdown" hidden>
        <div class="notification-header"><strong>Notifications</strong></div>
        <div class="notification-list" id="notification-list">
          <p class="notification-empty">No notifications yet</p>
        </div>
      </div>
    </div>
    <div class="user-panel">
      <div class="user-avatar" id="user-initials">${((user.full_name?.split(' ')[0]?.[0] || '') + (user.full_name?.split(' ')[1]?.[0] || '')).toUpperCase()}</div>
      <div class="user-name" id="header-user-name">${sanitizeHtml(user.full_name || 'User')}</div>
    </div>
    <button class="header-dashboard-btn" onclick="window.location.href='/dashboard.html'">Dashboard</button>
    <button class="header-logout-btn" onclick="sessionStorage.clear();localStorage.removeItem('jetstark_user');window.location.href='/login.html'">Log out</button>
  `;
  headerInner.appendChild(panel);

  initNotifications(access);
}

let notificationCount = 0;

function initNotifications(token) {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = window.location.host;
  let wsUrl;
  if (window.location.port === '5500' || window.location.hostname === '127.0.0.1') {
    wsUrl = `ws://localhost:8000/ws/notifications?token=${token}`;
  } else {
    wsUrl = `${wsProtocol}//${wsHost}/ws/notifications?token=${token}`;
  }

  let ws;
  try {
    ws = new WebSocket(wsUrl);
  } catch { return; }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'pong') return;
      addNotification(data);
    } catch {}
  };

  ws.onclose = () => {
    setTimeout(() => initNotifications(token), 5000);
  };

  const pingInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send('ping');
    } else {
      clearInterval(pingInterval);
    }
  }, 30000);

  const bell = document.getElementById('notification-bell');
  if (bell) {
    bell.addEventListener('click', (e) => {
      e.stopPropagation();
      const dropdown = document.getElementById('notification-dropdown');
      dropdown.hidden = !dropdown.hidden;
    });
    document.addEventListener('click', () => {
      const dropdown = document.getElementById('notification-dropdown');
      if (dropdown) dropdown.hidden = true;
    });
  }
}

function addNotification(data) {
  notificationCount++;
  const badge = document.getElementById('notification-badge');
  if (badge) {
    badge.textContent = notificationCount;
    badge.hidden = false;
  }

  const list = document.getElementById('notification-list');
  if (!list) return;

  const empty = list.querySelector('.notification-empty');
  if (empty) empty.remove();

  const item = document.createElement('div');
  item.className = 'notification-item';
  item.innerHTML = `<p>${sanitizeHtml(data.message || 'New notification')}</p><small>${new Date().toLocaleTimeString()}</small>`;
  list.prepend(item);
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
