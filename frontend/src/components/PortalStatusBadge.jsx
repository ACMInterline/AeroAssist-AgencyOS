const styles = {
  active: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  invited: "bg-blue-50 text-blue-700 ring-blue-200",
  email_unverified: "bg-amber-50 text-amber-700 ring-amber-200",
  suspended: "bg-rose-50 text-rose-700 ring-rose-200",
  archived: "bg-slate-50 text-slate-700 ring-slate-200",
  default: "bg-slate-50 text-slate-700 ring-slate-200",
}

export default function PortalStatusBadge({ status }) {
  const key = status || "default"
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ${styles[key] || styles.default}`}>{String(key).replaceAll("_", " ")}</span>
}
