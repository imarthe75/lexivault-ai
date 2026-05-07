import axios from 'axios';

// Base configuration for LexiVault API
const instance = axios.create({
  baseURL: '/lexivault/api',
});

// Attach OIDC token from session storage to every request
instance.interceptors.request.use((config) => {
  try {
    // find OIDC user in session storage
    const oidcKey = Object.keys(sessionStorage).find(key => key.startsWith('oidc.user:'));
    if (oidcKey) {
      const oidcUser = JSON.parse(sessionStorage.getItem(oidcKey));
      if (oidcUser && oidcUser.access_token) {
        config.headers.Authorization = `Bearer ${oidcUser.access_token}`;
      }
    }
  } catch (e) {
    console.error("Error attaching OIDC token to request", e);
  }
  return config;
}, (error) => Promise.reject(error));

// Global response handler
instance.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err && err.response && err.response.status === 401) {
      // If unauthorized, the OIDC context will eventually handle it, 
      // but we can trigger a reload to force re-auth if needed.
      console.warn("Unauthorized API call detected.");
    }
    return Promise.reject(err);
  }
);

export default instance;
