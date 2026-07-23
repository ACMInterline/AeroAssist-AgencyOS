import Clock3 from "lucide-react/dist/esm/icons/clock-3.js"
import EmptyState from "./EmptyState"

export default function Timeline({
  emptyBody = "Updates will appear here as work progresses.",
  emptyTitle = "No activity yet",
  items = [],
}) {
  if (!items.length) return <EmptyState title={emptyTitle} body={emptyBody} />
  return (
    <ol aria-label="Activity history" className="divide-y divide-slate-200 border-y border-slate-200">
      {items.map((item, index) => (
        <li className="grid gap-2 py-4 sm:grid-cols-[160px_minmax(0,1fr)]" key={item.id || `${item.title}-${index}`}>
          <time className="inline-flex items-center gap-2 text-xs text-slate-500" dateTime={item.created_at || item.timestamp || ""}>
            <Clock3 aria-hidden="true" className="h-3.5 w-3.5" />
            {formatDate(item.created_at || item.timestamp)}
          </time>
          <div>
            <p className="text-sm font-semibold text-slate-900">{item.title || item.event_type || "Update"}</p>
            {item.summary || item.description ? <p className="mt-1 text-sm leading-6 text-slate-600">{item.summary || item.description}</p> : null}
          </div>
        </li>
      ))}
    </ol>
  )
}

function formatDate(value) {
  if (!value) return "Time not recorded"
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString()
}
