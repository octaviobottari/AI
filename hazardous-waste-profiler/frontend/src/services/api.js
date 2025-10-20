// frontend/src/services/api.js
const API_BASE_URL = 'http://localhost:8000';

export const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(url, config);
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

export const getProfiles = () => apiRequest('/profiles');
export const getProfile = (id) => apiRequest(`/profiles/${id}`);
export const createProfile = (profileData) => 
  apiRequest('/profiles', { method: 'POST', body: profileData });
export const validateProfile = (id) => 
  apiRequest(`/profiles/${id}/validate`, { method: 'POST' });
export const submitFeedback = (profileId, recommendationId, feedback) =>
  apiRequest(`/profiles/${profileId}/recommendations/${recommendationId}/feedback`, {
    method: 'POST',
    body: { feedback }
  });