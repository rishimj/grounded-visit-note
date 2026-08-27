import { alvarezNote, splitTranscript } from './fixture'
import type {
  JobDetail,
  JobsApi,
  ParseResponse,
  StitchResponse,
  UploadResponse,
} from '../types'
import { ApiError } from './errors'

type Store = {
  lines: string[]
  status: JobDetail['status']
  note: JobDetail['note']
  errors: string[]
  created_at: string
  updated_at: string
}

const STORAGE_KEY = 'gvn_mock_jobs'

function loadJobs(): Map<string, Store> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return new Map()
    }
    return new Map(Object.entries(JSON.parse(raw) as Record<string, Store>))
  } catch {
    return new Map()
  }
}

const jobs = loadJobs()

function persist(): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(Object.fromEntries(jobs)))
}

function nowIso(): string {
  return new Date().toISOString()
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function getStore(jobId: string): Store {
  const job = jobs.get(jobId)
  if (!job) {
    throw new ApiError(404, `Job ${jobId} not found`)
  }
  return job
}

export const mockClient: JobsApi = {
  async createJob(file: File): Promise<UploadResponse> {
    await delay(250)
    const name = file.name.toLowerCase()
    if (!name.endsWith('.txt')) {
      throw new ApiError(400, 'Only .txt transcripts are accepted')
    }
    const text = await file.text()
    const lines = splitTranscript(text)
    if (lines.every((line) => line.trim() === '')) {
      throw new ApiError(400, 'Transcript file is empty')
    }
    const job_id = crypto.randomUUID()
    const ts = nowIso()
    jobs.set(job_id, {
      lines,
      status: 'uploaded',
      note: null,
      errors: [],
      created_at: ts,
      updated_at: ts,
    })
    persist()
    return { job_id, status: 'uploaded', lines }
  },

  async parseJob(jobId: string): Promise<ParseResponse> {
    await delay(1600)
    const job = getStore(jobId)
    job.status = 'parsed'
    job.note = null
    job.updated_at = nowIso()
    persist()
    return {
      job_id: jobId,
      status: 'parsed',
      grounded_count: 12,
      feature_count: 12,
    }
  },

  async stitchJob(jobId: string): Promise<StitchResponse> {
    await delay(200)
    const job = getStore(jobId)
    if (job.status !== 'parsed' && job.status !== 'stitched') {
      throw new ApiError(409, 'Job must be parsed before stitching')
    }
    const note = alvarezNote(job.lines)
    job.status = 'stitched'
    job.note = note
    job.updated_at = nowIso()
    persist()
    return { job_id: jobId, status: 'stitched', note, lines: job.lines }
  },

  async getJob(jobId: string): Promise<JobDetail> {
    await delay(80)
    const job = getStore(jobId)
    return {
      job_id: jobId,
      status: job.status,
      lines: job.lines,
      note: job.note,
      errors: job.errors,
      created_at: job.created_at,
      updated_at: job.updated_at,
    }
  },
}
