type UploadPanelProps = {
  disabled: boolean
  onFile: (file: File) => void
}

export function UploadPanel({ disabled, onFile }: UploadPanelProps) {
  return (
    <section className="panel upload-panel">
      <h1>Grounded visit note</h1>
      <p className="lede">
        Upload a visit transcript (.txt). The app drafts a SOAP note you can
        check against the source lines.
      </p>
      <label className={`drop${disabled ? ' drop-disabled' : ''}`}>
        <input
          type="file"
          accept=".txt,text/plain"
          disabled={disabled}
          onChange={(event) => {
            const file = event.target.files?.[0]
            event.target.value = ''
            if (file) {
              onFile(file)
            }
          }}
        />
        <span>Choose a .txt file</span>
      </label>
      <p className="hint">
        Sample transcripts: <code>docs/transcript_01.txt</code>,{' '}
        <code>docs/transcript_02.txt</code>
      </p>
    </section>
  )
}
