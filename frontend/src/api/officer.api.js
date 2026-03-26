import client from './client';

export const officerApi = {
  getQueue: (params) => client.get('/officer/queue', { params }),
  getApplications: (params) => client.get('/officer/applications', { params }),
  getApplication: (id) => client.get(`/officer/applications/${id}`),
  decide: (id, data) => client.post(`/officer/applications/${id}/decide`, data),
  getStats: () => client.get('/officer/stats'),
};