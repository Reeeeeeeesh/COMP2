import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
  timeout: 10000,
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
    if (error.message === 'Network Error') {
      console.log('Connection to the server failed. Please check if the backend server is running.');
    }
    return Promise.reject(error);
  }
);

export default api;
