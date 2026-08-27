import type { Citation } from '../types'

type SourceQuotesProps = {
  citations: Citation[]
}

export function SourceQuotes({ citations }: SourceQuotesProps) {
  if (citations.length === 0) {
    return (
      <section className="pane source-pane">
        <h2>Source</h2>
        <p className="muted">Click a note bullet to see the grounded quotes.</p>
      </section>
    )
  }

  return (
    <section className="pane source-pane">
      <h2>Source</h2>
      <ul className="quotes">
        {citations.map((citation, index) => (
          <li key={`${citation.offsets.start}-${index}`}>
            <blockquote>{citation.quote}</blockquote>
            <span className="line-meta">
              Line{citation.line_numbers.length === 1 ? '' : 's'}{' '}
              {citation.line_numbers.join(', ')}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
