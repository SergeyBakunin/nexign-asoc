import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

function authHeaders() {
  const token = localStorage.getItem('asoc_token') || ''
  return { 'x-api-token': token }
}

// Stats
export const getStats = (params) => api.get('/stats', { params })

// Projects
export const getProjects = () => api.get('/projects')
export const createProject = (data) => api.post('/projects', data, { headers: authHeaders() })
export const deleteProject = (id) => api.delete(`/projects/${id}`, { headers: authHeaders() })

// Scan Classes
export const getScanClasses = (projectId) => api.get(`/projects/${projectId}/scan-classes`)
export const createScanClass = (projectId, data) =>
  api.post(`/projects/${projectId}/scan-classes`, data, { headers: authHeaders() })
export const deleteScanClass = (projectId, scId) =>
  api.delete(`/projects/${projectId}/scan-classes/${scId}`, { headers: authHeaders() })

// Scans (history per scan class)
export const getScans = (scanClassId) => api.get(`/scan-classes/${scanClassId}/scans`)
export const deleteScan = (scanId) =>
  api.delete(`/scans/${scanId}`, { headers: authHeaders() })

// Findings
export const getFindings = (params) => api.get('/findings', { params })
export const getComponents = (params) => api.get('/findings/components', { params })
export const getTools = (params) => api.get('/findings/tools', { params })
export const getFinding = (id) => api.get(`/findings/${id}`)
export const updateFindingStatus = (id, status) =>
  api.put(`/findings/${id}/status`, { status }, { headers: authHeaders() })
export const exportFindings = (params) => {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v))
  ).toString()
  return `/api/v1/findings/export${qs ? '?' + qs : ''}`
}

// Dependencies
export const getDependencies = (params) => api.get('/dependencies', { params })
export const getDependenciesCount = (params) => api.get('/dependencies/count', { params })

// Import — Content-Type не выставляем вручную, axios сам добавит boundary
export const manualImport = (formData) =>
  api.post('/import', formData, { headers: authHeaders() })
