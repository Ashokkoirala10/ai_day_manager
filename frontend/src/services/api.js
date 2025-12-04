import axios from 'axios';

const API_URL = 'http://localhost:8000/';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } catch (err) {
          localStorage.clear();
          window.location.href = '/login';
          return Promise.reject(err);
        }
      } else {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  logout: (refreshToken) => api.post('/auth/logout/', { refresh: refreshToken }),
  getProfile: () => api.get('/auth/profile/'),
};

// Routine API
export const routineAPI = {
  getAll: () => api.get('/routines/'),
  getOne: (id) => api.get(`/routines/${id}/`),
  create: (data) => api.post('/routines/', data),
  update: (id, data) => api.put(`/routines/${id}/`, data),
  delete: (id) => api.delete(`/routines/${id}/`),
};

// Scheduler API
export const schedulerAPI = {
  getStatus: () => api.get('/scheduler/status/'),
  start: () => api.post('/scheduler/start/'),
  stop: () => api.post('/scheduler/stop/'),
  toggle: () => api.post('/scheduler/toggle/'),
};

export const chatAPI = {
  sendMessage: (message) => api.post('/chat/', { message }),
};
export default api;