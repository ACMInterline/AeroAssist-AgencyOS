const styles = {
  low: "bg-rose-50 text-rose-700 ring-rose-200",
  medium: "bg-amber-50 text-amber-700 ring-amber-200",
  high: "bg-blue-50 text-blue-700 ring-blue-200",
  official_source: "bg-emerald-50 text-emerald-700 ring-emerald-200",
}

export default function ConfidenceBadge({ confidence }) {
  const key = confidence || "medium"
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ${styles[key] || styles.medium}`}>{String(key).replaceAll("_", " ")}</span>
}
