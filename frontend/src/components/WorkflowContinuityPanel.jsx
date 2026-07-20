import ChevronLeft from "lucide-react/dist/esm/icons/chevron-left.js"
import ChevronRight from "lucide-react/dist/esm/icons/chevron-right.js"
import Link2 from "lucide-react/dist/esm/icons/link-2.js"

const validationTone = {
  ready: "border-emerald-200 bg-emerald-50 text-emerald-800",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  blocked: "border-red-200 bg-red-50 text-red-800",
  unknown: "border-slate-200 bg-slate-50 text-slate-700",
}

export default function WorkflowContinuityPanel({
  breadcrumbs = [],
  currentLabel,
  status = "unknown",
  validation = { state: "unknown", label: "Review required" },
  previous,
  next,
  relatedRecords = [],
}) {
  return (
    <section className="border-y border-slate-200 bg-white py-4" aria-label="Workflow continuity">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {breadcrumbs.map((item) => <a className="font-medium text-blue-700 hover:underline" href={item.href} key={`${item.href}-${item.label}`}>{item.label}</a>)}
        {breadcrumbs.length ? <span>/</span> : null}
        <span className="font-semibold text-slate-800">{currentLabel}</span>
      </div>
      <div className="mt-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(260px,0.9fr)_auto] lg:items-center">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">Status: {format(status)}</span>
          <span className={`rounded-md border px-3 py-1 text-xs font-semibold ${validationTone[validation.state] || validationTone.unknown}`}>
            {validation.label || format(validation.state)}
          </span>
          {validation.reason ? <span className="text-xs text-slate-600">{validation.reason}</span> : null}
        </div>
        <div className="flex min-w-0 flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
          {relatedRecords.map((item) => item.href ? (
            <a className="inline-flex min-w-0 items-center gap-1 font-medium text-blue-700 hover:underline" href={item.href} key={`${item.label}-${item.href}`}>
              <Link2 className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{item.label}: {item.value || "open"}</span>
            </a>
          ) : (
            <span className="inline-flex min-w-0 items-center gap-1" key={item.label}><Link2 className="h-3.5 w-3.5 shrink-0" /><span className="truncate">{item.label}: {item.value || "none"}</span></span>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 lg:justify-end">
          <WorkflowAction action={previous} direction="previous" />
          <WorkflowAction action={next} direction="next" />
        </div>
      </div>
    </section>
  )
}

function WorkflowAction({ action, direction }) {
  if (!action) return null
  const enabled = action.enabled !== false
  const className = direction === "next"
    ? "aa-primary-action inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
    : "inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
  const content = <>{direction === "previous" ? <ChevronLeft className="h-4 w-4" /> : null}{action.label}{direction === "next" ? <ChevronRight className="h-4 w-4" /> : null}</>
  if (enabled && action.href) return <a className={className} href={action.href}>{content}</a>
  return <button className={className} type="button" disabled={!enabled} onClick={enabled ? action.onClick : undefined} title={!enabled ? action.reason : undefined}>{content}</button>
}

function format(value) {
  return String(value || "unknown").replaceAll("_", " ")
}
