import { useState, useEffect, useRef } from 'react'
import { api } from './api'
import './App.css'

function App() {
  const [projects, setProjects] = useState([])
  const [currentProject, setCurrentProject] = useState(null)
  const [bible, setBible] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [showExport, setShowExport] = useState(false)
  const [newProject, setNewProject] = useState({ name: '', title: '', genre: '', tone: '' })
  const [chat, setChat] = useState({ messages: [], input: '' })
  const [chatLoading, setChatLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('chat')
  const [newChar, setNewChar] = useState({ name: '', description: '', role: '' })
  const [newLoc, setNewLoc] = useState({ name: '', description: '' })
  const [newChapter, setNewChapter] = useState({ title: '', content: '' })
  const [overview, setOverview] = useState('')
  const chatEnd = useRef(null)

  // Art generation state
  const [models, setModels] = useState([])
  const [artForm, setArtForm] = useState({
    prompt: '',
    negative_prompt: '',
    model: 'dreamShaper.safetensors',
    width: 1024,
    height: 1024,
    steps: 25,
    cfg: 7.0,
  })
  const [generating, setGenerating] = useState(false)
  const [artOutput, setArtOutput] = useState(null)
  const [artFullscreen, setArtFullscreen] = useState(null)

  useEffect(() => {
    api.listProjects().then(d => setProjects(d.projects)).catch(console.error)
  }, [])

  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: 'smooth' }) }, [chat.messages])

  const loadProject = async (name) => {
    setCurrentProject(name)
    const d = await api.getProject(name)
    setBible(d.bible)
    setOverview(d.bible.overview || '')
    setChat({ messages: [{ role: 'system', content: `Loaded: ${d.bible.title} (${d.bible.genre})` }], input: '' })
    setActiveTab('chat')
    setArtOutput(null)
    // Fetch available ComfyUI models
    api.listComfyModels?.().then(r => setModels(r.models || [])).catch(() => {})
  }

  const createProject = async (e) => {
    e.preventDefault()
    await api.createProject(newProject)
    setShowCreate(false)
    setNewProject({ name: '', title: '', genre: '', tone: '' })
    const d = await api.listProjects()
    setProjects(d.projects)
  }

  const deleteProject = async (name) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return
    await api.deleteProject(name)
    if (currentProject === name) { setCurrentProject(null); setBible(null) }
    const d = await api.listProjects()
    setProjects(d.projects)
  }

  const saveOverview = async () => {
    const d = await api.setOverview(currentProject, overview)
    setBible(d.bible)
  }

  const addChar = async (e) => {
    e.preventDefault()
    const d = await api.addCharacter(currentProject, newChar)
    setBible(d.bible)
    setNewChar({ name: '', description: '', role: '' })
  }

  const addLoc = async (e) => {
    e.preventDefault()
    const d = await api.addLocation(currentProject, newLoc)
    setBible(d.bible)
    setNewLoc({ name: '', description: '' })
  }

  const addChapter = async (e) => {
    e.preventDefault()
    const d = await api.addChapter(currentProject, newChapter)
    setBible(d.bible)
    setNewChapter({ title: '', content: '' })
  }

  const sendChat = async (e) => {
    e.preventDefault()
    if (!chat.input.trim() || chatLoading) return
    const userMsg = { role: 'user', content: chat.input }
    const history = chat.messages.filter(m => m.role !== 'system')
    setChat(c => ({ ...c, messages: [...c.messages, userMsg], input: '' }))
    setChatLoading(true)
    try {
      const d = await api.chat(chat.input, currentProject || '__none__', history)
      setChat(c => ({ ...c, messages: [...c.messages, { role: 'assistant', content: d.response }] }))
    } catch (err) {
      setChat(c => ({ ...c, messages: [...c.messages, { role: 'assistant', content: `Error: ${err.message}` }] }))
    }
    setChatLoading(false)
  }

  const generateImage = async (e) => {
    e.preventDefault()
    if (!artForm.prompt.trim() || generating) return
    setGenerating(true)
    setArtOutput(null)
    try {
      const d = await api.generateImage(currentProject, artForm)
      setArtOutput(d.result)
      // Refresh Bible to get updated generated_images
      const proj = await api.getProject(currentProject)
      setBible(proj.bible)
    } catch (err) {
      setArtOutput({ error: err.message })
    }
    setGenerating(false)
  }

  // Build image URL helper
  const imgUrl = (filename) => {
    const base = import.meta.env.VITE_API_BASE || '/api'
    return `${base}/projects/${currentProject}/images/${filename}`
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>AI Studio</h1>
          <span className="version">v0.1.0</span>
        </div>
        <nav>
          <h3>Projects</h3>
          <ul className="project-list">
            {projects.map(p => (
              <li key={p.name} className={currentProject === p.name ? 'active' : ''}>
                <button onClick={() => loadProject(p.name)} className="project-btn">
                  <span className="project-title">{p.title || p.name}</span>
                  {p.genre && <span className="project-genre">{p.genre}</span>}
                </button>
                <button onClick={() => deleteProject(p.name)} className="delete-btn" title="Delete">✕</button>
              </li>
            ))}
          </ul>
          <button className="new-project-btn" onClick={() => setShowCreate(true)}>+ New Project</button>
        </nav>
        <div className="sidebar-footer">
          <a href="http://localhost:8800/docs" target="_blank" rel="noopener">API Docs</a>
        </div>
      </aside>

      <main className="main">
        {showCreate && (
          <div className="modal-overlay" onClick={() => setShowCreate(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Forge New Project</h2>
              <form onSubmit={createProject}>
                <input placeholder="Project name (no spaces)" value={newProject.name} onChange={e => setNewProject(p => ({ ...p, name: e.target.value }))} required />
                <input placeholder="Title" value={newProject.title} onChange={e => setNewProject(p => ({ ...p, title: e.target.value }))} required />
                <input placeholder="Genre (e.g. dark fantasy)" value={newProject.genre} onChange={e => setNewProject(p => ({ ...p, genre: e.target.value }))} required />
                <input placeholder="Tone (e.g. dramatic)" value={newProject.tone} onChange={e => setNewProject(p => ({ ...p, tone: e.target.value }))} />
                <div className="modal-actions">
                  <button type="submit" className="btn-primary">Create</button>
                  <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {!bible ? (
          <div className="empty-state">
            <h2>The Studio Awaits</h2>
            <p>Select a project from the sidebar or forge a new one.</p>
            {projects.length === 0 && (
              <button className="btn-primary" onClick={() => setShowCreate(true)}>Forge Your First Project</button>
            )}
          </div>
        ) : (
          <div className="project-view">
            <header className="project-header">
              <div>
                <h2>{bible.title}</h2>
                <p className="project-meta">{bible.genre}{bible.tone ? ` — ${bible.tone}` : ''}</p>
              </div>
              <div className="tab-bar">
                <button className={activeTab === 'chat' ? 'active' : ''} onClick={() => setActiveTab('chat')}>Director Chat</button>
                <button className={activeTab === 'bible' ? 'active' : ''} onClick={() => setActiveTab('bible')}>Bible</button>
                <button className={activeTab === 'chapters' ? 'active' : ''} onClick={() => setActiveTab('chapters')}>Chapters</button>
                <button className={activeTab === 'characters' ? 'active' : ''} onClick={() => setActiveTab('characters')}>Characters</button>
                <button className={activeTab === 'locations' ? 'active' : ''} onClick={() => setActiveTab('locations')}>Locations</button>
                <button className={activeTab === 'art' ? 'active' : ''} onClick={() => setActiveTab('art')}>Art</button>
                <div className="export-dropdown">
                  <button className="export-btn" onClick={() => setShowExport(!showExport)} title="Export">⬇ Export</button>
                  {showExport && (
                    <div className="export-menu">
                      <a href={api.exportProject(currentProject, 'markdown')} download onClick={() => setShowExport(false)}>📄 Markdown (.md)</a>
                      <a href={api.exportProject(currentProject, 'pdf')} download onClick={() => setShowExport(false)}>📕 PDF</a>
                      <a href={api.exportProject(currentProject, 'epub')} download onClick={() => setShowExport(false)}>📖 EPUB</a>
                    </div>
                  )}
                </div>
              </div>
            </header>

            {activeTab === 'chat' && (
              <div className="chat-panel">
                <div className="chat-messages">
                  {chat.messages.map((m, i) => (
                    <div key={i} className={`msg msg-${m.role}`}>
                      <strong>{m.role === 'user' ? 'You' : m.role === 'assistant' ? 'Director' : 'System'}:</strong>
                      <div className="msg-content">{m.content}</div>
                    </div>
                  ))}
                  {chatLoading && <div className="msg msg-assistant"><em>The Director is contemplating...</em></div>}
                  <div ref={chatEnd} />
                </div>
                <form onSubmit={sendChat} className="chat-input">
                  <input
                    value={chat.input}
                    onChange={e => setChat(c => ({ ...c, input: e.target.value }))}
                    placeholder="Speak to the Director..."
                    disabled={chatLoading}
                  />
                  <button type="submit" disabled={chatLoading}>Send</button>
                </form>
              </div>
            )}

            {activeTab === 'bible' && (
              <div className="bible-panel">
                <section className="bible-section">
                  <h3>Overview</h3>
                  <textarea value={overview} onChange={e => setOverview(e.target.value)} rows={5} placeholder="Write your story overview..." />
                  <button onClick={saveOverview} className="btn-sm">Save Overview</button>
                </section>
                <section className="bible-section">
                  <h3>Story Outline</h3>
                  {bible.story_outline?.length > 0 ? (
                    <ul>{bible.story_outline.map((p, i) => <li key={i}>{p}</li>)}</ul>
                  ) : <p className="empty-hint">No outline yet.</p>}
                </section>
                <section className="bible-section">
                  <h3>World Rules</h3>
                  {bible.world_rules?.length > 0 ? (
                    <ul>{bible.world_rules.map((r, i) => <li key={i}>{r}</li>)}</ul>
                  ) : <p className="empty-hint">No world rules yet.</p>}
                </section>
              </div>
            )}

            {activeTab === 'chapters' && (
              <div className="chapters-panel">
                <form onSubmit={addChapter} className="inline-form">
                  <input placeholder="Chapter title" value={newChapter.title} onChange={e => setNewChapter(c => ({ ...c, title: e.target.value }))} required />
                  <textarea placeholder="Content (optional)" value={newChapter.content} onChange={e => setNewChapter(c => ({ ...c, content: e.target.value }))} rows={3} />
                  <button type="submit" className="btn-sm">Add Chapter</button>
                </form>
                {bible.chapters?.length > 0 ? (
                  <div className="chapter-list">
                    {bible.chapters.map((ch, i) => (
                      <div key={ch.id || i} className="chapter-card">
                        <h4>{ch.title || `Chapter ${i + 1}`}</h4>
                        {ch.content && <p>{ch.content.slice(0, 300)}{ch.content.length > 300 ? '...' : ''}</p>}
                        <span className="chapter-meta">Created: {ch.created?.slice(0, 10)}</span>
                      </div>
                    ))}
                  </div>
                ) : <p className="empty-hint">No chapters yet. Ask the Director to write one.</p>}
              </div>
            )}

            {activeTab === 'characters' && (
              <div className="characters-panel">
                <form onSubmit={addChar} className="inline-form">
                  <input placeholder="Character name" value={newChar.name} onChange={e => setNewChar(c => ({ ...c, name: e.target.value }))} required />
                  <input placeholder="Description" value={newChar.description} onChange={e => setNewChar(c => ({ ...c, description: e.target.value }))} />
                  <input placeholder="Role (protagonist, antagonist, etc.)" value={newChar.role} onChange={e => setNewChar(c => ({ ...c, role: e.target.value }))} />
                  <button type="submit" className="btn-sm">Add Character</button>
                </form>
                {bible.characters?.length > 0 ? (
                  <div className="card-grid">
                    {bible.characters.map((ch, i) => (
                      <div key={ch.id || i} className="card">
                        <h4>{ch.name}</h4>
                        {ch.role && <span className="badge">{ch.role}</span>}
                        {ch.description && <p>{ch.description}</p>}
                      </div>
                    ))}
                  </div>
                ) : <p className="empty-hint">No characters yet. Ask the Director to create some.</p>}
              </div>
            )}

            {activeTab === 'locations' && (
              <div className="locations-panel">
                <form onSubmit={addLoc} className="inline-form">
                  <input placeholder="Location name" value={newLoc.name} onChange={e => setNewLoc(c => ({ ...c, name: e.target.value }))} required />
                  <input placeholder="Description" value={newLoc.description} onChange={e => setNewLoc(c => ({ ...c, description: e.target.value }))} />
                  <button type="submit" className="btn-sm">Add Location</button>
                </form>
                {bible.locations?.length > 0 ? (
                  <div className="card-grid">
                    {bible.locations.map((loc, i) => (
                      <div key={loc.id || i} className="card">
                        <h4>{loc.name}</h4>
                        {loc.description && <p>{loc.description}</p>}
                      </div>
                    ))}
                  </div>
                ) : <p className="empty-hint">No locations yet.</p>}
              </div>
            )}

            {activeTab === 'art' && (
              <div className="art-panel">
                <form onSubmit={generateImage} className="inline-form">
                  <textarea
                    placeholder="Describe the image you want to create..."
                    value={artForm.prompt}
                    onChange={e => setArtForm(a => ({ ...a, prompt: e.target.value }))}
                    rows={3}
                    required
                  />
                  <input
                    placeholder="Negative prompt"
                    value={artForm.negative_prompt}
                    onChange={e => setArtForm(a => ({ ...a, negative_prompt: e.target.value }))}
                  />
                  <div className="art-controls">
                    <select
                      value={artForm.model}
                      onChange={e => setArtForm(a => ({ ...a, model: e.target.value }))}
                    >
                      {models.length > 0 ? models.map(m => (
                        <option key={m} value={m}>{m.replace('.safetensors', '')}</option>
                      )) : (
                        <option value="dreamShaper.safetensors">dreamShaper</option>
                      )}
                    </select>
                    <input
                      type="number" placeholder="Width" value={artForm.width}
                      onChange={e => setArtForm(a => ({ ...a, width: parseInt(e.target.value) || 1024 }))}
                      min={256} max={2048} step={64}
                      className="art-num"
                    />
                    <span className="art-x">x</span>
                    <input
                      type="number" placeholder="Height" value={artForm.height}
                      onChange={e => setArtForm(a => ({ ...a, height: parseInt(e.target.value) || 1024 }))}
                      min={256} max={2048} step={64}
                      className="art-num"
                    />
                    <input
                      type="number" placeholder="Steps" value={artForm.steps}
                      onChange={e => setArtForm(a => ({ ...a, steps: parseInt(e.target.value) || 25 }))}
                      min={1} max={100}
                      className="art-num-short"
                    />
                    <input
                      type="number" placeholder="CFG" value={artForm.cfg}
                      onChange={e => setArtForm(a => ({ ...a, cfg: parseFloat(e.target.value) || 7.0 }))}
                      min={1} max={30} step={0.5}
                      className="art-num-short"
                    />
                    <button type="submit" className="btn-primary" disabled={generating}>
                      {generating ? 'Generating...' : 'Generate'}
                    </button>
                  </div>
                </form>

                {artOutput && artOutput.error && (
                  <div className="art-error">
                    <strong>Error:</strong> {artOutput.error}
                  </div>
                )}

                {artOutput && artOutput.success && (
                  <div className="art-result">
                    <div className="art-image-wrapper">
                      <img
                        src={imgUrl(artOutput.filename)}
                        alt={artForm.prompt}
                        className="art-image"
                        onClick={() => setArtFullscreen(imgUrl(artOutput.filename))}
                      />
                      <div className="art-meta">
                        <span><strong>Seed:</strong> {artOutput.seed}</span>
                        <span><strong>Model:</strong> {artOutput.model}</span>
                        <span><strong>Size:</strong> {(artOutput.size_bytes / 1024).toFixed(0)} KB</span>
                        <a href={imgUrl(artOutput.filename)} target="_blank" rel="noopener" className="art-download">Open Full Size</a>
                      </div>
                    </div>
                    <div className="art-prompt-display">
                      <strong>Prompt:</strong> {artForm.prompt}
                    </div>
                  </div>
                )}

                <div className="art-gallery-section">
                  <h3>Gallery</h3>
                  {bible.generated_images?.length > 0 ? (
                    <div className="card-grid">
                      {[...bible.generated_images].reverse().map((img, i) => (
                        <div key={i} className="art-gallery-card">
                          <img
                            src={imgUrl(img.filename)}
                            alt={img.prompt}
                            className="art-thumb"
                            onClick={() => setArtFullscreen(imgUrl(img.filename))}
                          />
                          <div className="art-thumb-meta">
                            <p className="art-thumb-prompt">{img.prompt?.slice(0, 100)}{img.prompt?.length > 100 ? '...' : ''}</p>
                            <span className="chapter-meta">{img.model?.replace('.safetensors', '')} · seed {img.seed}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-hint">No images generated yet. Use the form above to create art.</p>
                  )}
                </div>

                {artFullscreen && (
                  <div className="modal-overlay" onClick={() => setArtFullscreen(null)}>
                    <div className="art-fullscreen" onClick={e => e.stopPropagation()}>
                      <button className="art-close" onClick={() => setArtFullscreen(null)}>✕</button>
                      <img src={artFullscreen} alt="Full size" className="art-fullscreen-img" />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
