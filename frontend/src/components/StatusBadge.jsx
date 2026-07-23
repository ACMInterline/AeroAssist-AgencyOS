import { productLabel } from "../lib/productLanguage"

const styles = {
  active: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  approved: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  booked: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  confirmed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  ready: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  verified: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  trial: "bg-blue-50 text-blue-700 ring-blue-200",
  draft: "bg-slate-50 text-slate-700 ring-slate-200",
  pending: "bg-blue-50 text-blue-700 ring-blue-200",
  in_progress: "bg-blue-50 text-blue-700 ring-blue-200",
  onboarding: "bg-amber-50 text-amber-700 ring-amber-200",
  blocked: "bg-red-50 text-red-800 ring-red-200",
  cancelled: "bg-red-50 text-red-800 ring-red-200",
  expired: "bg-red-50 text-red-800 ring-red-200",
  failed: "bg-red-50 text-red-800 ring-red-200",
  rejected: "bg-red-50 text-red-800 ring-red-200",
  suspended: "bg-rose-50 text-rose-700 ring-rose-200",
  warning: "bg-amber-50 text-amber-900 ring-amber-200",
  default: "bg-slate-50 text-slate-700 ring-slate-200",
}

export default function StatusBadge({ label, status }) {
  const key = status || "default"
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${styles[key] || styles.default}`}>
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
      <span>{label || productLabel(key)}</span>
    </span>
  )
}
