const colors = {
  draft: "bg-slate-50 text-slate-700 ring-slate-200",
  ready_to_send: "bg-blue-50 text-blue-700 ring-blue-200",
  sent: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  viewed: "bg-cyan-50 text-cyan-700 ring-cyan-200",
  accepted: "bg-green-50 text-green-700 ring-green-200",
  rejected: "bg-rose-50 text-rose-700 ring-rose-200",
  expired: "bg-amber-50 text-amber-700 ring-amber-200",
  withdrawn: "bg-slate-100 text-slate-600 ring-slate-200",
  archived: "bg-slate-100 text-slate-500 ring-slate-200",
}

export default function OfferStatusBadge({ status }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ${colors[status] || colors.draft}`}>
      {String(status || "draft").replaceAll("_", " ")}
    </span>
  )
}
