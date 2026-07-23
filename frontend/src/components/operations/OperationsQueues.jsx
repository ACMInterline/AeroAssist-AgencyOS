import { ArrowRight } from "lucide-react"
import { dateTime } from "./operationsFormat"

export default function OperationsQueues({ queues }) {
  return (
    <section aria-labelledby="queues-title">
      <h2 id="queues-title" className="text-lg font-semibold text-slate-950">Queues</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {queues.map((queue) => (
          <div className="overflow-hidden rounded-md border border-slate-200 bg-white" key={queue.key}>
            <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
              <h3 className="text-sm font-semibold text-slate-900">{queue.label}</h3>
              <span className="min-w-7 rounded bg-slate-100 px-2 py-1 text-center text-xs font-semibold text-slate-700">{queue.count}</span>
            </div>
            {queue.items?.length ? (
              <div className="divide-y divide-slate-100">
                {queue.items.slice(0, 3).map((item) => (
                  <a className="flex items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-slate-50" href={item.href} key={item.id}>
                    <span className="min-w-0"><span className="block truncate font-medium text-slate-800">{item.label}</span><span className="mt-0.5 block text-xs text-slate-500">{dateTime(item.deadline, item.status || "Open")}</span></span>
                    <ArrowRight className="h-4 w-4 shrink-0 text-slate-400" />
                  </a>
                ))}
              </div>
            ) : <p className="px-4 py-4 text-sm text-slate-500">Nothing waiting.</p>}
            {queue.count > 3 ? <a className="block border-t border-slate-100 px-4 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-50" href={queue.href}>View all {queue.count}</a> : null}
          </div>
        ))}
      </div>
    </section>
  )
}
