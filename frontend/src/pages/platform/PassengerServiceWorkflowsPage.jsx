import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const workflowStages = ["passenger_registered", "requirements_collected", "service_requirements_analysed", "airline_evaluation", "offer_preparation", "offer_accepted", "booking_ready", "booking_completed", "ticket_ready", "ticket_completed", "emd_required", "emd_completed", "documents_pending", "documents_complete", "travel_ready", "travel_completed", "case_closed"]
const readinessStates = ["ready", "waiting_for_customer", "waiting_for_airline", "waiting_for_documents", "waiting_for_payment", "waiting_for_approval", "waiting_for_emd", "blocked", "completed"]

const defaultFilters = {
  agency_id: "",
  stage: "",
  readiness: "",
  passenger: "",
  airline: "",
  priority: "",
  assigned_agent: "",
}

export default function PlatformPassengerServiceWorkflowsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, workflows] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/passenger-service-workflows${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      workflows: workflows.items || [],
      summary: workflows.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.stage, filters.readiness, filters.passenger, filters.airline, filters.priority, filters.assigned_agent])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const metrics = [
    ["Workflows", state?.workflows?.length || 0],
    ["Blocking requirements", state?.summary?.blocking_requirement_count || 0],
    ["Completed requirements", state?.summary?.completed_requirement_count || 0],
    ["AOIE references", state?.summary?.recommendation_pack_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Passenger Services</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Passenger Service Workflows</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only workflow engine records that coordinate passenger, request, trip, booking, ticket, EMD, SSR / OSI, document, timeline, and future AOIE references without workflow execution, AI decisions, workers, airline APIs, GDS/NDC connectivity, automatic approvals, ticketing, EMD issuance, or messaging.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No automation</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No AI decisions</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Workflow filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Workflow stage" value={filters.stage} onChange={(value) => setFilters({ ...filters, stage: value })} options={workflowStages.map((item) => [item, formatType(item)])} placeholder="All stages" />
              <SelectField label="Readiness" value={filters.readiness} onChange={(value) => setFilters({ ...filters, readiness: value })} options={readinessStates.map((item) => [item, formatType(item)])} placeholder="All readiness" />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
              <Field label="Assigned agent" value={filters.assigned_agent} onChange={(value) => setFilters({ ...filters, assigned_agent: value })} />
            </div>
          </section>

          {state?.workflows?.length ? <WorkflowList workflows={state.workflows} showAgency /> : <EmptyState title="No passenger service workflows" body="Workflow coordination metadata will appear here after platform records are created." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function WorkflowList({ workflows, showAgency = false }) {
  return (
    <section className="space-y-3">
      {workflows.map((workflow) => (
        <details key={workflow.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{workflow.workflow_display_name || workflow.workflow_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{formatType(workflow.current_stage)} · {formatType(workflow.readiness_status)} · {workflow.workflow_status || "status unset"}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{workflow.agency_name || workflow.agency_id}</p> : null}
                <p className="mt-1">Priority: {workflow.workflow_priority || "Unset"}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Agent: {workflow.responsible_agent || "Unset"}</p>
                <p className="mt-1">Airline: {workflow.related_airline || "Unset"}</p>
              </div>
            </div>
          </summary>
          <div className="mt-4 grid gap-4 text-xs text-slate-600 lg:grid-cols-4">
            <DetailBlock title="Workflow detail" lines={[
              `Type: ${workflow.workflow_type || "Unset"}`,
              `Version: ${workflow.workflow_version || "Unset"}`,
              `Previous: ${formatType(workflow.previous_stage)}`,
              `Current: ${formatType(workflow.current_stage)}`,
              `Next: ${formatType(workflow.next_stage)}`,
              `Readiness: ${formatType(workflow.readiness_status)}`,
            ]} />
            <DetailBlock title="Requirements" lines={[
              `Blocking: ${formatList(workflow.blocking_requirements)}`,
              `Completed: ${formatList(workflow.completed_requirements)}`,
              `Responsible team: ${workflow.responsible_team || "Unset"}`,
              `Responsible agent: ${workflow.responsible_agent || "Unset"}`,
              `AOIE pack: ${workflow.recommendation_pack_reference || "Unset"}`,
            ]} />
            <DetailBlock title="Linked workspaces" lines={[
              `Passenger: ${workflow.passenger_workspace_id || "Unset"}`,
              `Request: ${workflow.travel_request_workspace_id || "Unset"}`,
              `Trip: ${workflow.trip_workspace_id || "Unset"}`,
              `Booking: ${workflow.booking_workspace_id || "Unset"}`,
              `Ticket: ${workflow.ticket_workspace_id || "Unset"}`,
              `EMD: ${workflow.emd_workspace_id || "Unset"}`,
              `SSR / OSI: ${workflow.ssr_osi_workspace_id || "Unset"}`,
              `Document: ${workflow.document_workspace_id || "Unset"}`,
              `Timeline: ${workflow.timeline_workspace_id || "Unset"}`,
            ]} />
            <DetailBlock title="Dates and notes" lines={[
              `Started: ${formatDateTime(workflow.started_at)}`,
              `Completed: ${formatDateTime(workflow.completed_at)}`,
              `Last updated: ${formatDateTime(workflow.last_updated)}`,
              `Notes: ${workflow.operational_notes || "Unset"}`,
            ]} />
          </div>
        </details>
      ))}
    </section>
  )
}

function DetailBlock({ title, lines }) {
  return (
    <div>
      <p className="font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <div className="mt-2 space-y-1">
        {lines.map((line) => <p key={line}>{line}</p>)}
      </div>
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Field({ label, value, onChange, type = "text" }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input type={type} className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function SelectField({ label, value, onChange, options, placeholder }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
  )
}

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatType(value) {
  return String(value || "unset").replaceAll("_", " ")
}

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}

function formatList(items) {
  return (items || []).length ? items.join(", ") : "None"
}
