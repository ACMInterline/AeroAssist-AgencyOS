import ChevronLeft from "lucide-react/dist/esm/icons/chevron-left.js"
import ChevronRight from "lucide-react/dist/esm/icons/chevron-right.js"
import CircleAlert from "lucide-react/dist/esm/icons/circle-alert.js"
import Clock3 from "lucide-react/dist/esm/icons/clock-3.js"
import Link2 from "lucide-react/dist/esm/icons/link-2.js"
import ListChecks from "lucide-react/dist/esm/icons/list-checks.js"

const validationTone = {
  ready: "border-emerald-200 bg-emerald-50 text-emerald-800",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  blocked: "border-red-200 bg-red-50 text-red-800",
  unknown: "border-slate-200 bg-slate-50 text-slate-700",
}

export default function WorkflowContinuityPanel({
  breadcrumbs = [],
  blockers = [],
  completedStages = [],
  currentLabel,
  currentStage,
  deadline,
  deadlineLabel = "Deadline",
  status = "unknown",
  timelineHref = "/agency/timeline",
  validation = { state: "unknown", label: "Review required" },
  previous,
  next,
  relatedRecords = [],
  warnings = [],
}) {
  const effectiveStage = currentStage || status
  const effectiveWarnings = [
    ...warnings,
    ...(validation.state === "warning" ? [validation.reason || validation.label] : []),
  ].filter(Boolean)
  const effectiveBlockers = [
    ...blockers,
    ...(validation.state === "blocked" ? [validation.reason || validation.label] : []),
  ].filter(Boolean)
  const completed = completedStages.length
    ? completedStages
    : ["draft", "unknown"].includes(String(effectiveStage || "").toLowerCase()) ? [] : ["Record created"]

  return (
    <section className="border-y border-slate-200 bg-white py-4" aria-label="Workflow continuity">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {breadcrumbs.map((item) => <a className="font-medium text-blue-700 hover:underline" href={item.href} key={`${item.href}-${item.label}`}>{item.label}</a>)}
        {breadcrumbs.length ? <span>/</span> : null}
        <span className="font-semibold text-slate-800">{currentLabel}</span>
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <WorkflowFact label="Current stage" value={format(effectiveStage)} />
        <WorkflowFact label="Completed" value={completed.length ? completed.map(format).join(", ") : "No completed stages yet"} />
        <WorkflowFact label="Next action" value={next?.label || "Review this record"} />
        <WorkflowFact label={deadlineLabel} value={formatDeadline(deadline)} icon={Clock3} />
      </div>
      <div className="mt-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(260px,0.9fr)_auto] lg:items-center">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className={`rounded-md border px-3 py-1 text-xs font-semibold ${validationTone[validation.state] || validationTone.unknown}`}>
            {validation.label || format(validation.state)}
          </span>
          {effectiveWarnings.length ? <Signal icon={CircleAlert} label="Warning" items={effectiveWarnings} tone="text-amber-800" /> : null}
          {effectiveBlockers.length ? <Signal icon={CircleAlert} label="Blocked" items={effectiveBlockers} tone="text-red-800" /> : null}
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
          {timelineHref ? <a className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700" href={timelineHref}><ListChecks className="h-4 w-4" />Timeline</a> : null}
          <WorkflowAction action={previous} direction="previous" />
          <WorkflowAction action={next} direction="next" />
        </div>
      </div>
    </section>
  )
}

function WorkflowFact({ icon: Icon, label, value }) {
  return (
    <div className="min-w-0 border-l-2 border-slate-200 pl-3">
      <p className="flex items-center gap-1 text-[11px] font-semibold uppercase text-slate-500">{Icon ? <Icon aria-hidden="true" className="h-3.5 w-3.5" /> : null}{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-slate-900" title={value}>{value}</p>
    </div>
  )
}

function Signal({ icon: Icon, items, label, tone }) {
  const text = items.join("; ")
  return <span className={`inline-flex min-w-0 items-center gap-1 text-xs ${tone}`} title={text}><Icon aria-hidden="true" className="h-3.5 w-3.5 shrink-0" /><span className="truncate">{label}: {text}</span></span>
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

function formatDeadline(value) {
  if (!value) return "No deadline recorded"
  const parsed = new Date(value)
  return Number.isNaN(parsed.valueOf()) ? String(value) : parsed.toLocaleString()
}
