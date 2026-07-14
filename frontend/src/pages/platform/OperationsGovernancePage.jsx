import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const views = ["dashboard", "queue", "kanban", "calendar", "timeline", "exceptions", "workload"]

export default function OperationsGovernancePage() {
  const [state, setState] = useState(null)
  const [agencyId, setAgencyId] = useState("")
  const [view, setView] = useState("dashboard")
  const [error, setError] = useState("")

  async function load(nextAgencyId = agencyId) {
    const query = nextAgencyId ? `?agency_id=${encodeURIComponent(nextAgencyId)}` : ""
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/operations-governance${query}`),
    ])
    setState({ me, agencies: agencies.items || [], ...response })
  }

  useEffect(() => {
    load(agencyId).catch((err) => setError(err.message))
  }, [agencyId])

  const kpis = state?.kpis || {}
  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operations Governance</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only platform command center aggregated from existing agency operational metadata. Platform can inspect workload, deadlines, workflow lanes, exceptions, calendar events, and team load without acting as agency staff or duplicating operational records.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Aggregation only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No drag-and-drop mutation</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <label className="grid max-w-sm gap-1 text-sm font-medium text-slate-700">
              Agency filter
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={agencyId} onChange={(event) => setAgencyId(event.target.value)}>
                <option value="">All agencies</option>
                {agencyOptions.map(([value, label]) => <option value={value} key={value}>{label}</option>)}
              </select>
            </label>
          </section>

          <section className="grid gap-3 md:grid-cols-4 xl:grid-cols-6">
            <Metric label="Workload" value={kpis.current_operational_workload || 0} />
            <Metric label="Unassigned" value={kpis.unassigned_work || 0} />
            <Metric label="Due soon" value={kpis.due_soon || 0} />
            <Metric label="Overdue" value={kpis.overdue || 0} />
            <Metric label="Critical blockers" value={kpis.critical_blockers || 0} />
            <Metric label="After-sales" value={kpis.after_sales_cases || 0} />
          </section>

          <nav className="flex flex-wrap gap-2">
            {views.map((item) => (
              <button className={`rounded-md border px-3 py-2 text-sm font-semibold ${view === item ? "border-blue-600 bg-blue-50 text-blue-700" : "border-slate-200 bg-white text-slate-700"}`} key={item} type="button" onClick={() => setView(item)}>{formatType(item)}</button>
            ))}
          </nav>

          {view === "dashboard" ? <Dashboard state={state} /> : null}
          {view === "queue" ? <Feed title="Urgency-ranked operational feed" items={state?.queue || []} /> : null}
          {view === "kanban" ? <Kanban lanes={state?.kanban?.lanes || []} /> : null}
          {view === "calendar" ? <Calendar events={state?.calendar?.events || []} /> : null}
          {view === "timeline" ? <Timeline events={state?.timeline?.events || []} /> : null}
          {view === "exceptions" ? <Feed title="Exception list" items={state?.exceptions || []} /> : null}
          {view === "workload" ? <Workload items={state?.workload || []} /> : null}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Dashboard({ state }) {
  const kpis = state?.kpis || {}
  const cards = [
    ["Requests awaiting triage", kpis.requests_awaiting_triage],
    ["Offers awaiting action", kpis.offers_awaiting_action],
    ["Accepted offers awaiting booking", kpis.accepted_offers_awaiting_booking],
    ["Bookings awaiting ticketing", kpis.bookings_awaiting_ticketing],
    ["Service approvals/documents", kpis.service_approvals_documents],
    ["Departures 24h", kpis.departures_next_24_hours],
    ["Departures 48h", kpis.departures_next_48_hours],
    ["Departures 72h", kpis.departures_next_72_hours],
    ["Disrupted trips", kpis.disrupted_trips],
    ["Knowledge/manual review", kpis.unresolved_knowledge_manual_review],
    ["Payment/invoice blockers", kpis.payment_invoice_blockers],
    ["Pilot readiness issues", kpis.pilot_readiness_issues],
  ]
  return (
    <div className="space-y-4">
      <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-4">
        {cards.map(([label, value]) => <Metric label={label} value={value || 0} key={label} />)}
      </section>
      <Feed title="Top operational feed" items={state?.dashboard?.top_feed || []} />
    </div>
  )
}

function Feed({ title, items }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      {!items?.length ? <EmptyState title="No operational items" body="Aggregated work appears here when source modules contain open metadata." /> : (
        <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
          {items.map((item) => (
            <a className="grid gap-3 px-4 py-3 text-sm hover:bg-slate-50 lg:grid-cols-[1.3fr_0.8fr_0.7fr_0.7fr]" href={item.safe_action_link || "#"} key={item.id}>
              <span><span className="font-semibold text-slate-950">{item.title}</span><span className="mt-1 block text-slate-500">{item.summary || formatType(item.source)}</span></span>
              <span>{formatType(item.status)}</span>
              <span>{formatType(item.priority)}</span>
              <span>{item.urgency_score || 0}</span>
            </a>
          ))}
        </div>
      )}
    </section>
  )
}

function Kanban({ lanes }) {
  return (
    <section className="space-y-3">
      <p className="text-sm text-slate-600">Kanban lanes are derived from workflow state. Moves must be performed through valid workflow transitions and guard checks; uncontrolled drag-and-drop is disabled.</p>
      {!lanes?.length ? <EmptyState title="No workflow lanes" body="Workflow instances will populate lanes." /> : (
        <div className="grid gap-4 lg:grid-cols-3">
          {lanes.map((lane) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={lane.lane_key}>
              <h3 className="font-semibold text-slate-950">{lane.title} <span className="text-slate-500">({lane.count})</span></h3>
              <div className="mt-3 space-y-2">
                {lane.cards.map((card) => (
                  <a className="block rounded-md border border-slate-200 p-3 text-sm hover:bg-slate-50" href={card.transition_route_required} key={card.id}>
                    <span className="font-semibold text-slate-950">{formatType(card.entity_type)}</span>
                    <span className="mt-1 block text-slate-600">{card.entity_id}</span>
                    <span className="mt-2 block text-xs text-blue-700">Workflow transition required</span>
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

function Calendar({ events }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">Calendar</h3>
      <CompactTable rows={events || []} columns={["event_type", "title", "start", "status"]} />
    </section>
  )
}

function Timeline({ events }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">Timeline</h3>
      <CompactTable rows={events || []} columns={["event_type", "title", "timestamp", "source_entity_type"]} />
    </section>
  )
}

function Workload({ items }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">Agent and team workload</h3>
      <CompactTable rows={items || []} columns={["owner_key", "open_count", "critical_count", "overdue_count", "blocked_count"]} />
    </section>
  )
}

function CompactTable({ rows, columns }) {
  if (!rows?.length) return <EmptyState title="No metadata" body="Aggregated records will appear here." />
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
            {columns.map((column) => <th className="px-3 py-2" key={column}>{formatType(column)}</th>)}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={row.id || row.owner_key || row.title}>
              {columns.map((column) => <td className="px-3 py-2 text-slate-700" key={column}>{formatValue(row[column])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  if (typeof value === "object") return JSON.stringify(value)
  return formatType(value)
}

function formatType(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  return String(value).replaceAll("_", " ")
}
