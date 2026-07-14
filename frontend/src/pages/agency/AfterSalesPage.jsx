import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

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

const defaultForm = {
  case_type: "voluntary_change",
  case_priority: "normal",
  case_title: "",
  case_summary: "",
  trip_workspace_id: "",
  booking_workspace_id: "",
  ticket_workspace_id: "",
  emd_workspace_id: "",
  passenger_workspace_id: "",
  affected_segment_ref: "",
  residual_value_summary: "",
  penalty_summary: "",
  fare_difference_summary: "",
  service_fee_summary: "",
  refundability_summary: "",
  client_approval_required: false,
  supplier_communication_required: false,
}

export default function AfterSalesPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [filters, setFilters] = useState({ status: "", case_type: "" })
  const [selectedId, setSelectedId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const selected = useMemo(() => state?.items?.find((item) => item.id === selectedId) || state?.items?.[0] || null, [state, selectedId])

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const response = await apiGet(`/api/agencies/${context.agency.id}/after-sales${queryString(nextFilters)}`)
    setState({ ...context, ...response })
    if (!selectedId && response.items?.[0]?.id) setSelectedId(response.items[0].id)
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  function setField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function createCase(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    const payload = {
      case_type: form.case_type,
      case_priority: form.case_priority,
      case_title: form.case_title || `${formatType(form.case_type)} case`,
      case_summary: form.case_summary || undefined,
      trip_workspace_id: form.trip_workspace_id || undefined,
      booking_workspace_id: form.booking_workspace_id || undefined,
      ticket_workspace_ids: form.ticket_workspace_id ? [form.ticket_workspace_id] : [],
      emd_workspace_ids: form.emd_workspace_id ? [form.emd_workspace_id] : [],
      passenger_workspace_ids: form.passenger_workspace_id ? [form.passenger_workspace_id] : [],
      affected_segment_refs: form.affected_segment_ref ? [form.affected_segment_ref] : [],
      residual_value_summary: form.residual_value_summary || undefined,
      penalty_summary: form.penalty_summary || undefined,
      fare_difference_summary: form.fare_difference_summary || undefined,
      service_fee_summary: form.service_fee_summary || undefined,
      refundability_summary: form.refundability_summary || undefined,
      client_approval_required: form.client_approval_required,
      supplier_communication_required: form.supplier_communication_required,
      internal_message_json: { note: "Created from agency after-sales workspace." },
      generated_advice_json: { advice_status: "draft_metadata", execution_disabled: true },
      metadata: { ui_route: "/agency/after-sales" },
    }
    const result = await apiPost(`/api/agencies/${state.agency.id}/after-sales`, payload)
    setSelectedId(result.case.id)
    setMessage(`After-sales case ${result.case.case_reference} created as metadata only.`)
    setForm(defaultForm)
    await load()
  }

  async function updateStatus(caseStatus) {
    if (!selected?.id) return
    setError("")
    const result = await apiPut(`/api/agencies/${state.agency.id}/after-sales/${selected.id}`, { case_status: caseStatus })
    setSelectedId(result.case.id)
    setMessage(`Case status recorded as ${formatType(caseStatus)}.`)
    await load()
  }

  function applyFilters(next) {
    setFilters(next)
    load(next).catch((err) => setError(err.message))
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Servicing</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">After-Sales</h2>
              <p className="mt-1 text-sm text-slate-600">Unified servicing workflow metadata for changes, refunds, exchanges, claims, amendments, and disruptions. This workspace does not mutate tickets or EMDs, commit money, call providers, send messages, use AI, or automate execution.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Human authority final</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            <Metric label="Cases" value={state?.summary?.case_count || 0} />
            <Metric label="Open" value={state?.summary?.open_case_count || 0} />
            <Metric label="Client approvals" value={state?.summary?.requires_client_approval_count || 0} />
            <Metric label="Supplier contact" value={state?.summary?.requires_supplier_communication_count || 0} />
            <Metric label="Financial placeholders" value={state?.recent_financial_impacts?.length || 0} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createCase}>
              <h3 className="font-semibold text-slate-950">Open case metadata</h3>
              <SelectField label="Case type" value={form.case_type} onChange={(value) => setField("case_type", value)} options={caseTypes} />
              <SelectField label="Priority" value={form.case_priority} onChange={(value) => setField("case_priority", value)} options={["low", "normal", "high", "urgent", "critical"]} />
              <TextField label="Title" value={form.case_title} onChange={(value) => setField("case_title", value)} />
              <TextArea label="Summary" value={form.case_summary} onChange={(value) => setField("case_summary", value)} />
              <div className="grid gap-3 md:grid-cols-2">
                <TextField label="Trip workspace id" value={form.trip_workspace_id} onChange={(value) => setField("trip_workspace_id", value)} />
                <TextField label="Booking workspace id" value={form.booking_workspace_id} onChange={(value) => setField("booking_workspace_id", value)} />
                <TextField label="Ticket workspace id" value={form.ticket_workspace_id} onChange={(value) => setField("ticket_workspace_id", value)} />
                <TextField label="EMD workspace id" value={form.emd_workspace_id} onChange={(value) => setField("emd_workspace_id", value)} />
                <TextField label="Passenger workspace id" value={form.passenger_workspace_id} onChange={(value) => setField("passenger_workspace_id", value)} />
                <TextField label="Segment reference" value={form.affected_segment_ref} onChange={(value) => setField("affected_segment_ref", value)} />
              </div>
              <TextArea label="Financial estimate notes" value={form.refundability_summary} onChange={(value) => setField("refundability_summary", value)} />
              <div className="grid gap-2 text-sm text-slate-700">
                <label className="flex items-center gap-2"><input type="checkbox" checked={form.client_approval_required} onChange={(event) => setField("client_approval_required", event.target.checked)} /> Client approval required</label>
                <label className="flex items-center gap-2"><input type="checkbox" checked={form.supplier_communication_required} onChange={(event) => setField("supplier_communication_required", event.target.checked)} /> Supplier communication required</label>
              </div>
              <button className="aa-primary-action w-full rounded-md px-3 py-2 text-sm font-semibold" type="submit">Create case metadata</button>
            </form>

            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-950">Case list</h3>
                  <div className="grid gap-2 md:grid-cols-2">
                    <SelectField label="Status" value={filters.status} onChange={(value) => applyFilters({ ...filters, status: value })} options={["", "opened", "assessing", "awaiting_approval", "processing", "resolved", "cancelled"]} />
                    <SelectField label="Type" value={filters.case_type} onChange={(value) => applyFilters({ ...filters, case_type: value })} options={["", ...caseTypes]} />
                  </div>
                </div>
                {!state?.items?.length ? <EmptyState title="No after-sales cases" body="Create metadata for a servicing, claim, refund, exchange, amendment, or disruption case." /> : (
                  <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                    {state.items.map((item) => (
                      <button className={`grid w-full gap-3 px-4 py-3 text-left text-sm hover:bg-slate-50 lg:grid-cols-[1.2fr_0.8fr_0.8fr_0.7fr] ${item.id === selected?.id ? "bg-blue-50" : ""}`} key={item.id} type="button" onClick={() => setSelectedId(item.id)}>
                        <span className="font-semibold text-slate-950">{item.case_reference}</span>
                        <span>{formatType(item.case_type)}</span>
                        <span>{formatType(item.case_status)}</span>
                        <span>{formatType(item.case_priority)}</span>
                      </button>
                    ))}
                  </div>
                )}
              </section>

              <CaseWorkspace selected={selected} onUpdateStatus={updateStatus} />
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function CaseWorkspace({ selected, onUpdateStatus }) {
  if (!selected) return <EmptyState title="No case selected" body="Select a case to review after-sales workspace metadata." />
  return (
    <section className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{formatType(selected.case_status)}</p>
            <h3 className="mt-1 font-semibold text-slate-950">{selected.case_title}</h3>
            <p className="mt-1 text-sm text-slate-600">{selected.case_summary || "No summary recorded."}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {["assessing", "awaiting_approval", "processing", "resolved"].map((statusValue) => (
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700" key={statusValue} type="button" onClick={() => onUpdateStatus(statusValue)}>{formatType(statusValue)}</button>
            ))}
          </div>
        </div>
      </div>

      <Card title="Affected records">
        <CompactTable rows={selected.items || []} columns={["item_type", "source_entity_type", "source_entity_id", "impact_status"]} />
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Financial estimate">
          <CompactTable rows={selected.financial_impacts || []} columns={["impact_type", "estimate_status", "direction", "placeholder_notes"]} />
        </Card>
        <Card title="Decisions and approvals">
          <CompactTable rows={selected.decisions || []} columns={["decision_type", "decision_status", "client_approval_status", "decision_summary"]} />
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Communications">
          <CompactTable rows={selected.communications || []} columns={["communication_type", "audience", "channel", "summary"]} />
        </Card>
        <Card title="Resolution">
          <CompactTable rows={selected.resolutions || []} columns={["resolution_type", "resolution_status", "resolution_summary"]} />
        </Card>
      </div>
      <Card title="Documents, tasks, deadlines, workflow">
        <div className="grid gap-3 text-sm md:grid-cols-3">
          <Info label="Documents" value={(selected.document_workspace_ids || []).join(", ") || "Not linked"} />
          <Info label="Tasks" value={(selected.task_ids || []).join(", ") || "No generated tasks"} />
          <Info label="Deadlines" value={(selected.deadline_ids || []).join(", ") || "Not set"} />
          <Info label="Work items" value={(selected.work_item_ids || []).join(", ") || "Not set"} />
          <Info label="Workflow" value={selected.workflow_instance_id || "Not linked"} />
          <Info label="Timeline" value={(selected.timeline_entry_ids || []).join(", ") || "Not recorded"} />
        </div>
      </Card>
      <Card title="Coupon and impact scope">
        <JsonPreview label="Coupon status awareness" value={selected.coupon_status_snapshot_json} />
        <JsonPreview label="Impact scope" value={selected.impact_scope_json} />
      </Card>
    </section>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function Card({ title, children }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><div className="mt-4">{children}</div></section>
}

function Info({ label, value }) {
  return <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 break-words text-slate-800">{value}</p></div>
}

function CompactTable({ rows, columns }) {
  if (!rows?.length) return <EmptyState title="No metadata" body="After-sales child metadata will appear here." />
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
            {columns.map((column) => <th className="px-3 py-2" key={column}>{formatType(column)}</th>)}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={row.id}>
              {columns.map((column) => <td className="max-w-xs px-3 py-2 text-slate-700" key={column}>{formatValue(row[column])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function JsonPreview({ label, value }) {
  return <div className="mt-3 rounded-md bg-slate-950 p-3 text-xs text-slate-100"><p className="mb-2 font-semibold text-blue-200">{label}</p><pre className="max-h-48 overflow-auto whitespace-pre-wrap">{JSON.stringify(value || {}, null, 2)}</pre></div>
}

function TextField({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function TextArea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function SelectField({ label, value, onChange, options }) {
  const normalized = options.map((option) => Array.isArray(option) ? option : [option, option ? formatType(option) : "All"])
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{normalized.map(([option, text]) => <option value={option} key={option}>{text}</option>)}</select></label>
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
