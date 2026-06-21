export default function PortalSafeHtmlPreview({ html }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <iframe className="h-[720px] w-full bg-white" sandbox="" srcDoc={html || "<p>No preview available.</p>"} title="Portal document preview" />
    </div>
  )
}
