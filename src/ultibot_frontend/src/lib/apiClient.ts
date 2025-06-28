import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// You can add interceptors for handling tokens or errors globally
apiClient.interceptors.response.use(
  response => response,
  error => {
    // Handle errors
    console.error('API call error:', error);
    return Promise.reject(error);
  }
);

export default apiClient;
