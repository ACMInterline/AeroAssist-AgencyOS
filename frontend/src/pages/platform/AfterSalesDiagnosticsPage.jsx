import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const caseTypes = [
  "voluntary_change",
  "schedule_change",
  "cancellation",
  "refund",
  "ticket_exchange",
  "emd_exchange_refund",
  "claim",
  "service_amendment",
  "passenger_document_amendment",
  "disruption_irregular_operation",
]

const defaultFilters = {
  agency_id: "",
  status: "",
  case_type: "",
  case_priority: "",
  booking_workspace_id: "",
}

export default function AfterSalesDiagnosticsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/after-sales${query}`),
    ])
    setState({ me, agencies: agencies.items || [], ...response })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.status, filters.case_type, filters.case_priority, filters.booking_workspace_id])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const summary = state?.summary || {}

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">After-Sales Diagnostics</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only platform visibility into servicing and after-sales case metadata. Platform diagnostics do not mutate tickets or EMDs, commit financial actions, send messages, call providers, or act as agency staff.</p>
            </div>
            <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only diagnostics</span>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            <Metric label="Cases" value={summary.case_count || 0} />
            <Metric label="Open" value={summary.open_case_count || 0} />
            <Metric label="Client approvals" value={summary.requires_client_approval_count || 0} />
            <Metric label="Supplier contact" value={summary.requires_supplier_communication_count || 0} />
            <Metric label="Communications" value={state?.recent_communications?.length || 0} />
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Filters</h3>
            <div className="mt-4 grid gap-3 md:grid-cols-5">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={[["", "All agencies"], ...agencyOptions]} />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={["", "opened", "assessing", "awaiting_approval", "processing", "resolved", "cancelled"].map((value) => [value, value ? formatType(value) : "All statuses"])} />
              <SelectField label="Type" value={filters.case_type} onChange={(value) => setFilters({ ...filters, case_type: value })} options={["", ...caseTypes].map((value) => [value, value ? formatType(value) : "All types"])} />
              <SelectField label="Priority" value={filters.case_priority} onChange={(value) => setFilters({ ...filters, case_priority: value })} options={["", "low", "normal", "high", "urgent", "critical"].map((value) => [value, value ? formatType(value) : "All priorities"])} />
              <TextField label="Booking workspace id" value={filters.booking_workspace_id} onChange={(value) => setFilters({ ...filters, booking_workspace_id: value })} />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Recent cases</h3>
            {!state?.items?.length ? <EmptyState title="No after-sales cases" body="Agency servicing and after-sales metadata will appear here." /> : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
                      {["Reference", "Agency", "Type", "Status", "Priority", "Items", "Approval", "Workflow"].map((label) => <th className="px-3 py-2" key={label}>{label}</th>)}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {state.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-3 py-2 font-semibold text-slate-950">{item.case_reference}</td>
                        <td className="px-3 py-2 text-slate-700">{item.agency_id}</td>
                        <td className="px-3 py-2 text-slate-700">{formatType(item.case_type)}</td>
                        <td className="px-3 py-2 text-slate-700">{formatType(item.case_status)}</td>
                        <td className="px-3 py-2 text-slate-700">{formatType(item.case_priority)}</td>
                        <td className="px-3 py-2 text-slate-700">{item.item_count || 0}</td>
                        <td className="px-3 py-2 text-slate-700">{item.client_approval_required ? "required" : "not required"}</td>
                        <td className="px-3 py-2 text-slate-700">{item.workflow_instance_id || "not linked"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <DiagnosticCard title="Financial placeholders" rows={state?.recent_financial_impacts || []} columns={["impact_type", "estimate_status", "placeholder_notes"]} />
            <DiagnosticCard title="Decisions" rows={state?.recent_decisions || []} columns={["decision_type", "decision_status", "client_approval_status"]} />
            <DiagnosticCard title="Communications" rows={state?.recent_communications || []} columns={["communication_type", "audience", "channel"]} />
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function DiagnosticCard({ title, rows, columns }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <div className="mt-4 space-y-3">
        {!rows?.length ? <EmptyState title="No metadata" body="Records will appear after agency case activity." /> : rows.slice(0, 6).map((row) => (
          <div className="rounded-md border border-slate-200 p-3 text-sm" key={row.id}>
            {columns.map((column) => <p className="break-words text-slate-700" key={column}><span className="font-semibold text-slate-950">{formatType(column)}:</span> {formatValue(row[column])}</p>)}
          </div>
        ))}
      </div>
    </section>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function TextField({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function SelectField({ label, value, onChange, options }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([option, text]) => <option value={option} key={option}>{text}</option>)}</select></label>
}

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values || {}).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
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
