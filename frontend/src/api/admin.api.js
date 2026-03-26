import client from './client';

export const adminApi = {
  getStats: () => client.get('/admin/stats'),
  getApplications: (params) => client.get('/admin/applications', { params }),
  getModelMetrics: () => client.get('/admin/model/metrics'),
  getFairnessReport: () => client.get('/admin/model/fairness'),
  getConfusionMatrix: () => `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/admin/model/confusion`,
  getShapSummary: () => `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/admin/model/shap`,
  getConfusionMatrixBlob: () => client.get('/admin/model/confusion', { responseType: 'blob' }),
  getShapSummaryBlob: () => client.get('/admin/model/shap', { responseType: 'blob' }),
  getOfficerActivity: () => client.get('/admin/officers/activity'),
  getUsers: (params) => client.get('/admin/users', { params }),
};