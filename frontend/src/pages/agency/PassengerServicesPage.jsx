import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const needCategories = ["mobility", "medical", "visual_impairment", "hearing_impairment", "cognitive", "unaccompanied_minor", "infant", "pet", "assistance_animal", "sports_equipment", "musical_instrument", "oversized_baggage", "dangerous_goods", "religious", "dietary", "seating", "security", "immigration", "documentation", "vip", "disruption", "other"]
const approvalStatuses = ["not_required", "pending", "approved", "rejected", "expired"]
const readinessStatuses = ["ready", "pending", "awaiting_airline", "awaiting_documents", "awaiting_payment", "awaiting_emd", "awaiting_medif", "awaiting_customer", "blocked"]
const initialParams = new URLSearchParams(window.location.search)
const incomingTicketRecordId = initialParams.get("ticket_record_id") || ""
const incomingEmdRecordId = initialParams.get("emd_record_id") || ""
const incomingBookingWorkspaceId = initialParams.get("booking_workspace_id") || ""
const incomingBookingRecordId = initialParams.get("booking_record_id") || ""

const defaultFilters = {
  need_category: "",
  airline: "",
  approval_status: "",
  readiness_status: "",
  passenger: "",
  priority: "",
  rfic: "",
  rfisc: "",
}

const defaultFulfilment = {
  booking_workspace_id: "", booking_record_id: "", ticket_record_ids: [], ticket_coupon_ids: [],
  emd_record_ids: [], emd_coupon_ids: [], document_workspace_ids: [], ssr_osi_workspace_id: "",
  airline_confirmation_status: "unknown", airline_confirmation_evidence_reference: "",
  airport_handling_confirmation_status: "unknown", airport_handling_evidence_reference: "",
  external_manual_status: "unknown", fulfilment_result: "unknown", mismatches: "", next_action: "",
}

