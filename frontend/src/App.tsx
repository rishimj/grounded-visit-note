import { useMemo, useState } from 'react'
import { api, useMock } from './api/client'
import { ApiError } from './api/errors'
import { LoadingPanel } from './components/LoadingPanel'
import { NotePane } from './components/NotePane'
import { SourceQuotes } from './components/SourceQuotes'
import { TranscriptPane } from './components/TranscriptPane'
import { UploadPanel } from './components/UploadPanel'
import type { Citation, NoteItem, VisitNote } from './types'

type UiState = 'idle' | 'loading' | 'ready' | 'error'
type Phase = 'upload' | 'parse' | 'stitch'

const SESSION_KEY = 'gvn_job_id'

export default function App() {
  const [ui, setUi] = useState<UiState>('idle')
  const [phase, setPhase] = useState<Phase>('upload')
  const [jobId, setJobId] = useState<string | null>(null)
  const [lines, setLines] = useState<string[]>([])
  const [note, setNote] = useState<VisitNote | null>(null)
  const [selected, setSelected] = useState<NoteItem | null>(null)
  const [error, setError] = useState<string | null>(null)

  const highlighted = useMemo(() => {
    const nums = new Set<number>()
    for (const citation of selected?.citations ?? []) {
      for (const n of citation.line_numbers) {
        nums.add(n)
      }
    }
    return nums
  }, [selected])

  const citations: Citation[] = selected?.citations ?? []

  async function runPipeline(file: File) {
    setUi('loading')
    setError(null)
    setNote(null)
    setSelected(null)
    setLines([])
    try {
      setPhase('upload')
      const uploaded = await api.createJob(file)
      setJobId(uploaded.job_id)
      setLines(uploaded.lines)
      sessionStorage.setItem(SESSION_KEY, uploaded.job_id)

      setPhase('parse')
      await api.parseJob(uploaded.job_id)

      setPhase('stitch')
      const stitched = await api.stitchJob(uploaded.job_id)
      setLines(stitched.lines)
      setNote(stitched.note)
      setUi('ready')
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.errors.length
            ? err.errors.join(' ')
            : err.detail
          : 'Something went wrong.'
      setError(message)
      setUi('error')
    }
  }

  async function restoreLast() {
    const id = sessionStorage.getItem(SESSION_KEY)
    if (!id) {
      return
    }
    setUi('loading')
    setPhase('upload')
    setError(null)
    try {
      const job = await api.getJob(id)
      setJobId(job.job_id)
      setLines(job.lines)
      if (job.status === 'stitched' && job.note) {
        setNote(job.note)
        setUi('ready')
        return
      }
      setError(
        job.status === 'failed'
          ? job.errors.join(' ') || 'This job failed. Upload again.'
          : 'Last job is not finished. Upload again to generate a note.',
      )
      setUi('error')
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : 'Could not restore job.'
      setError(message)
      setUi('error')
    }
  }

  function reset() {
    setUi('idle')
    setPhase('upload')
    setJobId(null)
    setLines([])
    setNote(null)
    setSelected(null)
    setError(null)
  }

  const showWorkspace = ui === 'loading' || ui === 'ready' || (ui === 'error' && lines.length > 0)

  return (
    <div className="app">
      <header className="top">
        <span className="brand">Grounded visit note</span>
        {useMock ? <span className="badge">Mock API</span> : null}
        {jobId ? <span className="job">Job {jobId.slice(0, 8)}</span> : null}
        <span className="spacer" />
        {ui !== 'idle' ? (
          <button type="button" className="text-btn" onClick={reset}>
            New file
          </button>
        ) : (
          <button type="button" className="text-btn" onClick={() => void restoreLast()}>
            Restore last
          </button>
        )}
      </header>

      {ui === 'idle' ? <UploadPanel disabled={false} onFile={(file) => void runPipeline(file)} /> : null}

      {ui === 'error' ? (
        <div className="error-banner" role="alert">
          <p>{error}</p>
          <button type="button" onClick={reset}>
            Try again
          </button>
        </div>
      ) : null}

      {ui === 'loading' ? <LoadingPanel phase={phase} /> : null}

      {showWorkspace ? (
        <div className="workspace">
          <div className="note-column">
            <NotePane
              note={note}
              selectedId={selected?.id ?? null}
              onSelect={setSelected}
            />
            <SourceQuotes citations={citations} />
          </div>
          <TranscriptPane lines={lines} highlighted={highlighted} />
        </div>
      ) : null}
    </div>
  )
}
