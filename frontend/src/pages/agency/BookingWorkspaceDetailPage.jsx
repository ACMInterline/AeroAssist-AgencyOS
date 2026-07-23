import { useEffect, useState } from "react"
import ArchiveX from "lucide-react/dist/esm/icons/archive-x.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import ConfirmationDialog from "../../components/ConfirmationDialog"
import DestructiveButton from "../../components/DestructiveButton"
import DetailSummary from "../../components/DetailSummary"
import EmptyState from "../../components/EmptyState"
import OperationalAlert from "../../components/OperationalAlert"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import SecondaryButton from "../../components/SecondaryButton"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const workspaceStatuses = ["draft", "ready_to_book", "booking_in_progress", "booked", "blocked", "cancelled"]
const providerStatuses = ["draft", "queued", "held", "confirmed", "failed", "cancelled"]
const bookingStatuses = ["draft", "pending", "confirmed", "partially_confirmed", "failed", "cancelled"]

export default function BookingWorkspaceDetailPage({ bookingWorkspaceId }) {
  const [state, setState] = useState(null)
  const [statusForm, setStatusForm] = useState({ status: "draft" })
  const [recordForm, setRecordForm] = useState({ pnr_locator: "", provider_status: "draft", booking_status: "draft", internal_notes: "" })
  const [confirmCancel, setConfirmCancel] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/booking-workspaces/${bookingWorkspaceId}`)
    const bookingRecordId = detail.booking_record?.id
    const [tickets, emds, ticketEmdReadiness, invoices] = await Promise.all([
      bookingRecordId ? apiGet(`/api/agencies/${context.agency.id}/tickets?booking_record_id=${encodeURIComponent(bookingRecordId)}`) : Promise.resolve({ items: [] }),
      bookingRecordId ? apiGet(`/api/agencies/${context.agency.id}/emds?booking_record_id=${encodeURIComponent(bookingRecordId)}`) : Promise.resolve({ items: [] }),
      bookingRecordId ? apiGet(`/api/agencies/${context.agency.id}/booking-records/${bookingRecordId}/ticket-emd-readiness`) : Promise.resolve(null),
      apiGet(`/api/agencies/${context.agency.id}/invoices?booking_workspace_id=${encodeURIComponent(bookingWorkspaceId)}`),
    ])
    setState({ ...context, ...detail, tickets: tickets.items || [], emds: emds.items || [], ticketEmdReadiness, invoices: invoices.items || [] })
    setStatusForm({ status: detail.booking_workspace?.status || "draft" })
    setRecordForm({
      pnr_locator: detail.booking_record?.pnr_locator || "",
      provider_status: detail.booking_record?.provider_status || "draft",
      booking_status: detail.booking_record?.booking_status || "draft",
      internal_notes: detail.booking_record?.internal_notes || "",
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [bookingWorkspaceId])

  async function updateStatus(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/${bookingWorkspaceId}/status`, statusForm)
      setMessage("Booking workspace status updated.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function updateRecord(event) {
    event.preventDefault()
    if (!state?.booking_record) return
    setError("")
    setMessage("")
    try {
      await apiPut(`/api/agencies/${state.agency.id}/booking-records/${state.booking_record.id}`, {
        ...recordForm,
        pnr_locator: recordForm.pnr_locator || null,
      })
      setMessage("Manual PNR mirror updated.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function rebuildRecord() {
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/${bookingWorkspaceId}/rebuild-record`)
      setMessage("Booking record mirror rebuilt from readiness.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function cancelWorkspace() {
    setConfirmCancel(true)
  }

  async function confirmCancelWorkspace() {
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/${bookingWorkspaceId}/cancel`)
      setConfirmCancel(false)
      setMessage("Booking cancelled.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function createDraftTicket() {
    if (!state?.booking_record?.id) return
    setError("")
    setMessage("")
    try {
      const created = await apiPost(`/api/agencies/${state.agency.id}/tickets/from-booking-record`, {
        booking_record_id: state.booking_record.id,
        create_coupons: true,
      })
      window.location.href = `/agency/tickets/${created.ticket.id}`
    } catch (err) {
      setError(err.message)
    }
  }

  async function createDraftEmd() {
    if (!state?.booking_record?.id) return
    setError("")
    setMessage("")
    try {
      const created = await apiPost(`/api/agencies/${state.agency.id}/emds/from-booking-service`, {
        booking_record_id: state.booking_record.id,
        ticket_record_id: state.tickets?.[0]?.id || null,
        create_coupons: true,
      })
      window.location.href = `/agency/emds/${created.emd.id}`
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
    setError("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/${bookingWorkspaceId}/invoice`)
      window.location.href = `/agency/invoices/${result.invoice.id}`
    } catch (err) {
      setError(err.message)
    }
  }

  const workspace = state?.booking_workspace
  const record = state?.booking_record
  const source = workspace?.source_snapshot_json || {}
  const readiness = source.booking_readiness_package || {}
  const ticket = state?.tickets?.[0]
  const invoice = state?.invoices?.[0]
  const canContinueToTicket = Boolean(record && !["cancelled", "blocked"].includes(workspace?.status))

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Bookings", href: "/agency/booking-workspaces" }, { label: workspace?.workspace_number || "Booking" }]}
            eyebrow={`${workspace?.workspace_number || "Booking"} · ${label(workspace?.provider_target)}`}
            title={workspace?.title}
            description="Track the confirmed booking details, passengers, flights, tickets, services, and next action in one place."
            actions={<>{workspace?.trip_id ? <SecondaryButton href={`/agency/trips/${workspace.trip_id}`}>Open trip</SecondaryButton> : null}<SecondaryButton href={`/agency/after-sales?booking_workspace_id=${encodeURIComponent(workspace?.id || "")}`}>Start after-sales case</SecondaryButton><SecondaryButton icon={RefreshCw} onClick={rebuildRecord}>Refresh booking details</SecondaryButton><DestructiveButton icon={ArchiveX} onClick={cancelWorkspace}>Cancel booking</DestructiveButton></>}
          />

          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Booking handoffs", href: "/agency/booking-handoffs" }, { label: "Bookings", href: "/agency/booking-workspaces" }]}
            currentLabel={workspace?.workspace_number || "Booking"}
            status={workspace?.status}
            validation={canContinueToTicket ? { state: "ready", label: "Ready for ticket details", reason: "Booking details are present. Ticket issue remains a separate authorized action." } : { state: "blocked", label: "Booking details required", reason: "Resolve the booking checks or refresh the booking details before continuing." }}
            previous={workspace?.offer_workspace_id ? { label: "Previous: accepted offer", href: `/agency/offers/${workspace.offer_workspace_id}` } : workspace?.trip_id ? { label: "Previous: trip", href: `/agency/trips/${workspace.trip_id}` } : { label: "Booking handoffs", href: "/agency/booking-handoffs" }}
            next={ticket
              ? { label: "Continue to ticket", href: `/agency/tickets/${ticket.id}` }
              : { label: "Add ticket details", onClick: createDraftTicket, enabled: canContinueToTicket, reason: "An active booking is required." }}
            relatedRecords={[
              { label: "Trip", value: state?.trip_summary?.trip_reference || workspace?.trip_id || "none", href: workspace?.trip_id ? `/agency/trips/${workspace.trip_id}` : undefined },
              { label: "Accepted offer", value: state?.accepted_offer_summary?.id || workspace?.offer_acceptance_id || "none", href: workspace?.offer_workspace_id ? `/agency/offers/${workspace.offer_workspace_id}` : undefined },
              { label: "Tickets", value: state?.tickets?.length || 0 },
              { label: "Invoice", value: invoice?.invoice_number || "none", href: invoice ? `/agency/invoices/${invoice.id}` : undefined },
            ]}
          />

          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div> : null}
          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div> : null}

          <DetailSummary title="Booking summary" columns={4} items={[
            { label: "Current status", value: label(workspace?.status) },
            { label: "Booking status", value: label(record?.booking_status || "draft") },
            { label: "Airline or supplier status", value: label(record?.provider_status || "draft") },
            { label: "PNR", value: record?.pnr_locator || "Pending" },
          ]} />

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <Panel title="Current status">
                <form className="space-y-3" onSubmit={updateStatus}>
                  <label className="grid gap-1 text-sm font-medium text-slate-700">
                    Status
                    <select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={statusForm.status} onChange={(event) => setStatusForm({ status: event.target.value })}>
                      {workspaceStatuses.map((value) => <option value={value} key={value}>{label(value)}</option>)}
                    </select>
                  </label>
                  <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="submit">Save status</button>
                </form>
              </Panel>

              <Panel title="Booking details">
                {record ? (
                  <form className="space-y-3" onSubmit={updateRecord}>
                    <Field label="PNR locator" value={recordForm.pnr_locator} onChange={(value) => setRecordForm({ ...recordForm, pnr_locator: value.toUpperCase() })} />
                    <Select label="Provider status" value={recordForm.provider_status} options={providerStatuses} onChange={(value) => setRecordForm({ ...recordForm, provider_status: value })} />
                    <Select label="Booking status" value={recordForm.booking_status} options={bookingStatuses} onChange={(value) => setRecordForm({ ...recordForm, booking_status: value })} />
                    <Textarea label="Internal notes" value={recordForm.internal_notes} onChange={(value) => setRecordForm({ ...recordForm, internal_notes: value })} />
                    <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="submit">Save booking details</button>
                  </form>
                ) : (
                  <EmptyState title="No booking details yet" body="Refresh the booking details to prepare this booking for ticket information." />
                )}
              </Panel>

              <OperationalAlert title="Airline and supplier actions">
                AeroAssist records the outcome here. Your team continues to use the authorized airline or supplier channel for the booking itself.
              </OperationalAlert>

              <Panel title="Documents">
                <div className="grid gap-2">
                  <a className="aa-primary-action rounded-md px-3 py-2 text-center text-sm font-semibold" href={documentHref("booking_confirmation", "booking_workspace", workspace?.id)}>Booking confirmation</a>
                  <a className="rounded-md border border-slate-300 px-3 py-2 text-center text-sm font-semibold" href={documentHref("pnr_mirror", record ? "booking_record" : "booking_workspace", record?.id || workspace?.id)}>PNR mirror</a>
                  {record ? <a className="rounded-md border border-slate-300 px-3 py-2 text-center text-sm font-semibold" href={documentHref("internal_case_summary", "booking_record", record.id)}>Internal case summary</a> : null}
                </div>
                <p className="text-xs text-slate-500">Document previews are generated from stored internal mirrors only.</p>
              </Panel>

              <Panel title="Tickets & EMDs">
                <div className="grid gap-2">
                  <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={createDraftTicket} disabled={!record}>Add ticket details</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={createDraftEmd} disabled={!record}>Add EMD details</button>
                </div>
                <p className="text-xs text-slate-500">Live issuance is not implemented in this phase.</p>
              </Panel>

              <Panel title="Finance">
                <button className="aa-primary-action w-full rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-50" type="button" onClick={createOrOpenInvoice} disabled={!record}>{invoice ? "Open linked invoice" : "Create linked invoice"}</button>
                <p className="text-xs text-slate-500">Creates or opens one agency-scoped invoice linked to this canonical booking workspace and record. Payment remains manually recorded.</p>
              </Panel>
            </div>

            <div className="space-y-4">
              <Panel title="Ticket / EMD Readiness">
                <div className="grid gap-3 md:grid-cols-4">
                  <Summary label="Tickets" value={state?.ticketEmdReadiness?.ticket_count ?? 0} />
                  <Summary label="EMDs" value={state?.ticketEmdReadiness?.emd_count ?? 0} />
                  <Summary label="Missing ticket #" value={state?.ticketEmdReadiness?.missing_ticket_numbers ?? 0} />
                  <Summary label="Missing EMD #" value={state?.ticketEmdReadiness?.missing_emd_numbers ?? 0} />
                </div>
                <SnapshotList items={state?.ticketEmdReadiness?.warnings} render={(item) => item.message || JSON.stringify(item)} />
              </Panel>

              <section className="grid gap-4 lg:grid-cols-2">
                <Panel title="Linked Tickets">
                  <LinkedList
                    items={state?.tickets}
                    empty="No ticket mirrors yet."
                    href={(item) => `/agency/tickets/${item.id}`}
                    render={(item) => `${item.ticket_number || "Draft ticket"} · ${label(item.issue_status || item.status)}`}
                  />
                </Panel>
                <Panel title="Linked EMDs">
                  <LinkedList
                    items={state?.emds}
                    empty="No EMD mirrors yet."
                    href={(item) => `/agency/emds/${item.id}`}
                    render={(item) => `${item.emd_number || "Draft EMD"} · ${item.service_label || item.service_key || "Service"}`}
                  />
                </Panel>
              </section>

              <Panel title="Source Summary">
                <div className="grid gap-3 md:grid-cols-3">
                  <Summary label="Readiness" value={label(state?.readiness_summary?.status)} />
                  <Summary label="Accepted offer" value={state?.accepted_offer_summary?.id || workspace?.offer_acceptance_id || "Not linked"} />
                  <Summary label="Trip" value={state?.trip_summary?.trip_reference || workspace?.trip_id} />
                </div>
              </Panel>

              <Panel title="Passengers">
                <SnapshotList items={workspace?.passengers_snapshot_json} render={(item) => item.display_name || item.snapshot_display_name || `${item.first_name || ""} ${item.last_name || ""}`.trim() || "Passenger"} />
              </Panel>

              <Panel title="Segments">
                <SnapshotList items={workspace?.segments_snapshot_json} render={(item) => `${item.sequence || item.segment_order || ""}. ${item.origin_airport || item.origin_airport_code} to ${item.destination_airport || item.destination_airport_code}${item.flight_number ? ` · ${item.flight_number}` : ""}`} />
              </Panel>

              <section className="grid gap-4 lg:grid-cols-2">
                <Panel title="Pricing"><JsonBlock value={workspace?.pricing_snapshot_json} /></Panel>
                <Panel title="Services"><JsonBlock value={workspace?.services_snapshot_json} /></Panel>
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <Panel title="Pets"><JsonBlock value={workspace?.pets_snapshot_json} /></Panel>
                <Panel title="Special Items"><JsonBlock value={workspace?.special_items_snapshot_json} /></Panel>
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <Panel title="SSR"><SnapshotList items={workspace?.ssr_json} render={(item) => item.ssr_code || item.code || JSON.stringify(item)} /></Panel>
                <Panel title="OSI"><SnapshotList items={workspace?.osi_json} render={(item) => item.osi_text || item.text || JSON.stringify(item)} /></Panel>
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <Panel title="Required Documents"><SnapshotList items={workspace?.required_documents_json} render={(item) => item.label || item.document_type || JSON.stringify(item)} /></Panel>
                <Panel title="Warnings / Policy"><SnapshotList items={[...(workspace?.warnings_json || []), ...(workspace?.policy_violations_json || [])]} render={(item) => item.message || item.reason || JSON.stringify(item)} /></Panel>
              </section>

              <Panel title="Internal PNR Mirror">
                <JsonBlock value={record?.internal_pnr_mirror_json} />
              </Panel>

              <Panel title="Source Readiness">
                <JsonBlock value={readiness} />
              </Panel>

              <Panel title="Timeline">
                <SnapshotList items={state?.timeline} render={(item) => `${item.title}${item.description ? ` · ${item.description}` : ""}`} />
              </Panel>
            </div>
          </section>
          <ConfirmationDialog
            confirmLabel="Cancel booking"
            destructive
            message="The booking will be marked as cancelled in AeroAssist. Existing trip, passenger, ticket, and activity history will remain available."
            onCancel={() => setConfirmCancel(false)}
            onConfirm={confirmCancelWorkspace}
            open={confirmCancel}
            title="Cancel this booking?"
          />
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function Summary({ label, value }) {
  return <div className="rounded-md bg-slate-50 p-3"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 truncate text-sm font-semibold text-slate-950">{value || "Not set"}</p></div>
}

function Field({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Textarea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<textarea className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, options, onChange }) {
  return (
    <label className="grid gap-1 text-sm font-medium text-slate-700">
      {label}
      <select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{labelValue(option)}</option>)}
      </select>
    </label>
  )
}

