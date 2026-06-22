import { useEffect, useMemo, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import RefundExchangeStatusBadge from "../../components/RefundExchangeStatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const CASE_TYPES = [
  "refund",
  "exchange",
  "void",
  "schedule_change",
  "involuntary_change",
  "cancellation",
  "other",
]

const REASON_CATEGORIES = [
  "client_request",
  "illness",
  "visa_document_issue",
  "schedule_change",
  "disruption",
  "duplicate_booking",
  "wrong_name",
  "fare_rule_change",
  "agency_error",
  "airline_error",
  "other",
]

const PRIORITIES = ["low", "normal", "high", "urgent"]
const STATUSES = [
  "draft",
  "client_requested",
  "review_needed",
  "checking_supplier_rules",
  "waiting_for_client",
  "waiting_for_supplier",
  "approved",
  "processing_externally",
  "completed",
  "rejected",
  "cancelled",
  "archived",
]

const INITIAL = {
  source: "manual",
  client_id: "",
  booking_id: "",
  case_type: "refund",
  reason_category: "client_request",
  priority: "normal",
  status: "draft",
  client_reason_text: "",
  internal_summary: "",
  client_visible_summary: "",
  supplier_reference: "",
  expected_supplier_response_at: "",
  deadline_at: "",
  estimated_refund_amount: "",
  estimated_penalty_amount: "",
  estimated_exchange_difference_amount: "",
  estimated_agency_fee_amount: "",
  estimated_total_due_from_client: "",
  estimated_total_due_to_client: "",
  currency: "EUR",
  client_visible: true,
  link_ticket_ids: [],
  link_emd_ids: [],
  link_invoice_ids: [],
  link_payment_ids: [],
  link_passenger_ids: [],
}

