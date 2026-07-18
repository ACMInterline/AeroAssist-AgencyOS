import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const documentTypes = ["itinerary", "booking_confirmation", "ticket_receipt", "emd_receipt", "invoice", "voucher", "medif", "medical_certificate", "veterinary_certificate", "pet_passport", "battery_declaration", "mobility_aid_form", "unaccompanied_minor_form", "consent_form", "visa_document", "passport_copy", "assistance_confirmation", "airline_approval", "airport_handling_confirmation", "service_instruction", "other"]
const documentStatuses = ["draft_metadata", "required", "requested", "received", "generated", "under_review", "verified", "rejected", "expired", "waived", "not_required", "unknown", "archived"]

const defaultFilters = {
  document_type: "",
  document_status: "",
  passenger: "",
  booking_reference: "",
  related_service: "",
  required_for_travel: "",
  verification_status: "",
  deadline: "",
}

export default function DocumentWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(() => ({ ...defaultFilters, related_service: new URLSearchParams(window.location.search).get("related_service") || "" }))
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [reconcile, setReconcile] = useState({ workspace_id: "", render_job_id: "", document_status: "generated", rejection_reason: "", review_notes: "" })

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [workspaces, summary, renderJobs] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/document-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/document-workspaces/summary`),
      apiGet(`/api/agencies/${context.agency.id}/documents/render-jobs`),
    ])
    setState({
      ...context,
      workspaces: workspaces.items || [],
      summary: workspaces.summary || summary.summary || {},
      renderJobs: renderJobs.items || [],
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.document_type, filters.document_status, filters.passenger, filters.booking_reference, filters.related_service, filters.required_for_travel, filters.verification_status, filters.deadline])

  const metrics = [
    ["Documents", state?.workspaces?.length || 0],
    ["Required", state?.summary?.by_document_status?.required || 0],
    ["Verified", state?.summary?.by_document_status?.verified || 0],
    ["Rejected", state?.summary?.by_document_status?.rejected || 0],
  ]

  async function reconcileOutput(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/document-workspaces/${reconcile.workspace_id}/reconcile-output`, {
        render_job_id: reconcile.render_job_id,
        document_status: reconcile.document_status,
        rejection_reason: reconcile.rejection_reason || undefined,
        review_notes: reconcile.review_notes || undefined,
      })
      setMessage(`Document output reconciled as ${formatType(reconcile.document_status)}. Rendering alone did not verify it.`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Documents</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Documents</h2>
              <p className="mt-1 text-sm text-slate-600">Operational document requirements and explicit output review. Rendering or attaching output does not verify a requirement; an authorized operator records generated, review, verification, rejection, expiry, or unknown state separately.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Explicit review</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No public links</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <form className="rounded-lg border border-slate-200 bg-white p-5" onSubmit={reconcileOutput}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div><h3 className="font-semibold text-slate-950">Reconcile document output</h3><p className="mt-1 text-sm text-slate-600">Choose an existing requirement and render job. Verification requires this explicit operator action and is recorded with actor and time.</p></div>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/documents">Open document rendering</a>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-5">
              <SelectField label="Requirement" value={reconcile.workspace_id} onChange={(value) => setReconcile({ ...reconcile, workspace_id: value })} options={(state?.workspaces || []).map((item) => [item.id, item.document_display_name || item.document_reference])} placeholder="Select requirement" />
              <SelectField label="Render job" value={reconcile.render_job_id} onChange={(value) => setReconcile({ ...reconcile, render_job_id: value })} options={(state?.renderJobs || []).map((item) => [item.id, `${formatType(item.document_type)} · ${item.source_context_id || item.id}`])} placeholder="Select output" />
              <SelectField label="Review state" value={reconcile.document_status} onChange={(value) => setReconcile({ ...reconcile, document_status: value })} options={["requested", "received", "generated", "under_review", "verified", "rejected", "expired", "not_required", "unknown"].map((item) => [item, formatType(item)])} />
              <Field label="Rejection reason" value={reconcile.rejection_reason} onChange={(value) => setReconcile({ ...reconcile, rejection_reason: value })} />
              <Field label="Review notes" value={reconcile.review_notes} onChange={(value) => setReconcile({ ...reconcile, review_notes: value })} />
            </div>
            <button className="aa-primary-action mt-4 rounded-md px-3 py-2 text-sm font-semibold" type="submit" disabled={!reconcile.workspace_id || !reconcile.render_job_id}>Record output review</button>
          </form>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Document filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-8">
              <SelectField label="Type" value={filters.document_type} onChange={(value) => setFilters({ ...filters, document_type: value })} options={documentTypes.map((item) => [item, formatType(item)])} placeholder="All types" />
              <SelectField label="Status" value={filters.document_status} onChange={(value) => setFilters({ ...filters, document_status: value })} options={documentStatuses.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Booking" value={filters.booking_reference} onChange={(value) => setFilters({ ...filters, booking_reference: value })} />
              <Field label="Service" value={filters.related_service} onChange={(value) => setFilters({ ...filters, related_service: value })} />
              <SelectField label="Travel required" value={filters.required_for_travel} onChange={(value) => setFilters({ ...filters, required_for_travel: value })} options={[["true", "Required"], ["false", "Not required"]]} placeholder="Any" />
              <Field label="Verification" value={filters.verification_status} onChange={(value) => setFilters({ ...filters, verification_status: value })} />
              <Field label="Deadline" type="date" value={filters.deadline} onChange={(value) => setFilters({ ...filters, deadline: value })} />
            </div>
          </section>

          {state?.workspaces?.length ? <DocumentTable workspaces={state.workspaces} /> : <EmptyState title="No document workspaces" body="Operational document metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function DocumentTable({ workspaces }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Document</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Passenger</th>
            <th className="px-4 py-3">Related booking</th>
            <th className="px-4 py-3">Related service</th>
            <th className="px-4 py-3">Requirement</th>
            <th className="px-4 py-3">Verification</th>
            <th className="px-4 py-3">Storage and records</th>
            <th className="px-4 py-3">Visibility</th>
            <th className="px-4 py-3">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {workspaces.map((workspace) => (
            <tr key={workspace.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{workspace.document_display_name || workspace.document_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{workspace.document_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{workspace.file_name || "No file metadata"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatType(workspace.document_type)}</p>
                <p className="mt-1">Category: {workspace.document_category || "Unset"}</p>
                <p className="mt-1">Status: {formatType(workspace.document_status)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{workspace.passenger_name || "Passenger unset"}</p>
                <p className="mt-1">Passenger ID: {workspace.passenger_id || "Unset"}</p>
                <p className="mt-1">Workspace: {workspace.passenger_workspace_id || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Booking: {workspace.booking_reference || "Unset"}</p>
                <p className="mt-1">PNR: {workspace.airline_pnr || "Unset"}</p>
                <p className="mt-1">GDS: {workspace.gds_record_locator || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Service: {workspace.related_service_requirement || "Unset"}</p>
                <p className="mt-1">Ticket: {workspace.related_ticket_number || workspace.ticket_workspace_id || "Unset"}</p>
                <p className="mt-1">EMD: {workspace.related_emd_number || workspace.emd_workspace_id || "Unset"}</p>
                <p className="mt-1">SSR / OSI: {workspace.related_ssr_code || workspace.ssr_osi_workspace_id || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Travel: {workspace.required_for_travel ? "Required" : "Not required"}</p>
                <p className="mt-1">Airline: {workspace.required_by_airline ? "Required" : "No"}</p>
                <p className="mt-1">Airport: {workspace.required_by_airport ? "Required" : "No"}</p>
                <p className="mt-1">Authority: {workspace.required_by_authority ? "Required" : "No"}</p>
                <p className="mt-1">Deadline: {formatDate(workspace.requirement_deadline)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <StatusBadge status={workspace.verification_status || workspace.document_status} />
                <p className="mt-2">Received: {workspace.received_status || "Unset"}</p>
                <p className="mt-1">Validity: {formatDate(workspace.validity_start_date)} to {formatDate(workspace.validity_end_date)}</p>
                <p className="mt-1">Authority: {workspace.issuing_authority || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Storage: {workspace.storage_reference || "Unset"}</p>
                <ReferenceLine label="Packages" items={workspace.document_package_ids} />
                <ReferenceLine label="Render jobs" items={workspace.render_job_ids} />
                <ReferenceLine label="Rendered outputs" items={workspace.rendered_document_ids} />
                <ReferenceLine label="Share records" items={workspace.share_record_ids} />
                <ReferenceLine label="AOIE" items={workspace.operational_intelligence_record_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Customer: {workspace.customer_visible ? "Visible" : "Hidden"}</p>
                <p className="mt-1">Airline: {workspace.airline_visible ? "Visible" : "Hidden"}</p>
                <p className="mt-1">Internal only: {workspace.internal_only ? "Yes" : "No"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{workspace.operational_notes || "No operational notes"}</p>
                <p className="mt-1">Missing: {workspace.missing_reason || "None"}</p>
                <p className="mt-1">Rejected: {workspace.rejection_reason || "None"}</p>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
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

function ReferenceLine({ label, items }) {
  return <p className="mt-1"><span className="font-semibold text-slate-700">{label}:</span> {formatList(items)}</p>
}

function StatusBadge({ status }) {
  return <span className="inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{formatType(status || "draft_metadata")}</span>
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

function formatDate(value) {
  return value ? String(value).slice(0, 10) : "Unset"
}

function formatList(items) {
  return (items || []).length ? items.join(", ") : "None"
}
