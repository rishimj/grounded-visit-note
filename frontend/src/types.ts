export type JobStatus = 'uploaded' | 'parsed' | 'stitched' | 'failed'

export type CitationOffsets = {
  start: number
  end: number
}

export type Citation = {
  quote: string
  line_numbers: number[]
  offsets: CitationOffsets
}

export type NoteItem = {
  id: string
  text: string
  citations: Citation[]
  uncertain: boolean
  grounded: boolean
}

export type SectionId = 'subjective' | 'objective' | 'assessment' | 'plan'

export type NoteSection = {
  id: SectionId
  heading: string
  items: NoteItem[]
}

export type VisitNote = {
  sections: NoteSection[]
}

export type UploadResponse = {
  job_id: string
  status: 'uploaded'
  lines: string[]
}

export type ParseResponse = {
  job_id: string
  status: 'parsed'
  grounded_count: number
  feature_count: number
}

export type StitchResponse = {
  job_id: string
  status: 'stitched'
  note: VisitNote
  lines: string[]
}

export type JobDetail = {
  job_id: string
  status: JobStatus
  lines: string[]
  note: VisitNote | null
  errors: string[]
  created_at: string
  updated_at: string
}

export type ParseFailedBody = {
  job_id: string
  status: 'failed'
  errors: string[]
}

export type JobsApi = {
  createJob: (file: File) => Promise<UploadResponse>
  parseJob: (jobId: string) => Promise<ParseResponse>
  stitchJob: (jobId: string) => Promise<StitchResponse>
  getJob: (jobId: string) => Promise<JobDetail>
}
