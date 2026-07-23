import { AlertTriangle, ArrowRight, BriefcaseBusiness, FileInput, ListTodo, Plus, TicketCheck, UserPlus } from "lucide-react"
import { dateTime, urgencyTone } from "./operationsFormat"

const actionIcons = {
  new_request: Plus,
  new_offer: BriefcaseBusiness,
  new_booking: TicketCheck,
  new_passenger: UserPlus,
  import_pnr: FileInput,
  open_tasks: ListTodo,
}

export default function OperationsAlerts({ alerts, quickActions }) {
  if (quickActions) return <QuickActions items={quickActions} />
  return (
    <section aria-labelledby="alerts-title">
      <div className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-amber-600" /><h2 id="alerts-title" className="text-lg font-semibold text-slate-950">Needs attention</h2></div>
      <div className="mt-3 overflow-hidden rounded-md border border-slate-200 bg-white">
        {alerts.length ? <div className="divide-y divide-slate-100">{alerts.slice(0, 8).map((alert) => (
          <a className="block px-4 py-3 hover:bg-slate-50" href={alert.href} key={alert.id}>
            <div className="flex items-start justify-between gap-2"><p className="text-sm font-semibold text-slate-900">{alert.what}</p><span className={`rounded border px-1.5 py-0.5 text-[11px] font-semibold ${urgencyTone(alert.urgency)}`}>{alert.urgency}</span></div>
            <p className="mt-1 text-xs leading-5 text-slate-600">{alert.why}</p>
            <p className="mt-2 text-xs font-semibold text-blue-700">{alert.next_action}</p>
            {alert.deadline ? <p className="mt-1 text-xs text-slate-500">{dateTime(alert.deadline)}</p> : null}
          </a>
        ))}</div> : <p className="px-4 py-5 text-sm text-slate-500">No urgent alerts.</p>}
      </div>
    </section>
  )
}

function QuickActions({ items }) {
  return (
    <section aria-labelledby="quick-actions-title">
      <h2 id="quick-actions-title" className="text-lg font-semibold text-slate-950">Quick actions</h2>
      <div className="mt-3 grid grid-cols-2 gap-2">
        {items.map((item) => {
          const Icon = actionIcons[item.key] || ArrowRight
          return <a className="flex min-h-11 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:border-blue-300 hover:text-blue-700" href={item.href} key={item.key}><Icon className="h-4 w-4" />{item.label}</a>
        })}
      </div>
    </section>
  )
}
