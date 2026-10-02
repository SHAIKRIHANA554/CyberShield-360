/**
 * CyberShield 360 - API Helper Functions
 */

function normalizeApiEndpoint(endpoint) {
  return endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
}

async function apiRequest(endpoint, options = {}) {
  const normalizedEndpoint = normalizeApiEndpoint(endpoint);
  const url = `${API_BASE}${normalizedEndpoint}`;
  const token = localStorage.getItem('access_token');
  const isFormData = options.body instanceof FormData;

  const config = {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.headers || {})
    }
  };

  if (token && !options.skipAuth) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  if (!isFormData && !config.headers['Content-Type']) {
    config.headers['Content-Type'] = 'application/json';
  }

  if (options.body && typeof options.body === 'object' && !isFormData) {
    config.body = JSON.stringify(options.body);
  }

  try {
    const response = await fetch(url, config);
    const text = await response.text();
    let payload = {};

    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (error) {
        payload = { success: false, message: text || 'Unexpected server response.' };
      }
    }

    if (response.status === 401 && !options._retry) {
      const refreshed = await refreshToken();
      if (refreshed) {
        return apiRequest(endpoint, { ...options, _retry: true });
      }
      logout();
      return { success: false, message: 'Session expired. Please login again.' };
    }

    if (response.status === 403) {
      return { success: false, message: payload.message || 'Access forbidden.' };
    }

    if (response.status === 404) {
      return { success: false, message: payload.message || 'The requested resource was not found.' };
    }

    if (response.status >= 500) {
      return { success: false, message: payload.message || 'Server error. Please try again later.' };
    }

    if (payload && typeof payload === 'object' && 'success' in payload) {
      return payload;
    }

    return { success: true, data: payload };
  } catch (error) {
    console.error('API Error:', error);
    return {
      success: false,
      message: 'Backend unavailable. Please ensure the Flask service is running on 127.0.0.1:5000.'
    };
  }
}

async function refreshToken() {
  const refreshTokenValue = localStorage.getItem('refresh_token');
  if (!refreshTokenValue) return false;

  try {
    const response = await fetch(`${API_BASE}${ENDPOINTS.REFRESH}`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${refreshTokenValue}`
      }
    });

    const text = await response.text();
    let payload = {};
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (error) {
        payload = { success: false, message: text };
      }
    }

    if (response.ok && payload.success && payload.data && payload.data.access_token) {
      localStorage.setItem('access_token', payload.data.access_token);
      return true;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }

  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  return false;
}

async function apiGet(endpoint) {
  return apiRequest(endpoint, { method: 'GET' });
}

async function apiPost(endpoint, body) {
  return apiRequest(endpoint, { method: 'POST', body });
}

async function apiPut(endpoint, body) {
  return apiRequest(endpoint, { method: 'PUT', body });
}

async function apiDelete(endpoint) {
  return apiRequest(endpoint, { method: 'DELETE' });
}

async function apiUpload(endpoint, formData) {
  return apiRequest(endpoint, { method: 'POST', body: formData });
}

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}
