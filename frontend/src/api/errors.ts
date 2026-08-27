export class ApiError extends Error {
  status: number
  detail: string
  errors: string[]

  constructor(status: number, detail: string, errors: string[] = []) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.errors = errors
  }
}

export async function readError(response: Response): Promise<ApiError> {
  const text = await response.text()
  try {
    const body = JSON.parse(text) as {
      detail?: string
      errors?: string[]
      job_id?: string
      status?: string
    }
    if (response.status === 502 && Array.isArray(body.errors)) {
      return new ApiError(
        502,
        body.errors.join(' ') || 'Parse failed',
        body.errors,
      )
    }
    if (typeof body.detail === 'string') {
      return new ApiError(response.status, body.detail)
    }
  } catch {
    /* not JSON */
  }
  return new ApiError(
    response.status,
    text.trim() || `Request failed (${response.status})`,
  )
}
