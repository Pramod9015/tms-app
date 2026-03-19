import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const axiosClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT to every request
axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refreshToken });
          localStorage.setItem('access_token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
          original.headers.Authorization = `Bearer ${res.data.access_token}`;
          return axiosClient(original);
        } catch (_) {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;

// ── API helpers ──────────────────────────────────────────────────────────────
export const authAPI = {
  login: (data) => axiosClient.post('/auth/login', data),
  register: (data) => axiosClient.post('/auth/register', data),
  logout: () => axiosClient.post('/auth/logout'),
};

export const dashboardAPI = {
  getSummary: () => axiosClient.get('/dashboard/summary'),
  getDailyChart: (days = 30) => axiosClient.get(`/dashboard/daily-chart?days=${days}`),
  getAppUsage: () => axiosClient.get('/dashboard/app-usage'),
  getBankWise: () => axiosClient.get('/dashboard/bank-wise'),
  getMonthlyTrend: () => axiosClient.get('/dashboard/monthly-trend'),
  getRecentTransactions: (limit = 10) => axiosClient.get(`/dashboard/recent-transactions?limit=${limit}`),
};

export const transactionsAPI = {
  list: (params) => axiosClient.get('/transactions', { params }),
  create: (data) => axiosClient.post('/transactions', data),
  update: (id, data) => axiosClient.put(`/transactions/${id}`, data),
  delete: (id) => axiosClient.delete(`/transactions/${id}`),
};

export const banksAPI = {
  list: () => axiosClient.get('/banks'),
  create: (data) => axiosClient.post('/banks', data),
  update: (id, data) => axiosClient.put(`/banks/${id}`, data),
  delete: (id) => axiosClient.delete(`/banks/${id}`),
};

export const beneficiariesAPI = {
  list: () => axiosClient.get('/beneficiaries'),
  create: (data) => axiosClient.post('/beneficiaries', data),
  delete: (id) => axiosClient.delete(`/beneficiaries/${id}`),
  byMobile: (mobile) => axiosClient.get('/beneficiaries/by-mobile', { params: { mobile } }),
};

export const reportsAPI = {
  exportCsv: (params) => axiosClient.get('/reports/export/csv', { params, responseType: 'blob' }),
  exportExcel: (params) => axiosClient.get('/reports/export/excel', { params, responseType: 'blob' }),
  exportPdf: (params) => axiosClient.get('/reports/export/pdf', { params, responseType: 'blob' }),
};

export const usersAPI = {
  list: () => axiosClient.get('/users'),
  update: (id, data) => axiosClient.put(`/users/${id}`, data),
  delete: (id) => axiosClient.delete(`/users/${id}`),
};

export const auditAPI = {
  list: () => axiosClient.get('/audit'),
};
