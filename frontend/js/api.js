const API_BASE = (window.location.port === '5500' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8000/api'
  : '/api';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

function sanitize(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, (match) => {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };
    return map[match];
  });
}

function getTokens() {
  return {
    access: sessionStorage.getItem('jetstark_access_token'),
    refresh: sessionStorage.getItem('jetstark_refresh_token'),
  };
}

function setTokens(access, refresh) {
  sessionStorage.setItem('jetstark_access_token', access);
  sessionStorage.setItem('jetstark_refresh_token', refresh);
}

function clearTokens() {
  sessionStorage.removeItem('jetstark_access_token');
  sessionStorage.removeItem('jetstark_refresh_token');
  localStorage.removeItem('jetstark_user');
}

async function refreshAccessToken() {
  const { refresh } = getTokens();
  if (!refresh) throw new ApiError('No refresh token', 401);

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  if (!res.ok) {
    clearTokens();
    throw new ApiError('Session expired', 401);
  }

  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

async function apiRequest(endpoint, options = {}) {
  const { method = 'GET', body, authenticated = true, retry = true, params } = options;

  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') searchParams.set(k, v);
    });
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const headers = { 'Content-Type': 'application/json' };

  if (authenticated) {
    const { access } = getTokens();
    if (access) headers['Authorization'] = `Bearer ${access}`;
  }

  try {
    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401 && authenticated && retry) {
      await refreshAccessToken();
      return apiRequest(endpoint, { ...options, retry: false });
    }

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new ApiError(data.detail || `HTTP ${res.status}`, res.status, data);
    }

    if (res.status === 204) return null;
    return await res.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error. Check your connection.', 0);
  }
}

// Config API (public)
export const config = {
  get: () => apiRequest('/config', { authenticated: false }),
};

// Payments API
export const payments = {
  initialize: (orderId) => apiRequest(`/payments/initialize?order_id=${orderId}`, { method: 'POST' }),
  verify: (reference) => apiRequest(`/payments/verify/${reference}`, { method: 'POST' }),
};

// Auth API
export const auth = {
  signup: (data) => apiRequest('/auth/signup', { method: 'POST', body: data, authenticated: false }),
  login: (data) => apiRequest('/auth/login', { method: 'POST', body: data, authenticated: false }),
  refresh: () => apiRequest('/auth/refresh', { authenticated: false }),
  me: () => apiRequest('/auth/me'),
  changePassword: (data) => apiRequest('/auth/change-password', { method: 'PUT', body: data }),
  forgotPassword: (email) => apiRequest('/auth/forgot-password', { method: 'POST', body: { email }, authenticated: false }),
  resetPassword: (data) => apiRequest('/auth/reset-password', { method: 'POST', body: data, authenticated: false }),
};

// Products API
export const products = {
  list: (params) => apiRequest('/products', { params }),
  get: (id) => apiRequest(`/products/${id}`),
  create: (data) => apiRequest('/products', { method: 'POST', body: data }),
  update: (id, data) => apiRequest(`/products/${id}`, { method: 'PUT', body: data }),
  delete: (id) => apiRequest(`/products/${id}`, { method: 'DELETE' }),
  getVendorProducts: () => apiRequest('/products/my-products'),
  categories: () => apiRequest('/products/categories'),
  uploadImage: (file) => {
    const { access } = getTokens();
    const form = new FormData();
    form.append('file', file);
    return fetch(`${API_BASE}/products/upload-image`, {
      method: 'POST',
      headers: access ? { Authorization: `Bearer ${access}` } : {},
      body: form,
    }).then(async res => {
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new ApiError(d.detail || `HTTP ${res.status}`, res.status); }
      return res.json();
    });
  },
};

// Orders API
export const orders = {
  create: (data) => apiRequest('/orders', { method: 'POST', body: data }),
  list: () => apiRequest('/orders'),
  get: (id) => apiRequest(`/orders/${id}`),
  vendorEarnings: () => apiRequest('/orders/vendor/earnings'),
  updateStatus: (orderId, status) => apiRequest(`/orders/${orderId}/status`, { method: 'PUT', body: { status } }),
};

// Admin API
export const admin = {
  listUsers: () => apiRequest('/users/admin/users'),
  suspendUser: (userId) => apiRequest(`/users/admin/users/${userId}/suspend`, { method: 'POST' }),
  listAllProducts: () => apiRequest('/products/admin/all'),
  listPendingProducts: () => apiRequest('/products/admin/pending'),
  approveProduct: (productId) => apiRequest(`/products/admin/${productId}/approve`, { method: 'POST' }),
  rejectProduct: (productId) => apiRequest(`/products/admin/${productId}/reject`, { method: 'POST' }),
  listAllOrders: () => apiRequest('/orders/admin/all'),
  stats: () => apiRequest('/admin/stats'),
};

// Affiliate API
export const affiliate = {
  createLink: (data) => apiRequest('/affiliate/links', { method: 'POST', body: data }),
  listLinks: () => apiRequest('/affiliate/links'),
  deleteLink: (id) => apiRequest(`/affiliate/links/${id}`, { method: 'DELETE' }),
  getAnalytics: () => apiRequest('/affiliate/analytics'),
  trackClick: (linkCode) => apiRequest(`/affiliate/track-click?link_code=${linkCode}`, { method: 'POST', authenticated: false }),
};

// Payouts API
export const payouts = {
  request: (data) => apiRequest('/payouts', { method: 'POST', body: data }),
  list: () => apiRequest('/payouts'),
  getBalance: () => apiRequest('/payouts/balance'),
};

// Reviews API
export const reviews = {
  create: (productId, data) => apiRequest(`/reviews/products/${productId}`, { method: 'POST', body: data }),
  getByProduct: (productId) => apiRequest(`/reviews/products/${productId}`),
};

// User API
export const users = {
  updateProfile: (data) => apiRequest('/users/profile', { method: 'PUT', body: data }),
  deleteAccount: () => apiRequest('/users/account', { method: 'DELETE' }),
};

// Cart API
export const cart = {
  get: () => apiRequest('/cart'),
  add: (data) => apiRequest('/cart/items', { method: 'POST', body: data }),
  update: (itemId, data) => apiRequest(`/cart/items/${itemId}`, { method: 'PUT', body: data }),
  remove: (itemId) => apiRequest(`/cart/items/${itemId}`, { method: 'DELETE' }),
  clear: () => apiRequest('/cart', { method: 'DELETE' }),
};

// Wishlist API
export const wishlist = {
  get: () => apiRequest('/wishlist'),
  add: (productId) => apiRequest(`/wishlist/products/${productId}`, { method: 'POST' }),
  remove: (productId) => apiRequest(`/wishlist/products/${productId}`, { method: 'DELETE' }),
};

// Sanitize helper (exported for use in views)
export const sanitizeHtml = sanitize;

// Token helpers (exported for use in auth module)
export { getTokens, setTokens, clearTokens };

// Toast notification system
export function showToast(message, type = 'info', duration = 4000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.addEventListener('click', () => {
    toast.classList.add('toast-removing');
    setTimeout(() => toast.remove(), 200);
  });
  container.appendChild(toast);

  setTimeout(() => {
    if (toast.isConnected) {
      toast.classList.add('toast-removing');
      setTimeout(() => toast.remove(), 200);
    }
  }, duration);
}
