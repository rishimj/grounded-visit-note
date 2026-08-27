type LoadingPanelProps = {
  phase: 'upload' | 'parse' | 'stitch'
}

const copy: Record<LoadingPanelProps['phase'], { title: string; body: string }> =
  {
    upload: {
      title: 'Saving transcript…',
      body: 'Uploading the file.',
    },
    parse: {
      title: 'Reading the visit…',
      body: 'This can take 30–90 seconds. Stay on this page.',
    },
    stitch: {
      title: 'Building the note…',
      body: 'Assembling the SOAP draft from grounded findings.',
    },
  }

export function LoadingPanel({ phase }: LoadingPanelProps) {
  const { title, body } = copy[phase]
  return (
    <div className="loading-banner" role="status">
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  )
}
