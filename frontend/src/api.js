const API_BASE = import.meta.env.VITE_API_BASE || '/api'

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

  deleteCharacter: (name, characterId) =>
    request(`/projects/${encodeURIComponent(name)}/characters/${encodeURIComponent(characterId)}`, {
      method: 'DELETE',
    }),

  generateCharacterPortrait: (name, characterId, params) =>
    request(`/projects/${encodeURIComponent(name)}/characters/${encodeURIComponent(characterId)}/portrait`, {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  addLocation: (name, data) =>
    request(`/projects/${encodeURIComponent(name)}/locations`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deleteLocation: (name, locationId) =>
    request(`/projects/${encodeURIComponent(name)}/locations/${encodeURIComponent(locationId)}`, {
      method: 'DELETE',
    }),

  addOutlinePoint: (name, point) =>
    request(`/projects/${encodeURIComponent(name)}/outline`, {
      method: 'POST',
      body: JSON.stringify({ point }),
    }),

  deleteOutlinePoint: (name, index) =>
    request(`/projects/${encodeURIComponent(name)}/outline/${index}`, {
      method: 'DELETE',
    }),

  addWorldRule: (name, rule) =>
    request(`/projects/${encodeURIComponent(name)}/rules`, {
      method: 'POST',
      body: JSON.stringify({ rule }),
    }),

  deleteWorldRule: (name, index) =>
    request(`/projects/${encodeURIComponent(name)}/rules/${index}`, {
      method: 'DELETE',
    }),

  addTimelineEntry: (name, data) =>
    request(`/projects/${encodeURIComponent(name)}/timeline`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deleteTimelineEntry: (name, entryId) =>
    request(`/projects/${encodeURIComponent(name)}/timeline/${encodeURIComponent(entryId)}`, {
      method: 'DELETE',
    }),

  chat: (message, projectName, messages) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, project_name: projectName, messages }),
    }),

  listComfyModels: () =>
    request('/comfyui/models'),

  generateImage: (name, params) =>
    request(`/projects/${encodeURIComponent(name)}/generate`, {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  exportProject: (name, format) =>
    `${API_BASE}/projects/${encodeURIComponent(name)}/export/${format}`,
}
