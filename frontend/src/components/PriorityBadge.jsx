import { productLabel } from "../lib/productLanguage"

const styles = {
  urgent: "bg-red-50 text-red-800 ring-red-200",
  critical: "bg-red-50 text-red-800 ring-red-200",
  high: "bg-amber-50 text-amber-900 ring-amber-200",
  normal: "bg-blue-50 text-blue-800 ring-blue-200",
  medium: "bg-blue-50 text-blue-800 ring-blue-200",
  low: "bg-slate-50 text-slate-700 ring-slate-200",
}

export default function PriorityBadge({ priority = "normal" }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${styles[priority] || styles.normal}`}>
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
      <span>{productLabel(priority)} priority</span>
    </span>
  )
}