function SnapshotList({ items, render }) {
  const list = items || []
  if (!list.length) return <p className="text-sm text-slate-500">None recorded.</p>
  return (
    <div className="divide-y divide-slate-100 rounded-md border border-slate-200">
      {list.map((item, index) => <div className="p-3 text-sm text-slate-700" key={item.id || index}>{render(item)}</div>)}
    </div>
  )
}

function LinkedList({ items, empty, href, render }) {
  const list = items || []
  if (!list.length) return <p className="text-sm text-slate-500">{empty}</p>
  return (
    <div className="divide-y divide-slate-100 rounded-md border border-slate-200">
      {list.map((item) => <a className="block p-3 text-sm font-medium text-blue-700" href={href(item)} key={item.id}>{render(item)}</a>)}
    </div>
  )
}

function JsonBlock({ value }) {
  const hasValue = value && (Array.isArray(value) ? value.length : Object.keys(value).length)
  if (!hasValue) return <p className="text-sm text-slate-500">None recorded.</p>
  return <pre className="max-h-72 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">{JSON.stringify(value, null, 2)}</pre>
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function labelValue(value) {
  return String(value || "").replaceAll("_", " ")
}

function documentHref(documentType, sourceContextType, sourceContextId) {
  const params = new URLSearchParams({
    document_type: documentType,
    source_context_type: sourceContextType,
    source_context_id: sourceContextId || "",
  })
  return `/agency/documents?${params.toString()}`
}
