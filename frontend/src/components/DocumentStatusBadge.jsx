const styles = {
  draft: "bg-slate-50 text-slate-700 ring-slate-200",
  rendered: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  superseded: "bg-amber-50 text-amber-700 ring-amber-200",
  archived: "bg-rose-50 text-rose-700 ring-rose-200",
  active: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  inactive: "bg-slate-50 text-slate-700 ring-slate-200",
}

export default function DocumentStatusBadge({ status }) {
  const key = status || "draft"
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ${styles[key] || styles.draft}`}>{String(key).replaceAll("_", " ")}</span>
}
