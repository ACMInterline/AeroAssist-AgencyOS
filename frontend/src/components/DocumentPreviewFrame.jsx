export default function DocumentPreviewFrame({ html }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <iframe className="h-[760px] w-full bg-white" sandbox="" srcDoc={html || "<p>No preview available.</p>"} title="Document preview" />
    </div>
  )
}
