export function label(value, fallback = "Not set") {
  if (value === null || value === undefined || value === "") return fallback
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function dateTime(value, fallback = "No deadline") {
  if (!value) return fallback
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return String(value)
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(parsed)
}

export function urgencyTone(value) {
  const key = String(value || "").toLowerCase()
  if (key === "critical") return "border-red-200 bg-red-50 text-red-800"
  if (key === "urgent") return "border-amber-300 bg-amber-50 text-amber-900"
  if (key === "high") return "border-orange-200 bg-orange-50 text-orange-800"
  return "border-slate-200 bg-slate-50 text-slate-700"
}
