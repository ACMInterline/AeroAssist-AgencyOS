import { ArrowRight, CheckCircle2, UserCheck, UsersRound } from "lucide-react"
import EmptyState from "../EmptyState"
import { dateTime, label, urgencyTone } from "./operationsFormat"

export default function OperationsWorkList({ priorities, assignees, busyAction, onAction }) {
  const items = priorities?.items || []
  return (
    <section aria-labelledby="my-work-title">
      <div className="flex items-center justify-between gap-3">
        <h2 id="my-work-title" className="text-lg font-semibold text-slate-950">My Work Today</h2>
        <span className="text-sm text-slate-500">{priorities?.displayed_count || 0} items</span>
      </div>
      {!items.length ? <div className="mt-3 rounded-md border border-slate-200 bg-white"><EmptyState title="You’re caught up" body="Assigned and available work will appear here." /></div> : (
        <div className="mt-3 overflow-hidden rounded-md border border-slate-200 bg-white">
          <div className="hidden grid-cols-[minmax(210px,1.4fr)_minmax(140px,0.8fr)_150px_115px] gap-3 border-b border-slate-200 bg-slate-50 px-4 py-2 text-xs font-semibold text-slate-500 lg:grid">
            <span>Work</span><span>Next action</span><span>Deadline</span><span>Consultant</span>
          </div>
          <div className="divide-y divide-slate-100">
            {items.map((item) => <WorkRow item={item} assignees={assignees} busyAction={busyAction} onAction={onAction} key={item.id} />)}
          </div>
        </div>
      )}
    </section>
  )
}

function WorkRow({ item, assignees, busyAction, onAction }) {
  const busy = busyAction.startsWith(`${item.id}:`)
  const reassign = item.actions?.find((action) => action.key === "reassign")
  return (
    <article className="px-4 py-4">
      <div className="grid gap-3 lg:grid-cols-[minmax(210px,1.4fr)_minmax(140px,0.8fr)_150px_115px]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${urgencyTone(item.urgency)}`}>{label(item.urgency)}</span>
            <span className="max-w-full truncate text-xs text-slate-500" title={`${item.source_label} ${item.source_id}`}>{item.source_label} · {item.source_id}</span>
          </div>
          <p className="mt-2 font-semibold text-slate-950">{item.reason}</p>
          <p className="mt-1 truncate text-sm text-slate-600">{item.client} · {item.passenger} · {item.trip_or_route}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500 lg:hidden">Next action</p>
          <p className="text-sm font-medium text-slate-800">{item.next_action}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500 lg:hidden">Deadline</p>
          <p className="text-sm text-slate-700">{dateTime(item.deadline)}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500 lg:hidden">Consultant</p>
          <p className="text-sm text-slate-700">{item.consultant}</p>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {item.actions?.filter((action) => action.key !== "reassign").map((action) => action.href ? (
          <a className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" href={action.href} key={action.key}>{action.label}<ArrowRight className="h-3.5 w-3.5" /></a>
        ) : (
          <button className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 disabled:opacity-50" disabled={busy} type="button" onClick={() => onAction(item, action)} key={action.key}>
            {action.key === "assign_self" ? <UserCheck className="h-3.5 w-3.5" /> : <CheckCircle2 className="h-3.5 w-3.5" />}{action.label}
          </button>
        ))}
        {reassign && assignees.length ? (
          <label className="inline-flex items-center gap-1 text-xs text-slate-600">
            <UsersRound className="h-3.5 w-3.5" />
            <span className="sr-only">Reassign to</span>
            <select className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-xs" disabled={busy} defaultValue="" onChange={(event) => { if (event.target.value) onAction(item, reassign, event.target.value); event.target.value = "" }}>
              <option value="">Reassign…</option>
              {assignees.map((assignee) => <option value={assignee.value} key={assignee.value}>{assignee.label}</option>)}
            </select>
          </label>
        ) : null}
      </div>
    </article>
  )
}
