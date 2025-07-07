// api_endpoints.js
// Centralized API endpoints and dynamic fetch utility for Your App React frontend

// --- API Endpoints ---
export const API_BASE = '/api';

// Store
export const STORE = `${API_BASE}/store`;
export const PRODUCTS = `${STORE}/products/`;
export const CATEGORIES = `${STORE}/categories/`;
export const SIZES = `${STORE}/sizes/`;
export const PRODUCT_IMAGES = `${STORE}/product-images/`;
export const COUPONS = `${STORE}/coupons/`;
export const REVIEWS = `${STORE}/reviews/`;

// Users
export const USERS = `${API_BASE}/users`;
export const REGISTER = `${USERS}/register/`;
export const LOGIN = `${USERS}/login/`;
export const LOGOUT = `${USERS}/logout/`;
export const PROFILE = `${USERS}/profile/`;
export const PROFILE_DETAILS = `${USERS}/profile/details/`;
export const PROFILE_UPDATE = `${USERS}/profile/update/`;
export const TOKEN = `${API_BASE}/token/`;
export const TOKEN_REFRESH = `${API_BASE}/token/refresh/`;

// Orders
export const ORDERS = `${API_BASE}/orders/orders/`;
export const ORDER_ITEMS = `${API_BASE}/orders/order-items/`;
export const CARTS = `${API_BASE}/orders/carts/`;
export const CART_ITEMS = `${API_BASE}/orders/cart-items/`;
export const CHECKOUT = `${API_BASE}/orders/checkout/`;
export const STRIPE_WEBHOOK = `${API_BASE}/orders/webhook/stripe/`;
export const APPLY_COUPON = `${API_BASE}/orders/apply-coupon/`;

// --- Dynamic Fetch Utility ---
/**
 * Dynamic API fetch with JWT authentication.
 * @param {string} url - Endpoint URL (absolute or relative).
 * @param {object} options - Fetch options (method, body, headers, etc).
 * @param {string} [token] - JWT access token (optional, will add Authorization header if provided).
 * @returns {Promise<Response>} - Fetch response promise.
 */
export async function apiFetch(url, options = {}, token = null) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const fetchOptions = {
    ...options,
    headers,
  };
  // If body is an object, stringify it
  if (fetchOptions.body && typeof fetchOptions.body === 'object' && !(fetchOptions.body instanceof FormData)) {
    fetchOptions.body = JSON.stringify(fetchOptions.body);
  }
  const response = await fetch(url, fetchOptions);
  // Optionally handle auto-refresh of token here if needed
  return response;
}

// Example usage in React:
// import { PRODUCTS, apiFetch } from './api_endpoints';
// const res = await apiFetch(PRODUCTS, { method: 'GET' }, accessToken); 