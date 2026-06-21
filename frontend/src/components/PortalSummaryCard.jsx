export default function PortalSummaryCard({ label, value, href }) {
  const content = (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
  return href ? <a className="block hover:opacity-90" href={href}>{content}</a> : content
}
