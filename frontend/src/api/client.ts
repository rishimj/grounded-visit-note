import { httpClient } from './httpClient'
import { mockClient } from './mockClient'
import type { JobsApi } from '../types'

/** Real FastAPI unless VITE_USE_MOCK=true. */
export const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export const api: JobsApi = useMock ? mockClient : httpClient
