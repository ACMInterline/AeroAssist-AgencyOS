import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const documentTypes = ["itinerary", "booking_confirmation", "ticket_receipt", "emd_receipt", "invoice", "voucher", "medif", "medical_certificate", "veterinary_certificate", "pet_passport", "battery_declaration", "mobility_aid_form", "unaccompanied_minor_form", "consent_form", "visa_document", "passport_copy", "assistance_confirmation", "airline_approval", "airport_handling_confirmation", "service_instruction", "other"]
const documentStatuses = ["draft_metadata", "required", "requested", "received", "under_review", "verified", "rejected", "expired", "waived", "not_required", "archived"]

const defaultFilters = {
  agency_id: "",
  document_type: "",
  document_status: "",
  passenger: "",
  booking_reference: "",
  related_service: "",
  required_for_travel: "",
  verification_status: "",
  deadline: "",
}

export default function PlatformDocumentWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, workspaces] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/document-workspaces${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      workspaces: workspaces.items || [],
      summary: workspaces.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.document_type, filters.document_status, filters.passenger, filters.booking_reference, filters.related_service, filters.required_for_travel, filters.verification_status, filters.deadline])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const metrics = [
    ["Documents", state?.workspaces?.length || 0],
    ["Required", state?.summary?.by_document_status?.required || 0],
    ["Verified", state?.summary?.by_document_status?.verified || 0],
    ["Rejected", state?.summary?.by_document_status?.rejected || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Document Workspaces</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only operational document workspace records. These link passengers, requests, trips, bookings, tickets, EMDs, SSR / OSI operations, packages, render jobs, shares, and operational intelligence references without delivery, e-signature, public share links, PDF generation, payment or invoice generation, external storage integrations, workers, or AI document generation.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No delivery</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No duplicate render layer</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Document workspace filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-9">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
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

          {state?.workspaces?.length ? <DocumentTable workspaces={state.workspaces} showAgency /> : <EmptyState title="No document workspaces" body="Operational document workspace metadata will appear here after platform records are created." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function DocumentTable({ workspaces, showAgency = false }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Document reference</th>
            {showAgency ? <th className="px-4 py-3">Agency</th> : null}
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Passenger</th>
            <th className="px-4 py-3">Related records</th>
            <th className="px-4 py-3">Requirement</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Storage</th>
            <th className="px-4 py-3">Visibility</th>
            <th className="px-4 py-3">Operational notes</th>
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
              {showAgency ? <td className="px-4 py-3 align-top text-xs text-slate-600">{workspace.agency_name || workspace.agency_id}</td> : null}
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatType(workspace.document_type)}</p>
                <p className="mt-1">Category: {workspace.document_category || "Unset"}</p>
                <p className="mt-1">{workspace.document_description || "Description unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{workspace.passenger_name || "Passenger unset"}</p>
                <p className="mt-1">Passenger ID: {workspace.passenger_id || "Unset"}</p>
                <p className="mt-1">Workspace: {workspace.passenger_workspace_id || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Booking: {workspace.booking_reference || "Unset"}</p>
                <p className="mt-1">PNR: {workspace.airline_pnr || "Unset"} / {workspace.gds_record_locator || "Unset"}</p>
                <p className="mt-1">Ticket: {workspace.related_ticket_number || workspace.ticket_workspace_id || "Unset"}</p>
                <p className="mt-1">EMD: {workspace.related_emd_number || workspace.emd_workspace_id || "Unset"}</p>
                <p className="mt-1">SSR / OSI: {workspace.related_ssr_code || workspace.ssr_osi_workspace_id || "Unset"}</p>
                <ReferenceLine label="AOIE" items={workspace.operational_intelligence_record_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Travel: {workspace.required_for_travel ? "Required" : "Not required"}</p>
                <p className="mt-1">Airline: {workspace.required_by_airline ? "Required" : "No"}</p>
                <p className="mt-1">Airport: {workspace.required_by_airport ? "Required" : "No"}</p>
                <p className="mt-1">Authority: {workspace.required_by_authority ? "Required" : "No"}</p>
                <p className="mt-1">Deadline: {formatDate(workspace.requirement_deadline)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <StatusBadge status={workspace.document_status} />
                <p className="mt-2">Received: {workspace.received_status || "Unset"}</p>
                <p className="mt-1">Verification: {workspace.verification_status || "Unset"}</p>
                <p className="mt-1">Validity: {formatDate(workspace.validity_start_date)} to {formatDate(workspace.validity_end_date)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Storage: {workspace.storage_reference || "Unset"}</p>
                <p className="mt-1">Type: {workspace.file_type || "Unset"}</p>
                <p className="mt-1">Size: {workspace.file_size || "Unset"}</p>
                <ReferenceLine label="Packages" items={workspace.document_package_ids} />
                <ReferenceLine label="Render jobs" items={workspace.render_job_ids} />
                <ReferenceLine label="Share records" items={workspace.share_record_ids} />
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
