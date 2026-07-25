const API_BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => request('/health'),

  listProjects: () => request('/projects'),

  createProject: (data) =>
    request('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getProject: (name) => request(`/projects/${encodeURIComponent(name)}`),

  deleteProject: (name) =>
    request(`/projects/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  setOverview: (name, overview) =>
    request(`/projects/${encodeURIComponent(name)}/overview`, {
      method: 'POST',
      body: JSON.stringify({ overview }),
    }),

  addChapter: (name, data) =>
    request(`/projects/${encodeURIComponent(name)}/chapters`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateChapter: (name, chapterId, data) =>
    request(`/projects/${encodeURIComponent(name)}/chapters/${encodeURIComponent(chapterId)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  addCharacter: (name, data) =>
    request(`/projects/${encodeURIComponent(name)}/characters`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  addLocation: (name, data) =>
    request(`/projects/${encodeURIComponent(name)}/locations`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  chat: (message, projectName, messages) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, project_name: projectName, messages }),
    }),
}
