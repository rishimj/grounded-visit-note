import type { NoteItem, VisitNote } from '../types'

type NotePaneProps = {
  note: VisitNote | null
  selectedId: string | null
  onSelect: (item: NoteItem) => void
}

export function NotePane({ note, selectedId, onSelect }: NotePaneProps) {
  if (!note) {
    return (
      <section className="pane">
        <h2>Visit note</h2>
        <p className="muted">The SOAP draft appears here after processing.</p>
      </section>
    )
  }

  return (
    <section className="pane">
      <h2>Visit note</h2>
      {note.sections.map((section) => (
        <div key={section.id} className="soap-section">
          <h3>{section.heading}</h3>
          <ul>
            {section.items
              .filter((item) => item.grounded)
              .map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`bullet${selectedId === item.id ? ' selected' : ''}`}
                    onClick={() => onSelect(item)}
                  >
                    <span>{item.text}</span>
                    {item.uncertain ? (
                      <span className="uncertain" title="Uncertain — check the source">
                        Uncertain
                      </span>
                    ) : null}
                  </button>
                </li>
              ))}
          </ul>
        </div>
      ))}
    </section>
  )
}
