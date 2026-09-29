import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchAPI = {
  createSearch: async (searchData) => {
    const response = await api.post('/search/search', searchData);
    return response.data;
  },
  
  getSearchStatus: async (searchId) => {
    const response = await api.get(`/search/search/${searchId}`);
    return response.data;
  },
  
  listSearches: async (limit = 20) => {
    const response = await api.get(`/search/searches?limit=${limit}`);
    return response.data;
  },
};

export const nlSearchAPI = {
  // Plain-language request -> structured criteria (local AI model; can take 5-30 s)
  parse: async (text) => {
    const response = await api.post('/nl-search/parse', { text }, { timeout: 120000 });
    return response.data;
  },

  status: async () => {
    const response = await api.get('/nl-search/status');
    return response.data;
  },
};

export const dealsAPI = {
  getDeals: async (params = {}) => {
    const queryParams = new URLSearchParams(params).toString();
    const response = await api.get(`/deals/deals?${queryParams}`);
    return response.data;
  },
  
  getDealsBySearch: async (searchId) => {
    const response = await api.get(`/deals/deals/search/${searchId}`);
    return response.data;
  },
  
  getDeal: async (dealId) => {
    const response = await api.get(`/deals/deals/${dealId}`);
    return response.data;
  },
};

export const exportAPI = {
  exportToExcel: async (searchId) => {
    const response = await api.get(`/export/excel/${searchId}`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `travel_deals_${searchId}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
  
  exportToCSV: async (searchId) => {
    const response = await api.get(`/export/csv/${searchId}`, {
      responseType: 'blob',
    });
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `travel_deals_${searchId}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default api;