export default function PassengerServicesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [selectedId, setSelectedId] = useState(initialParams.get("service_id") || "")
  const [fulfilment, setFulfilment] = useState(defaultFulfilment)
  const [linkOptions, setLinkOptions] = useState({})
  const selected = useMemo(
    () => state?.serviceCases?.find((item) => item.id === selectedId) || (!selectedId ? state?.serviceCases?.[0] : null) || null,
    [state, selectedId],
  )

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [workspaces, summary, serviceCases] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/ssr-osi-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/ssr-osi-workspaces/summary`),
      apiGet(`/api/agencies/${context.agency.id}/passenger-services`),
    ])
    setState({
      ...context,
      workspaces: workspaces.items || [],
      summary: workspaces.summary || summary.summary || {},
      serviceCases: serviceCases.items || [],
    })
    if (!selectedId && serviceCases.items?.[0]?.id) setSelectedId(serviceCases.items[0].id)
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.need_category, filters.airline, filters.approval_status, filters.readiness_status, filters.passenger, filters.priority, filters.rfic, filters.rfisc])

  useEffect(() => {
    if (!state?.agency?.id || !selected?.id) return
    setFulfilment({
      ...defaultFulfilment,
      booking_workspace_id: selected.booking_workspace_id || incomingBookingWorkspaceId,
      booking_record_id: selected.booking_record_id || incomingBookingRecordId,
      ticket_record_ids: uniqueValues([...(selected.ticket_record_ids || []), incomingTicketRecordId]),
      ticket_coupon_ids: selected.ticket_coupon_ids || [],
      emd_record_ids: uniqueValues([...(selected.emd_record_ids || []), incomingEmdRecordId]),
      emd_coupon_ids: selected.emd_coupon_ids || [],
      document_workspace_ids: selected.document_workspace_ids || [],
      ssr_osi_workspace_id: selected.ssr_osi_workspace_id || "",
      airline_confirmation_status: selected.airline_confirmation_status || "unknown",
      airline_confirmation_evidence_reference: selected.airline_confirmation_evidence_reference || "",
      airport_handling_confirmation_status: selected.airport_handling_confirmation_status || "unknown",
      airport_handling_evidence_reference: selected.airport_handling_evidence_reference || "",
      external_manual_status: selected.external_manual_status || "unknown",
      fulfilment_result: selected.fulfilment_result || "unknown",
      next_action: selected.next_action || "",
    })
    apiGet(`/api/agencies/${state.agency.id}/passenger-services/${selected.id}/link-options`)
      .then((response) => setLinkOptions(response.items || {}))
      .catch((err) => setError(err.message))
  }, [state?.agency?.id, selected?.id])

  const metrics = [
    ["Service cases", state?.serviceCases?.length || 0],
    ["Ready", state?.summary?.by_readiness_status?.ready || 0],
    ["Awaiting airline", state?.summary?.by_readiness_status?.awaiting_airline || 0],
    ["Blocked", state?.summary?.by_readiness_status?.blocked || 0],
  ]

  function setFulfilmentField(field, value) {
    setFulfilment((current) => ({ ...current, [field]: value }))
  }

  async function recordAction(action, payload) {
    if (!selected?.id) return
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/passenger-services/${selected.id}/fulfilment/${action}`, payload)
      setMessage(`Passenger-service ${action.replaceAll("_", " ")} metadata recorded.`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function persistLinks(continueToDocuments = false) {
    if (!selected?.id || selectedWarnings.length) return
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/passenger-services/${selected.id}/fulfilment/links`, {
        booking_workspace_id: fulfilment.booking_workspace_id || undefined,
        booking_record_id: fulfilment.booking_record_id || undefined,
        ssr_osi_workspace_id: fulfilment.ssr_osi_workspace_id || undefined,
        ticket_record_ids: fulfilment.ticket_record_ids,
        ticket_coupon_ids: fulfilment.ticket_coupon_ids,
        emd_record_ids: fulfilment.emd_record_ids,
        emd_coupon_ids: fulfilment.emd_coupon_ids,
        document_workspace_ids: fulfilment.document_workspace_ids,
        next_action: fulfilment.next_action || undefined,
      })
      if (continueToDocuments) {
        window.location.href = `/agency/document-workspaces?related_service=${encodeURIComponent(selected.id)}`
        return
      }
      setMessage("Canonical passenger-service links recorded.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const selectedWarnings = selectionWarnings(fulfilment, linkOptions)
  const documentsReady = Boolean(selected?.document_workspace_ids?.length)

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Daily Work</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Passenger Services</h2>
              <p className="mt-1 text-sm text-slate-600">One continuous passenger-service fulfilment thread from request or trip need through booking, manual airline or airport confirmation, documents, EMD when applicable, and final outcome. External results are recorded and reconciled; AeroAssist does not transmit SSR/OSI, confirm airline approval, issue EMDs, or call providers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Manual reconciliation</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No SSR/OSI transmission</span>
            </div>
          </div>

          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Passenger services", href: "/agency/passenger-services" }]}
            currentLabel={selected?.service_label || selected?.service_type || "Passenger Service"}
            status={selected?.fulfilment_result || selected?.status || "unknown"}
            validation={!selected
              ? { state: "blocked", label: "Service case required", reason: "Passenger service must originate from Request or Trip." }
              : selectedWarnings.length ? { state: "warning", label: "Link context requires review", reason: selectedWarnings[0] }
                : { state: documentsReady ? "ready" : "warning", label: documentsReady ? "Document context linked" : "Document requirement pending", reason: documentsReady ? "Continue to explicit document review." : "Create or link the required document metadata before continuing." }}
            previous={selected?.ticket_record_ids?.[0] || incomingTicketRecordId
              ? { label: "Previous: ticket", href: `/agency/tickets/${selected?.ticket_record_ids?.[0] || incomingTicketRecordId}` }
              : selected?.booking_workspace_id ? { label: "Previous: booking", href: `/agency/booking-workspaces/${selected.booking_workspace_id}` }
                : selected?.trip_id ? { label: "Previous: trip", href: `/agency/trips/${selected.trip_id}` }
                  : selected?.request_id ? { label: "Previous: request", href: `/agency/requests/${selected.request_id}` } : { label: "Passenger services", href: "/agency/passenger-services" }}
            next={{ label: "Continue to documents", onClick: () => persistLinks(true), enabled: Boolean(selected) && selectedWarnings.length === 0, reason: selectedWarnings[0] || "Select a passenger-service case first." }}
            relatedRecords={[
              { label: "Booking", value: selected?.booking_record_id || selected?.booking_workspace_id || "none", href: selected?.booking_workspace_id ? `/agency/booking-workspaces/${selected.booking_workspace_id}` : undefined },
              { label: "Tickets", value: selected?.ticket_record_ids?.length || 0 },
              { label: "Documents", value: selected?.document_workspace_ids?.length || 0 },
            ]}
          />

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Passenger-service cases</h3>
              <div className="mt-4 divide-y divide-slate-100 border-y border-slate-200">
                {(state?.serviceCases || []).map((item) => (
                  <button className={`grid w-full gap-1 px-3 py-3 text-left text-sm ${item.id === selected?.id ? "bg-blue-50" : "hover:bg-slate-50"}`} key={item.id} type="button" onClick={() => setSelectedId(item.id)}>
                    <span className="font-semibold text-slate-950">{item.service_label || item.service_type}</span>
                    <span className="text-xs text-slate-600">{item.request_id || item.trip_id || "Source pending"} · {formatType(item.fulfilment_result || "unknown")}</span>
                  </button>
                ))}
              </div>
              {!state?.serviceCases?.length ? <EmptyState title="No service cases" body="Passenger service requirements originate from request or trip passenger need." /> : null}
            </div>
            {selected ? (
              <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div><h3 className="font-semibold text-slate-950">{selected.service_label || selected.service_type}</h3><p className="mt-1 text-sm text-slate-600">External status: {formatType(selected.external_manual_status || "unknown")} · Outcome: {formatType(selected.fulfilment_result || "unknown")}</p></div>
                  <div className="flex flex-wrap gap-2">
                    <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/document-workspaces?related_service=${encodeURIComponent(selected.id)}`}>Document requirements</a>
                    <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/documents?document_type=service_confirmation&source_context_type=service_request&source_context_id=${encodeURIComponent(selected.id)}`}>Render service document</a>
                    <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/after-sales?passenger_service_request_id=${encodeURIComponent(selected.id)}${selected.booking_workspace_id ? `&booking_workspace_id=${encodeURIComponent(selected.booking_workspace_id)}` : ""}`}>Open after-sales case</a>
                  </div>
                </div>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  <CanonicalSelector label="Booking workspace" value={fulfilment.booking_workspace_id} onChange={(value) => setFulfilmentField("booking_workspace_id", value)} items={linkOptions.booking_workspaces} />
                  <CanonicalSelector label="Booking record" value={fulfilment.booking_record_id} onChange={(value) => setFulfilmentField("booking_record_id", value)} items={linkOptions.booking_records} />
                  <CanonicalMultiSelector label="Tickets" value={fulfilment.ticket_record_ids} onChange={(value) => setFulfilmentField("ticket_record_ids", value)} items={linkOptions.tickets} />
                  <CanonicalMultiSelector label="Ticket coupons" value={fulfilment.ticket_coupon_ids} onChange={(value) => setFulfilmentField("ticket_coupon_ids", value)} items={(linkOptions.ticket_coupons || []).filter((item) => !fulfilment.ticket_record_ids.length || fulfilment.ticket_record_ids.includes(item.context?.ticket_record_id))} />
                  <CanonicalMultiSelector label="EMDs" value={fulfilment.emd_record_ids} onChange={(value) => setFulfilmentField("emd_record_ids", value)} items={linkOptions.emds} />
                  <CanonicalMultiSelector label="EMD coupons" value={fulfilment.emd_coupon_ids} onChange={(value) => setFulfilmentField("emd_coupon_ids", value)} items={(linkOptions.emd_coupons || []).filter((item) => !fulfilment.emd_record_ids.length || fulfilment.emd_record_ids.includes(item.context?.emd_record_id))} />
                  <CanonicalMultiSelector label="Documents" value={fulfilment.document_workspace_ids} onChange={(value) => setFulfilmentField("document_workspace_ids", value)} items={linkOptions.documents} />
                  <CanonicalSelector label="SSR / OSI workspace" value={fulfilment.ssr_osi_workspace_id} onChange={(value) => setFulfilmentField("ssr_osi_workspace_id", value)} items={linkOptions.ssr_osi_workspaces} />
                </div>
                <SelectionWarnings warnings={selectedWarnings} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => persistLinks(false)} disabled={selectedWarnings.length > 0}>Link selected records</button>
                <div className="grid gap-3 md:grid-cols-3">
                  <SelectField label="Airline confirmation" value={fulfilment.airline_confirmation_status} onChange={(value) => setFulfilmentField("airline_confirmation_status", value)} options={confirmationOptions()} />
                  <Field label="Airline evidence reference" value={fulfilment.airline_confirmation_evidence_reference} onChange={(value) => setFulfilmentField("airline_confirmation_evidence_reference", value)} />
                  <SelectField label="Airport confirmation" value={fulfilment.airport_handling_confirmation_status} onChange={(value) => setFulfilmentField("airport_handling_confirmation_status", value)} options={confirmationOptions()} />
                  <Field label="Airport evidence reference" value={fulfilment.airport_handling_evidence_reference} onChange={(value) => setFulfilmentField("airport_handling_evidence_reference", value)} />
                  <SelectField label="External/manual status" value={fulfilment.external_manual_status} onChange={(value) => setFulfilmentField("external_manual_status", value)} options={confirmationOptions()} />
                  <Field label="Next action" value={fulfilment.next_action} onChange={(value) => setFulfilmentField("next_action", value)} />
                </div>
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => recordAction("confirmations", {
                  airline_confirmation_status: fulfilment.airline_confirmation_status,
                  airline_confirmation_evidence_reference: fulfilment.airline_confirmation_evidence_reference || undefined,
                  airport_handling_confirmation_status: fulfilment.airport_handling_confirmation_status,
                  airport_handling_evidence_reference: fulfilment.airport_handling_evidence_reference || undefined,
                  external_manual_status: fulfilment.external_manual_status, next_action: fulfilment.next_action || undefined,
                })}>Record manual confirmation</button>
                <div className="grid gap-3 md:grid-cols-3">
                  <SelectField label="Fulfilment result" value={fulfilment.fulfilment_result} onChange={(value) => setFulfilmentField("fulfilment_result", value)} options={["pending", "confirmed", "conditionally_confirmed", "fulfilled", "failed", "cancelled", "unknown"].map((item) => [item, formatType(item)])} />
                  <Field label="Mismatch notes" value={fulfilment.mismatches} onChange={(value) => setFulfilmentField("mismatches", value)} />
                  <Field label="Next action" value={fulfilment.next_action} onChange={(value) => setFulfilmentField("next_action", value)} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => recordAction("reconcile", { external_manual_status: fulfilment.external_manual_status, fulfilment_result: fulfilment.fulfilment_result, unresolved_mismatches_json: fulfilment.mismatches ? [{ code: "manual_mismatch", message: fulfilment.mismatches }] : [], next_action: fulfilment.next_action || undefined })}>Reconcile result</button>
                  <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={() => recordAction("outcome", { fulfilment_result: fulfilment.fulfilment_result, unresolved_mismatches_json: fulfilment.mismatches ? [{ code: "manual_mismatch", message: fulfilment.mismatches }] : [], next_action: fulfilment.next_action || undefined })}>Record final outcome</button>
                </div>
                <div className="grid gap-3 text-sm md:grid-cols-3">
                  <Info label="Booking" value={selected.booking_record_id || selected.booking_workspace_id || "Not linked"} />
                  <Info label="Tickets" value={formatList(selected.ticket_record_ids)} />
                  <Info label="EMDs" value={formatList(selected.emd_record_ids)} />
                  <Info label="Documents" value={formatList(selected.document_workspace_ids)} />
                  <Info label="Last reconciled" value={selected.last_reconciled_at || "Not reconciled"} />
                  <Info label="Work item" value={selected.work_item_id || "Not synchronized"} />
                </div>
              </div>
            ) : null}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Passenger service filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-8">
              <SelectField label="Need" value={filters.need_category} onChange={(value) => setFilters({ ...filters, need_category: value })} options={needCategories.map((item) => [item, formatType(item)])} placeholder="All needs" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value.toUpperCase() })} />
              <SelectField label="Approval" value={filters.approval_status} onChange={(value) => setFilters({ ...filters, approval_status: value })} options={approvalStatuses.map((item) => [item, formatType(item)])} placeholder="All approvals" />
              <SelectField label="Readiness" value={filters.readiness_status} onChange={(value) => setFilters({ ...filters, readiness_status: value })} options={readinessStatuses.map((item) => [item, formatType(item)])} placeholder="All readiness" />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
              <Field label="RFIC" value={filters.rfic} onChange={(value) => setFilters({ ...filters, rfic: value.toUpperCase() })} />
              <Field label="RFISC" value={filters.rfisc} onChange={(value) => setFilters({ ...filters, rfisc: value.toUpperCase() })} />
            </div>
          </section>

          {state?.workspaces?.length ? <WorkspaceTable workspaces={state.workspaces} /> : <EmptyState title="No passenger services" body="SSR / OSI operational service metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function WorkspaceTable({ workspaces }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Service workspace</th>
            <th className="px-4 py-3">Passenger need</th>
            <th className="px-4 py-3">SSR / OSI</th>
            <th className="px-4 py-3">Approval</th>
            <th className="px-4 py-3">EMD</th>
            <th className="px-4 py-3">Documents</th>
            <th className="px-4 py-3">Fulfilment</th>
            <th className="px-4 py-3">Readiness</th>
            <th className="px-4 py-3">Operational notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {workspaces.map((workspace) => (
            <tr key={workspace.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{workspace.workspace_display_name || workspace.workspace_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{workspace.workspace_reference}</p>
                <p className="mt-2 text-xs text-slate-500">Priority: {workspace.operational_priority || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatType(workspace.need_category)}</p>
                <p className="mt-1">{workspace.need_description || "Need description unset"}</p>
                <p className="mt-1">Passenger statement: {workspace.passenger_statement || "Unset"}</p>
                <p className="mt-1">Passenger: {workspace.passenger_workspace_id || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>SSR: {workspace.ssr_code || "Unset"}</p>
                <p className="mt-1">{workspace.ssr_description || "SSR description unset"}</p>
                <p className="mt-1">Confirmation: {workspace.ssr_confirmation_status || "Unset"}</p>
                <p className="mt-1">OSI required: {workspace.osi_required ? "Yes" : "No"}</p>
                <p className="mt-1">OSI: {workspace.osi_text || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Airline: {workspace.airline_code || "Unset"}</p>
                <p className="mt-1">Approval: {formatType(workspace.approval_status)}</p>
                <p className="mt-1">Reference: {workspace.approval_reference || "Unset"}</p>
                <p className="mt-1">Deadline: {formatDate(workspace.approval_deadline)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Required: {workspace.emd_required ? "Yes" : "No"}</p>
                <p className="mt-1">RFIC/RFISC: {workspace.rfic || "Unset"} / {workspace.rfisc || "Unset"}</p>
                <ReferenceLine label="EMDs" items={workspace.emd_workspace_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Requirements" items={workspace.document_requirements} />
                <p className="mt-1">MEDIF: {workspace.medif_required ? "Required" : "Not required"}</p>
                <p className="mt-1">Medical cert: {workspace.medical_certificate_required ? "Required" : "Not required"}</p>
                <p className="mt-1">Veterinary: {workspace.veterinary_documents_required ? "Required" : "Not required"}</p>
                <p className="mt-1">Customs: {workspace.customs_documents_required ? "Required" : "Not required"}</p>
                <p className="mt-1">Visa: {workspace.visa_documents_required ? "Required" : "Not required"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Tasks" items={workspace.task_ids} />
                <ReferenceLine label="Timeline" items={workspace.timeline_ids} />
                <ReferenceLine label="Comms" items={workspace.communication_ids} />
                <ReferenceLine label="Flights" items={workspace.flight_workspace_ids} />
                <ReferenceLine label="Documents" items={workspace.linked_document_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <StatusBadge status={workspace.readiness_status} />
                <ReferenceLine label="Missing" items={workspace.missing_requirements} />
                <ReferenceLine label="Unresolved" items={workspace.unresolved_items} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Agent: {workspace.agent_notes || "Unset"}</p>
                <p className="mt-1">Passenger: {workspace.passenger_notes || "Unset"}</p>
                <p className="mt-1">Airline: {workspace.airline_notes || "Unset"}</p>
                <p className="mt-1">Internal: {workspace.internal_notes || "Unset"}</p>
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

function Field({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
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

function CanonicalSelector({ label, value, onChange, items = [] }) {
  const [search, setSearch] = useState("")
  const selected = items.find((item) => item.id === value)
  const filtered = items.filter((item) => item.id === value || `${item.label} ${item.context_preview || ""}`.toLowerCase().includes(search.toLowerCase()))
  return (
    <div className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`Search ${label.toLowerCase()}`} />
      <select className="min-w-0 rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Not linked</option>
        {filtered.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}
      </select>
      {selected ? <p className="text-xs text-slate-500">{selected.context_preview || formatType(selected.status)}{selected.immutable_reference ? " · immutable reference" : ""}</p> : null}
    </div>
  )
}

function CanonicalMultiSelector({ label, value = [], onChange, items = [] }) {
  const [search, setSearch] = useState("")
  const filtered = items.filter((item) => value.includes(item.id) || `${item.label} ${item.context_preview || ""}`.toLowerCase().includes(search.toLowerCase()))
  function toggle(itemId) {
    onChange(value.includes(itemId) ? value.filter((id) => id !== itemId) : [...value, itemId])
  }
  return (
    <div className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label} <span className="text-xs font-normal text-slate-500">({value.length} selected)</span></span>
      <input className="rounded-md border border-slate-300 px-3 py-2" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`Search ${label.toLowerCase()}`} />
      <div className="max-h-32 overflow-auto rounded-md border border-slate-200 p-2">
        {filtered.length ? filtered.map((item) => (
          <label className="flex gap-2 border-b border-slate-100 py-2 last:border-0" key={item.id}>
            <input type="checkbox" checked={value.includes(item.id)} onChange={() => toggle(item.id)} />
            <span className="min-w-0"><span className="block truncate font-medium text-slate-800">{item.label}</span><span className="block truncate text-xs text-slate-500">{item.context_preview || formatType(item.status)}</span></span>
          </label>
        )) : <span className="text-xs text-slate-500">No matching canonical records.</span>}
      </div>
    </div>
  )
}

function SelectionWarnings({ warnings }) {
  if (!warnings.length) return null
  return <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900"><p className="font-semibold">Review before linking</p><ul className="mt-1 list-disc space-y-1 pl-4">{warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div>
}

function selectionWarnings(values, options) {
  const groups = [
    ["booking_workspace_id", "booking_workspaces"], ["booking_record_id", "booking_records"],
    ["ticket_record_ids", "tickets"], ["ticket_coupon_ids", "ticket_coupons"],
    ["emd_record_ids", "emds"], ["emd_coupon_ids", "emd_coupons"],
    ["document_workspace_ids", "documents"], ["ssr_osi_workspace_id", "ssr_osi_workspaces"],
  ]
  return [...new Set(groups.flatMap(([field, group]) => {
    const ids = Array.isArray(values[field]) ? values[field] : [values[field]].filter(Boolean)
    return ids.flatMap((id) => (options[group] || []).find((item) => item.id === id)?.warnings || [])
  }))]
}

function ReferenceLine({ label, items }) {
  return <p className="mt-1"><span className="font-semibold text-slate-700">{label}:</span> {formatList(items)}</p>
}

function StatusBadge({ status }) {
  return <span className="inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{formatType(status || "pending")}</span>
}

function Info({ label, value }) {
  return <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 break-words text-slate-800">{value}</p></div>
}

function confirmationOptions() {
  return ["pending", "requested", "awaiting_external_confirmation", "confirmed", "conditionally_confirmed", "rejected", "cancelled", "not_required", "unknown"].map((item) => [item, formatType(item)])
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

function uniqueValues(items) {
  return [...new Set((items || []).filter(Boolean))]
}
