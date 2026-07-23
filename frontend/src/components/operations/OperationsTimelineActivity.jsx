import { ArrowRight, CalendarDays, ChevronLeft, ChevronRight, History } from "lucide-react"
import { dateTime, label } from "./operationsFormat"

export default function OperationsTimelineActivity({ mode, timeline, activities = [], onDateChange }) {
  if (mode === "activity") return <RecentActivity activities={activities} />
  const events = timeline?.events || []
  return (
    <section aria-labelledby="timeline-title">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2"><CalendarDays className="h-4 w-4 text-blue-700" /><h2 id="timeline-title" className="text-lg font-semibold text-slate-950">Today’s Timeline</h2></div>
        <div className="flex items-center gap-1">
          <DateButton label="Previous day" onClick={() => onDateChange(timeline.previous_date)}><ChevronLeft className="h-4 w-4" /></DateButton>
          <button className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700" type="button" onClick={() => onDateChange(timeline.today)}>Today</button>
          <DateButton label="Next day" onClick={() => onDateChange(timeline.next_date)}><ChevronRight className="h-4 w-4" /></DateButton>
        </div>
      </div>
      <p className="mt-1 text-sm text-slate-500">{timeline?.selected_date} · {timeline?.timezone}</p>
      <div className="mt-3 overflow-hidden rounded-md border border-slate-200 bg-white">
        {events.length ? <div className="divide-y divide-slate-100">{events.map((event) => (
          <a className="grid grid-cols-[60px_1fr_auto] items-center gap-3 px-4 py-3 text-sm hover:bg-slate-50" href={event.href} key={event.id}>
            <time className="font-semibold text-slate-700">{event.time_label}</time>
            <span><span className="block font-medium text-slate-900">{event.label}</span><span className="text-xs text-slate-500">{label(event.event_type)}</span></span>
            <ArrowRight className="h-4 w-4 text-slate-400" />
          </a>
        ))}</div> : <p className="px-4 py-5 text-sm text-slate-500">No deadlines or scheduled work for this day.</p>}
      </div>
    </section>
  )
}

function RecentActivity({ activities }) {
  return (
    <section aria-labelledby="activity-title">
      <div className="flex items-center gap-2"><History className="h-4 w-4 text-slate-500" /><h2 id="activity-title" className="text-lg font-semibold text-slate-950">Recent Activity</h2></div>
      <div className="mt-3 overflow-hidden rounded-md border border-slate-200 bg-white">
        {activities.length ? <div className="divide-y divide-slate-100">{activities.map((item) => (
          <a className="flex items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-slate-50" href={item.href} key={item.id}>
            <span><span className="block font-medium text-slate-900">{item.label}</span><span className="mt-0.5 block text-xs text-slate-500">{dateTime(item.timestamp)} · {item.actor}</span></span>
            <ArrowRight className="h-4 w-4 shrink-0 text-slate-400" />
          </a>
        ))}</div> : <p className="px-4 py-5 text-sm text-slate-500">No recent activity.</p>}
      </div>
    </section>
  )
}

function DateButton({ label: ariaLabel, onClick, children }) {
  return <button className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-300 text-slate-700" aria-label={ariaLabel} title={ariaLabel} type="button" onClick={onClick}>{children}</button>
}
