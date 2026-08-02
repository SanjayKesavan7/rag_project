import { useMemo, useState } from 'react'
import './App.css'

const API_BASE_URL = 'http://localhost:3000'

const initialMessages = [
  {
    role: 'assistant',
    content:
      'Upload a PDF and ask a question. Studex will answer only from the indexed document context.',
  },
]

function App() {
  const [file, setFile] = useState(null)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState(initialMessages)
  const [sources, setSources] = useState([])
  const [uploadStatus, setUploadStatus] = useState('No document uploaded')
  const [isUploading, setIsUploading] = useState(false)
  const [isAsking, setIsAsking] = useState(false)

  const sourceNames = useMemo(() => {
    const names = sources
      .map((source) => source?.source)
      .filter(Boolean)

    return [...new Set(names)]
  }, [sources])

  async function handleUpload(event) {
    event.preventDefault()

    if (!file) {
      setUploadStatus('Choose a PDF before uploading.')
      return
    }

    const formData = new FormData()
    formData.append('document', file)

    setIsUploading(true)
    setUploadStatus('Uploading and indexing...')

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed.')
      }

      setUploadStatus(`${file.name} is ready`)
    } catch (error) {
      setUploadStatus(error.message || 'Upload failed.')
    } finally {
      setIsUploading(false)
    }
  }

  async function handleAsk(event) {
    event.preventDefault()

    const trimmedQuestion = question.trim()
    if (!trimmedQuestion) {
      return
    }

    const nextMessages = [
      ...messages,
      { role: 'user', content: trimmedQuestion },
    ]

    setMessages(nextMessages)
    setQuestion('')
    setIsAsking(true)
    setSources([])

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: trimmedQuestion }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Unable to get an answer right now.')
      }

      setMessages([
        ...nextMessages,
        {
          role: 'assistant',
          content: data.answer || 'No answer returned.',
        },
      ])
      setSources(data.sources || [])
    } catch (error) {
      setMessages([
        ...nextMessages,
        {
          role: 'assistant',
          content: error.message || 'Unable to get an answer right now.',
        },
      ])
    } finally {
      setIsAsking(false)
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="brand-mark">Studex</p>
          <h1>Chat with your notes</h1>
          <p className="sidebar-copy">
            Upload one PDF, then ask questions grounded in that document.
          </p>
        </div>

        <form className="upload-panel" onSubmit={handleUpload}>
          <label className="upload-field" htmlFor="pdf-upload">
            <span className="field-label">Document</span>
            <input
              id="pdf-upload"
              type="file"
              accept="application/pdf"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
            <span className="file-name">{file ? file.name : 'No file selected'}</span>
          </label>

          <button className="primary-button" type="submit" disabled={isUploading}>
            {isUploading ? 'Uploading...' : 'Upload PDF'}
          </button>

          <p className="upload-status">{uploadStatus}</p>
        </form>

        <section className="sources-panel">
          <p className="section-label">Sources</p>
          {sourceNames.length === 0 ? (
            <p className="muted-text">Uploaded document names will appear here.</p>
          ) : (
            <ul className="sources-list">
              {sourceNames.map((sourceName) => (
                <li key={sourceName}>{sourceName}</li>
              ))}
            </ul>
          )}
        </section>
      </aside>

      <section className="chat-layout">
        <header className="chat-topbar">
          <div>
            <p className="section-label">Studex chat</p>
            <h2>Ask from the uploaded PDF</h2>
          </div>
        </header>

        <div className="messages">
          {messages.map((message, index) => (
            <article
              key={`${message.role}-${index}`}
              className={`message-row ${message.role}`}
            >
              <div className={`message-bubble ${message.role}`}>
                <span className="message-role">
                  {message.role === 'assistant' ? 'Studex' : 'You'}
                </span>
                <p>{message.content}</p>
              </div>
            </article>
          ))}
        </div>

        <form className="composer" onSubmit={handleAsk}>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question from the uploaded PDF..."
            rows="3"
          />
          <button className="primary-button" type="submit" disabled={isAsking}>
            {isAsking ? 'Thinking...' : 'Send'}
          </button>
        </form>
      </section>
    </main>
  )
}

export default App