export default function RefundExchangeCaseCreatePage() {
  const [state, setState] = useState(null)
  const [bookingDetail, setBookingDetail] = useState(null)
  const [error, setError] = useState("")
  const [form, setForm] = useState(INITIAL)

  async function load() {
    const context = await loadCurrentAgency()
    const [clients, bookings] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/clients`),
      apiGet(`/api/agencies/${context.agency.id}/bookings`),
    ])
    const selectedBookingId = new URLSearchParams(window.location.search).get("bookingId") || ""
    const booking = bookings.items.find((item) => item.id === selectedBookingId) || null

    const nextState = { ...context, clients: clients.items, bookings: bookings.items }
    setState(nextState)
    setForm((current) => ({
      ...current,
      source: booking ? "booking" : "manual",
      booking_id: selectedBookingId || "",
      client_id: booking ? booking.client_id : clients.items[0]?.id || "",
      status: booking ? "client_requested" : "draft",
    }))

    if (booking) {
      await loadBookingDetail(context.agency.id, booking.id)
    }
  }

  async function loadBookingDetail(agencyId, bookingId) {
    const detail = await apiGet(`/api/agencies/${agencyId}/bookings/${bookingId}`)
    setBookingDetail(detail)
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedBooking = useMemo(() => (
    state?.bookings?.find((item) => item.id === form.booking_id) || null
  ), [state?.bookings, form.booking_id])

  function onFieldChange(name, value) {
    if (name === "source" && value === "manual") {
      setBookingDetail(null)
    }
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function changeBooking(bookingId) {
    const nextBookingId = bookingId
    onFieldChange("booking_id", nextBookingId)
    if (!nextBookingId) {
      setBookingDetail(null)
      return
    }
    onFieldChange("client_id", selectedBooking?.client_id || "")
    if (state?.agency) {
      await loadBookingDetail(state.agency.id, nextBookingId)
    }
  }

  function toggleSelection(name, id) {
    const existing = new Set(form[name])
    if (existing.has(id)) {
      existing.delete(id)
    } else {
      existing.add(id)
    }
    onFieldChange(name, Array.from(existing))
  }

  function asNumber(value) {
    if (value === "" || value === undefined || value === null) return undefined
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : undefined
  }

  async function submit(event) {
    event.preventDefault()
    if (!state?.agency) return

    const payload = {
      case_type: form.case_type,
      reason_category: form.reason_category,
      priority: form.priority,
      status: form.status,
      client_reason_text: form.client_reason_text || undefined,
      internal_summary: form.internal_summary || undefined,
      client_visible_summary: form.client_visible_summary || undefined,
      supplier_reference: form.supplier_reference || undefined,
      expected_supplier_response_at: form.expected_supplier_response_at || undefined,
      deadline_at: form.deadline_at || undefined,
      estimated_refund_amount: asNumber(form.estimated_refund_amount),
      estimated_penalty_amount: asNumber(form.estimated_penalty_amount),
      estimated_exchange_difference_amount: asNumber(form.estimated_exchange_difference_amount),
      estimated_agency_fee_amount: asNumber(form.estimated_agency_fee_amount),
      estimated_total_due_from_client: asNumber(form.estimated_total_due_from_client),
      estimated_total_due_to_client: asNumber(form.estimated_total_due_to_client),
      currency: form.currency || "EUR",
      client_visible: form.client_visible,
    }

    if (form.source === "manual") {
      if (!form.client_id) {
        setError("Client is required.")
        return
      }
      payload.client_id = form.client_id
      const result = await apiPost(`/api/agencies/${state.agency.id}/refund-exchange-cases`, payload)
      window.location.href = `/agency/refunds-exchanges/${result.case.id}`
      return
    }

    if (!form.booking_id) {
      setError("Booking is required.")
      return
    }

    const bookingPayload = {
      ...payload,
      case_type: form.case_type,
      reason_category: form.reason_category,
      priority: form.priority,
      status: form.status || "client_requested",
      currency: form.currency || "EUR",
      link_ticket_ids: form.link_ticket_ids,
      link_emd_ids: form.link_emd_ids,
      link_invoice_ids: form.link_invoice_ids,
      link_payment_ids: form.link_payment_ids,
      link_passenger_ids: form.link_passenger_ids,
    }

    const result = await apiPost(
      `/api/agencies/${state.agency.id}/bookings/${form.booking_id}/create-refund-exchange-case`,
      bookingPayload,
    )
    window.location.href = `/agency/refunds-exchanges/${result.case.id}`
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/refunds-exchanges">Back to refunds/exchanges</a>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Create refund / exchange case</h2>
            <p className="mt-1 text-sm text-slate-600">Use this page to track manual refund/exchange follow-up without executing any supplier action.</p>
          </div>
          <form className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={submit}>
            <label className="text-sm font-medium text-slate-700">
              Source
              <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.source} onChange={(event) => onFieldChange("source", event.target.value)}>
                <option value="manual">Manual</option>
                <option value="booking">From booking</option>
              </select>
            </label>
            {form.source === "booking" ? (
              <label className="text-sm font-medium text-slate-700">
                Booking
                <select required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.booking_id} onChange={(event) => changeBooking(event.target.value)}>
                  <option value="">Select booking</option>
                  {(state?.bookings || []).map((booking) => <option key={booking.id} value={booking.id}>{booking.booking_reference} · {booking.client_id}</option>)}
                </select>
              </label>
            ) : (
              <label className="text-sm font-medium text-slate-700">
                Client
                <select required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.client_id} onChange={(event) => onFieldChange("client_id", event.target.value)}>
                  <option value="">Select client</option>
                  {(state?.clients || []).map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}
                </select>
              </label>
            )}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <label className="text-sm font-medium text-slate-700">
                Case type
                <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.case_type} onChange={(event) => onFieldChange("case_type", event.target.value)}>
                  {CASE_TYPES.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Status
                <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.status} onChange={(event) => onFieldChange("status", event.target.value)}>
                  {STATUSES.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Priority
                <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.priority} onChange={(event) => onFieldChange("priority", event.target.value)}>
                  {PRIORITIES.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700 md:col-span-2">
                Reason category
                <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.reason_category} onChange={(event) => onFieldChange("reason_category", event.target.value)}>
                  {REASON_CATEGORIES.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Currency
                <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.currency} onChange={(event) => onFieldChange("currency", event.target.value)} />
              </label>
            </div>
            <label className="text-sm font-medium text-slate-700">
              Client reason
              <textarea rows="2" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.client_reason_text} onChange={(event) => onFieldChange("client_reason_text", event.target.value)} />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Internal summary
              <textarea rows="2" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.internal_summary} onChange={(event) => onFieldChange("internal_summary", event.target.value)} />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Client visible summary
              <textarea rows="2" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.client_visible_summary} onChange={(event) => onFieldChange("client_visible_summary", event.target.value)} />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Supplier reference
              <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.supplier_reference} onChange={(event) => onFieldChange("supplier_reference", event.target.value)} />
            </label>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <label className="text-sm font-medium text-slate-700">
                ETA from supplier
                <input type="datetime-local" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.expected_supplier_response_at} onChange={(event) => onFieldChange("expected_supplier_response_at", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Deadline
                <input type="datetime-local" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.deadline_at} onChange={(event) => onFieldChange("deadline_at", event.target.value)} />
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="text-sm font-medium text-slate-700">
                Estimated refund
                <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.estimated_refund_amount} onChange={(event) => onFieldChange("estimated_refund_amount", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Estimated penalty
                <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.estimated_penalty_amount} onChange={(event) => onFieldChange("estimated_penalty_amount", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Estimated fare diff
                <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.estimated_exchange_difference_amount} onChange={(event) => onFieldChange("estimated_exchange_difference_amount", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Estimated agency fee
                <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.estimated_agency_fee_amount} onChange={(event) => onFieldChange("estimated_agency_fee_amount", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Estimated due from client
                <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.estimated_total_due_from_client} onChange={(event) => onFieldChange("estimated_total_due_from_client", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Estimated due to client
                <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.estimated_total_due_to_client} onChange={(event) => onFieldChange("estimated_total_due_to_client", event.target.value)} />
              </label>
            </div>
            {form.source === "booking" && bookingDetail ? (
              <section className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <h3 className="font-semibold text-slate-900">Link optional booking records</h3>
                <p className="mt-1 text-sm text-slate-600">Selecting records does not execute any external action. It only seeds linked references.</p>
                <div className="mt-3 grid gap-4 md:grid-cols-2">
                  <fieldset className="rounded border border-slate-200 bg-white p-3">
                    <legend className="px-2 text-sm font-medium text-slate-700">Tickets</legend>
                    <div className="space-y-2 text-sm">
                      {bookingDetail.tickets.length ? bookingDetail.tickets.map((ticket) => (
                        <label className="flex items-center gap-2" key={ticket.id}>
                          <input type="checkbox" checked={form.link_ticket_ids.includes(ticket.id)} onChange={() => toggleSelection("link_ticket_ids", ticket.id)} />
                          {ticket.ticket_number}
                        </label>
                      )) : <p className="text-slate-500">No tickets for booking.</p>}
                    </div>
                  </fieldset>
                  <fieldset className="rounded border border-slate-200 bg-white p-3">
                    <legend className="px-2 text-sm font-medium text-slate-700">EMDs</legend>
                    <div className="space-y-2 text-sm">
                      {bookingDetail.emds.length ? bookingDetail.emds.map((emd) => (
                        <label className="flex items-center gap-2" key={emd.id}>
                          <input type="checkbox" checked={form.link_emd_ids.includes(emd.id)} onChange={() => toggleSelection("link_emd_ids", emd.id)} />
                          {emd.emd_number}
                        </label>
                      )) : <p className="text-slate-500">No EMDs for booking.</p>}
                    </div>
                  </fieldset>
                  <fieldset className="rounded border border-slate-200 bg-white p-3">
                    <legend className="px-2 text-sm font-medium text-slate-700">Invoices</legend>
                    <div className="space-y-2 text-sm">
                      {bookingDetail.invoices.length ? bookingDetail.invoices.map((invoice) => (
                        <label className="flex items-center gap-2" key={invoice.id}>
                          <input type="checkbox" checked={form.link_invoice_ids.includes(invoice.id)} onChange={() => toggleSelection("link_invoice_ids", invoice.id)} />
                          {invoice.invoice_number}
                        </label>
                      )) : <p className="text-slate-500">No invoices for booking.</p>}
                    </div>
                  </fieldset>
                  <fieldset className="rounded border border-slate-200 bg-white p-3">
                    <legend className="px-2 text-sm font-medium text-slate-700">Payments</legend>
                    <div className="space-y-2 text-sm">
                      {bookingDetail.payments.length ? bookingDetail.payments.map((payment) => (
                        <label className="flex items-center gap-2" key={payment.id}>
                          <input type="checkbox" checked={form.link_payment_ids.includes(payment.id)} onChange={() => toggleSelection("link_payment_ids", payment.id)} />
                          {payment.amount} {payment.currency} · {payment.status}
                        </label>
                      )) : <p className="text-slate-500">No payments for booking.</p>}
                    </div>
                  </fieldset>
                  <fieldset className="rounded border border-slate-200 bg-white p-3 md:col-span-2">
                    <legend className="px-2 text-sm font-medium text-slate-700">Passengers</legend>
                    <div className="space-y-2 text-sm">
                      {bookingDetail.passengers.length ? bookingDetail.passengers.map((item) => (
                        <label className="flex items-center gap-2" key={item.id}>
                          <input type="checkbox" checked={form.link_passenger_ids.includes(item.id)} onChange={() => toggleSelection("link_passenger_ids", item.id)} />
                          {item.snapshot_display_name} · {item.snapshot_passenger_type}
                        </label>
                      )) : <p className="text-slate-500">No passenger snapshots for booking.</p>}
                    </div>
                  </fieldset>
                </div>
              </section>
            ) : null}
            <label className="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.client_visible} onChange={(event) => onFieldChange("client_visible", event.target.checked)} />
              <span>Client-visible</span>
            </label>
            <button className="justify-self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Create case</button>
          </form>
          {form.status ? <div className="rounded-lg bg-slate-50 p-4"><RefundExchangeStatusBadge status={form.status} /></div> : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
