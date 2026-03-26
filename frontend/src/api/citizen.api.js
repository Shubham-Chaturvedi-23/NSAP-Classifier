import client from './client';

export const citizenApi = {
  apply: (data) => client.post('/citizen/apply', data),
  updateApplication: (id, data) => client.put(`/citizen/applications/${id}`, data),
  getApplications: (params) => client.get('/citizen/applications', { params }),
  getApplication: (id) => client.get(`/citizen/applications/${id}`),
  uploadDocument: (formData) =>
    client.post('/citizen/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  verifyDocuments: (data) => client.post('/citizen/documents/verify', data),
  getNotifications: (params) => client.get('/citizen/notifications', { params }),
  markAllRead: () => client.put('/citizen/notifications/read'),
  markRead: (id) => client.put(`/citizen/notifications/${id}/read`),
};