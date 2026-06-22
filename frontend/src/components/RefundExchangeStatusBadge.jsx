const colors = {
  draft: "bg-slate-50 text-slate-700 ring-slate-200",
  client_requested: "bg-blue-50 text-blue-700 ring-blue-200",
  review_needed: "bg-amber-50 text-amber-700 ring-amber-200",
  checking_supplier_rules: "bg-violet-50 text-violet-700 ring-violet-200",
  waiting_for_client: "bg-purple-50 text-purple-700 ring-purple-200",
  waiting_for_supplier: "bg-cyan-50 text-cyan-700 ring-cyan-200",
  approved: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  processing_externally: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  completed: "bg-green-50 text-green-700 ring-green-200",
  rejected: "bg-rose-50 text-rose-700 ring-rose-200",
  cancelled: "bg-amber-100 text-rose-700 ring-rose-200",
  archived: "bg-slate-100 text-slate-500 ring-slate-200",
}

export default function RefundExchangeStatusBadge({ status }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ${colors[status] || colors.draft}`}>
      {String(status || "draft").replaceAll("_", " ")}
    </span>
  )
}
