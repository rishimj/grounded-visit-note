import { useEffect, useRef } from 'react'

type TranscriptPaneProps = {
  lines: string[]
  highlighted: Set<number>
}

export function TranscriptPane({ lines, highlighted }: TranscriptPaneProps) {
  const firstHighlight = useRef<HTMLLIElement | null>(null)
  const firstLine = highlighted.size
    ? Math.min(...highlighted)
    : null

  useEffect(() => {
    firstHighlight.current?.scrollIntoView({
      block: 'center',
      behavior: 'smooth',
    })
  }, [firstLine])

  return (
    <section className="pane transcript-pane">
      <h2>Transcript</h2>
      {lines.length === 0 ? (
        <p className="muted">No transcript yet.</p>
      ) : (
        <ol className="transcript">
          {lines.map((line, index) => {
            const n = index + 1
            const isHit = highlighted.has(n)
            return (
              <li
                key={n}
                ref={n === firstLine ? firstHighlight : undefined}
                value={n}
                className={isHit ? 'hit' : undefined}
              >
                {line}
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}
