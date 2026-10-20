import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const analyzeQuery = async (query) => {
  const response = await api.post('/query/analyze', { query });
  return response.data;
};

export const explainQuery = async (query) => {
  const response = await api.post('/query/explain', { query });
  return response.data;
};

export const executeQuery = async (query) => {
  const response = await api.post('/query/analyze-execution', { query });
  return response.data;
};

export const getHistory = async () => {
  const response = await api.get('/query/history');
  return response.data;
};

export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

export const getDashboardAnalytics = async () => {
  const response = await api.get('/dashboard/analytics');
  return response.data;
};

export const getModelMetrics = async () => {
  const response = await api.get('/model/metrics');
  return response.data;
};

export const retrainFromHistory = async () => {
  const response = await api.post('/dashboard/retrain-from-history');
  return response.data;
};

export const simulateIndex = async (query, indexSql) => {
  const response = await api.post('/query/simulate-index', { 
    query, 
    index_sql: indexSql 
  });
  return response.data;
};

export const rewriteQuery = async (query) => {
  const response = await api.post('/query/rewrite', { query });
  return response.data;
};

export default api;
