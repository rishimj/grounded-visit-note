import { ApiError, readError } from './errors'
import type {
  JobsApi,
  JobDetail,
  ParseResponse,
  StitchResponse,
  UploadResponse,
} from '../types'

const PARSE_TIMEOUT_MS = 120_000
const DEFAULT_TIMEOUT_MS = 30_000

async function request(
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(0, 'Request timed out. Try again.')
    }
    throw err
  } finally {
    window.clearTimeout(timer)
  }
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw await readError(response)
  }
  return (await response.json()) as T
}

export const httpClient: JobsApi = {
  async createJob(file: File): Promise<UploadResponse> {
    const form = new FormData()
    form.append('file', file)
    const response = await request(
      '/api/jobs',
      { method: 'POST', body: form },
      DEFAULT_TIMEOUT_MS,
    )
    return parseJson<UploadResponse>(response)
  },

  async parseJob(jobId: string): Promise<ParseResponse> {
    const response = await request(
      `/api/jobs/${encodeURIComponent(jobId)}/parse`,
      { method: 'POST' },
      PARSE_TIMEOUT_MS,
    )
    return parseJson<ParseResponse>(response)
  },

  async stitchJob(jobId: string): Promise<StitchResponse> {
    const response = await request(
      `/api/jobs/${encodeURIComponent(jobId)}/stitch`,
      { method: 'POST' },
      DEFAULT_TIMEOUT_MS,
    )
    return parseJson<StitchResponse>(response)
  },

  async getJob(jobId: string): Promise<JobDetail> {
    const response = await request(
      `/api/jobs/${encodeURIComponent(jobId)}`,
      { method: 'GET' },
      DEFAULT_TIMEOUT_MS,
    )
    return parseJson<JobDetail>(response)
  },
}
