import ArrowLeft from "lucide-react/dist/esm/icons/arrow-left.js"
import ChevronRight from "lucide-react/dist/esm/icons/chevron-right.js"
import EmptyState from "../EmptyState"
import PortalStatusBadge from "../PortalStatusBadge"

export function PortalPageHeader({ eyebrow, title, description, backHref, backLabel, status, actions }) {
  return (
    <header className="border-b border-slate-200 pb-5">
      {backHref ? (
        <a className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-900" href={backHref}>
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          {backLabel || "Back"}
        </a>
      ) : null}
      <div className={`${backHref ? "mt-4" : ""} flex flex-wrap items-start justify-between gap-4`}>
        <div className="min-w-0">
          {eyebrow ? <p className="text-xs font-semibold uppercase text-blue-700">{eyebrow}</p> : null}
          <h2 className="mt-1 text-2xl font-semibold text-slate-950">{title}</h2>
          {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {status ? <PortalStatusBadge status={status} /> : null}
          {actions}
        </div>
      </div>
    </header>
  )
}

export function PortalSection({ title, description, action, children }) {
  return (
    <section className="border-t border-slate-200 pt-5 first:border-t-0 first:pt-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-950">{title}</h3>
          {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
        </div>
        {action}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  )
}

export function PortalRecordList({ items, emptyTitle, emptyBody, href, children }) {
  if (!items?.length) {
    return <EmptyState title={emptyTitle} body={emptyBody} />
  }
  return (
    <div className="divide-y divide-slate-200 border-y border-slate-200 bg-white">
      {items.map((item) => {
        const content = (
          <>
            <div className="min-w-0 flex-1">{children(item)}</div>
            {href ? <ChevronRight aria-hidden="true" className="h-4 w-4 shrink-0 text-slate-400" /> : null}
          </>
        )
        return href ? (
          <a className="flex min-h-16 items-center gap-3 px-2 py-4 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-600" href={href(item)} key={item.id}>
            {content}
          </a>
        ) : (
          <div className="flex min-h-16 items-center gap-3 px-2 py-4" key={item.id}>
            {content}
          </div>
        )
      })}
    </div>
  )
}

export function PortalFacts({ rows, columns = 2 }) {
  const grid = columns === 3 ? "md:grid-cols-3" : columns === 1 ? "" : "md:grid-cols-2"
  return (
    <dl className={`grid gap-x-8 gap-y-4 ${grid}`}>
      {rows.map(([label, value]) => (
        <div className="min-w-0 border-b border-slate-100 pb-3" key={label}>
          <dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt>
          <dd className="mt-1 break-words text-sm text-slate-900">{displayValue(value)}</dd>
        </div>
      ))}
    </dl>
  )
}

export function PortalTimeline({ items, empty = "No activity is visible yet." }) {
  if (!items?.length) {
    return <EmptyState title="No activity yet" body={empty} />
  }
  return (
    <ol className="border-l border-slate-300 pl-5">
      {items.map((item) => (
        <li className="relative pb-5 last:pb-0" key={item.id}>
          <span className="absolute -left-[25px] top-1.5 h-2 w-2 rounded-full bg-blue-600" />
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium text-slate-950">{titleCase(item.summary || item.title || item.event_type)}</p>
            {item.status ? <PortalStatusBadge status={item.status} /> : null}
          </div>
          <p className="mt-1 text-xs text-slate-500">{formatDateTime(item.occurred_at || item.created_at)}</p>
        </li>
      ))}
    </ol>
  )
}

export function PortalPill({ children, tone = "slate" }) {
  const tones = {
    blue: "bg-blue-50 text-blue-700 ring-blue-200",
    amber: "bg-amber-50 text-amber-800 ring-amber-200",
    emerald: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    rose: "bg-rose-50 text-rose-700 ring-rose-200",
    slate: "bg-slate-50 text-slate-700 ring-slate-200",
  }
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ${tones[tone]}`}>{children}</span>
}

export function titleCase(value) {
  return String(value || "Not set")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function formatDate(value) {
  if (!value) return "Not set"
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString([], { dateStyle: "medium" })
}

export function formatDateTime(value) {
  if (!value) return "Not set"
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString([], { dateStyle: "medium", timeStyle: "short" })
}

export function formatMoney(value, currency = "EUR") {
  if (value === null || value === undefined || value === "") return "Not set"
  return new Intl.NumberFormat([], { style: "currency", currency: currency || "EUR" }).format(Number(value))
}

function displayValue(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  if (typeof value === "boolean") return value ? "Yes" : "No"
  if (Array.isArray(value)) return value.length ? value.join(", ") : "None"
  if (typeof value === "object") return titleCase(value.label || value.name || value.status || "Available")
  return String(value)
}
