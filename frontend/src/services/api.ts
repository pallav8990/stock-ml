import axios from 'axios';
import { StockPrediction, StockAccuracy, ApiResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token if available
apiClient.interceptors.request.use(
  (config) => {
    // Temporarily disable auth for testing - uncomment below for production
    /*
    const user = localStorage.getItem('stockml_user');
    if (user) {
      try {
        const userData = JSON.parse(user);
        config.headers.Authorization = `Bearer ${userData.sub}`;
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
    */
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login or refresh token
      localStorage.removeItem('stockml_user');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export const stockApi = {
  // Get today's predictions
  getPredictionsToday: async (): Promise<StockPrediction[]> => {
    try {
      const response = await apiClient.get('/predict_today');
      return response.data;
    } catch (error) {
      console.error('Error fetching predictions:', error);
      throw error;
    }
  },

  // Get accuracy metrics by stock
  getAccuracyByStock: async (window?: number): Promise<StockAccuracy[]> => {
    try {
      const params = window ? { window } : {};
      const response = await apiClient.get('/accuracy_by_stock', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching accuracy data:', error);
      throw error;
    }
  },

  // Get gap explanations
  getExplanations: async (): Promise<any[]> => {
    try {
      const response = await apiClient.get('/explain_gap');
      return response.data;
    } catch (error) {
      console.error('Error fetching explanations:', error);
      throw error;
    }
  },

  // Health check
  getHealth: async (): Promise<any> => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  },

  // Get API root info
  getApiInfo: async (): Promise<any> => {
    try {
      const response = await apiClient.get('/');
      return response.data;
    } catch (error) {
      console.error('Error fetching API info:', error);
      throw error;
    }
  }
};

export default apiClient;