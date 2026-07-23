import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import FilterBar from "../../components/FilterBar"
import OperationalAlert from "../../components/OperationalAlert"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
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
    const [workspaces, summary, renderJobs, serviceResponse] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/document-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/document-workspaces/summary`),
      apiGet(`/api/agencies/${context.agency.id}/documents/render-jobs`),
      nextFilters.related_service
        ? apiGet(`/api/agencies/${context.agency.id}/passenger-services/${encodeURIComponent(nextFilters.related_service)}`)
        : Promise.resolve({ service: null }),
    ])
    const bookingWorkspaceId = nextFilters.related_service
      ? workspaces.items?.find((item) => item.booking_workspace_id)?.booking_workspace_id || serviceResponse.service?.booking_workspace_id
      : null
    const invoices = bookingWorkspaceId ? await apiGet(`/api/agencies/${context.agency.id}/invoices?booking_workspace_id=${encodeURIComponent(bookingWorkspaceId)}`) : { items: [] }
    setState({
      ...context,
      workspaces: workspaces.items || [],
      summary: workspaces.summary || summary.summary || {},
      renderJobs: renderJobs.items || [],
      invoices: invoices.items || [],
      service: serviceResponse.service || null,
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
      setMessage(`Document review saved as ${formatType(reconcile.document_status)}. Creating a document does not verify the travel requirement.`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function createOrOpenInvoice() {
    const existing = state?.invoices?.[0]
    if (existing) {
      window.location.href = `/agency/invoices/${existing.id}`
      return
    }
    if (!bookingWorkspaceId) return
    setError("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/${bookingWorkspaceId}/invoice`)
      window.location.href = `/agency/invoices/${result.invoice.id}`
    } catch (err) {
      setError(err.message)
    }
  }

  async function createDocumentRequirement() {
    if (!filters.related_service) return
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/passenger-services/${encodeURIComponent(filters.related_service)}/document-requirement`)
      setMessage(result.created ? "Required document added to the passenger service." : "Existing required document opened.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const sourceDocument = state?.workspaces?.find((item) => item.booking_workspace_id) || state?.workspaces?.[0]
  const bookingWorkspaceId = filters.related_service ? sourceDocument?.booking_workspace_id || state?.service?.booking_workspace_id : null
  const documentsVerified = Boolean(state?.workspaces?.length) && state.workspaces.every((item) => !item.required_for_travel || ["verified", "not_required", "waived"].includes(item.document_status))

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <PageHeader
            eyebrow="Travel documents"
            title="Documents"
            description="See what each passenger needs, what has been received, and what still requires review before travel."
          />

          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Passenger services", href: filters.related_service ? `/agency/passenger-services?service_id=${encodeURIComponent(filters.related_service)}` : "/agency/passenger-services" }, { label: "Documents", href: "/agency/document-workspaces" }]}
            currentLabel={sourceDocument?.document_display_name || sourceDocument?.document_reference || "Document"}
            status={sourceDocument?.document_status || "unknown"}
            validation={!filters.related_service
              ? { state: "blocked", label: "Passenger service required", reason: "Open Documents from a passenger service to continue." }
              : !sourceDocument
              ? { state: "blocked", label: "Required document missing", reason: "Add the required document from the passenger service." }
              : documentsVerified ? { state: "ready", label: "Required documents reviewed", reason: "Finance can continue without documents changing financial state." }
                : { state: "warning", label: "Document review incomplete", reason: "Unverified requirements remain visible; an authorized operator decides whether finance may continue." }}
            previous={filters.related_service ? { label: "Previous: passenger service", href: `/agency/passenger-services?service_id=${encodeURIComponent(filters.related_service)}` } : { label: "Passenger services", href: "/agency/passenger-services" }}
            next={!sourceDocument
              ? { label: "Create document requirement", onClick: createDocumentRequirement, enabled: Boolean(filters.related_service), reason: "A canonical passenger-service context is required." }
              : { label: state?.invoices?.[0] ? "Continue to finance" : "Create linked invoice", onClick: createOrOpenInvoice, enabled: Boolean(bookingWorkspaceId), reason: "A canonical booking workspace link is required before invoice creation." }}
            relatedRecords={[
              { label: "Passenger service", value: filters.related_service || sourceDocument?.passenger_service_request_id || "none" },
              { label: "Booking", value: sourceDocument?.booking_reference || bookingWorkspaceId || "none", href: bookingWorkspaceId ? `/agency/booking-workspaces/${bookingWorkspaceId}` : undefined },
              { label: "Invoice", value: state?.invoices?.[0]?.invoice_number || "none", href: state?.invoices?.[0] ? `/agency/invoices/${state.invoices[0].id}` : undefined },
            ]}
          />

          {error ? <OperationalAlert title="The document update could not be saved" tone="error">{error}</OperationalAlert> : null}
          {message ? <OperationalAlert title="Document updated" tone="success">{message}</OperationalAlert> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <form className="rounded-lg border border-slate-200 bg-white p-5" onSubmit={reconcileOutput}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div><h3 className="font-semibold text-slate-950">Review a prepared document</h3><p className="mt-1 text-sm text-slate-600">Match the prepared document to its requirement, then record the review outcome.</p></div>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/documents">Prepare documents</a>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-5">
              <SelectField label="Requirement" value={reconcile.workspace_id} onChange={(value) => setReconcile({ ...reconcile, workspace_id: value })} options={(state?.workspaces || []).map((item) => [item.id, item.document_display_name || item.document_reference])} placeholder="Select requirement" />
              <SelectField label="Prepared document" value={reconcile.render_job_id} onChange={(value) => setReconcile({ ...reconcile, render_job_id: value })} options={(state?.renderJobs || []).map((item) => [item.id, `${formatType(item.document_type)} · ${item.source_context_id || "Prepared document"}`])} placeholder="Select document" />
              <SelectField label="Review outcome" value={reconcile.document_status} onChange={(value) => setReconcile({ ...reconcile, document_status: value })} options={["requested", "received", "generated", "under_review", "verified", "rejected", "expired", "not_required", "unknown"].map((item) => [item, formatType(item)])} />
              <Field label="Rejection reason" value={reconcile.rejection_reason} onChange={(value) => setReconcile({ ...reconcile, rejection_reason: value })} />
              <Field label="Review notes" value={reconcile.review_notes} onChange={(value) => setReconcile({ ...reconcile, review_notes: value })} />
            </div>
            <button className="aa-primary-action mt-4 rounded-md px-3 py-2 text-sm font-semibold" type="submit" disabled={!reconcile.workspace_id || !reconcile.render_job_id}>Record output review</button>
          </form>

          <FilterBar onClear={() => setFilters({ ...defaultFilters })} resultCount={state?.workspaces?.length || 0} title="Filter documents">
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
              <SelectField label="Type" value={filters.document_type} onChange={(value) => setFilters({ ...filters, document_type: value })} options={documentTypes.map((item) => [item, formatType(item)])} placeholder="All types" />
              <SelectField label="Status" value={filters.document_status} onChange={(value) => setFilters({ ...filters, document_status: value })} options={documentStatuses.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Booking" value={filters.booking_reference} onChange={(value) => setFilters({ ...filters, booking_reference: value })} />
              {filters.related_service
                ? <ContextValue label="Service context" value={state?.service?.service_label || state?.service?.service_type || filters.related_service} />
                : <Field label="Service" value={filters.related_service} onChange={(value) => setFilters({ ...filters, related_service: value })} />}
              <SelectField label="Travel required" value={filters.required_for_travel} onChange={(value) => setFilters({ ...filters, required_for_travel: value })} options={[["true", "Required"], ["false", "Not required"]]} placeholder="Any" />
              <Field label="Verification" value={filters.verification_status} onChange={(value) => setFilters({ ...filters, verification_status: value })} />
              <Field label="Deadline" type="date" value={filters.deadline} onChange={(value) => setFilters({ ...filters, deadline: value })} />
            </div>
          </FilterBar>

          {state?.workspaces?.length ? <DocumentTable workspaces={state.workspaces} /> : <EmptyState title="No documents match these filters" body="Clear the filters or add a required document from a passenger service." />}
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
            <th className="px-4 py-3">Files and packages</th>
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
                <p className="mt-1 text-xs text-slate-500">{workspace.file_name || "No file attached"}</p>
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

function ContextValue({ label, value }) {
  return (
    <div className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <span className="min-h-10 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700">{value}</span>
    </div>
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
