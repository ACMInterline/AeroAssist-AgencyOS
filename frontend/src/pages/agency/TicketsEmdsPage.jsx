import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "ready_to_issue", "issued", "voided", "refunded", "exchanged", "cancelled"]
const emdStatuses = ["draft", "ready_to_issue", "issued", "voided", "refunded", "cancelled"]
const providers = ["manual", "travelport", "amadeus", "ndc", "supplier", "other"]
const emdTypes = ["manual_mirror", "checked_baggage", "ancillary_service", "residual_value", "refund_credit", "unknown"]

const emptyTicketCoupon = {
  coupon_number: "1",
  marketing_airline: "",
  operating_airline: "",
  flight_number: "",
  departure_airport: "",
  arrival_airport: "",
  departure_date: "",
  departure_time: "",
  cabin: "",
  rbd: "",
  status: "draft",
  segment_reference: "",
}

const emptyEmdCoupon = {
  coupon_number: "1",
  rfic: "",
  rfisc: "",
  service_description: "",
  status: "draft",
  related_segment_reference: "",
  related_ticket_coupon_reference: "",
}

export default function TicketsEmdsPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("tickets")
  const [filters, setFilters] = useState({ status: "", provider: "", service_key: "", search: "" })
  const [modal, setModal] = useState("")
  const [form, setForm] = useState(defaultForm())
  const [error, setError] = useState("")
  const [working, setWorking] = useState(false)

  async function load() {
    const context = await loadCurrentAgency()
    const [tickets, emds] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/tickets`),
      apiGet(`/api/agencies/${context.agency.id}/emds`),
    ])
    setState({ ...context, tickets: tickets.items || [], emds: emds.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  function openModal(name) {
    setModal(name)
    setForm(defaultForm())
    setError("")
  }

  async function submitModal(event) {
    event.preventDefault()
    setWorking(true)
    setError("")
    try {
      if (modal === "ticket") {
        const created = await apiPost(`/api/agencies/${state.agency.id}/tickets/manual`, buildManualTicketPayload(form))
        window.location.href = `/agency/tickets/${created.ticket.id}`
        return
      }
      if (modal === "emd") {
        const created = await apiPost(`/api/agencies/${state.agency.id}/emds/manual`, buildManualEmdPayload(form))
        window.location.href = `/agency/emds/${created.emd.id}`
        return
      }
      if (modal === "ticket_exchange") {
        await apiPost(`/api/agencies/${state.agency.id}/ticket-exchange-operations`, {
          original_ticket_record_id: form.original_record_id,
          operation_type: form.operation_type || "exchange",
          trip_id: form.trip_id || null,
          booking_record_id: form.booking_record_id || null,
          reason: form.internal_notes || null,
          currency: form.currency || null,
        })
      }
      if (modal === "emd_exchange") {
        await apiPost(`/api/agencies/${state.agency.id}/emd-exchange-operations`, {
          original_emd_record_id: form.original_record_id,
          operation_type: form.operation_type || "exchange",
          trip_id: form.trip_id || null,
          booking_record_id: form.booking_record_id || null,
          reason: form.internal_notes || null,
          currency: form.currency || null,
        })
      }
      setModal("")
      setForm(defaultForm())
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking(false)
    }
  }

  const filteredTickets = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.tickets || []).filter((item) => (
      (!filters.status || item.issue_status === filters.status)
      && (!filters.provider || item.issuing_provider === filters.provider)
      && (!search || [item.ticket_number, item.validating_carrier, item.trip_id, item.booking_workspace_id, passengerName(item)].some((value) => String(value || "").toLowerCase().includes(search)))
    ))
  }, [filters, state])

  const filteredEmds = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.emds || []).filter((item) => (
      (!filters.status || item.issue_status === filters.status)
      && (!filters.provider || item.issuing_provider === filters.provider)
      && (!filters.service_key || item.service_key === filters.service_key)
      && (!search || [item.emd_number, item.service_key, item.service_label, item.trip_id, item.booking_workspace_id, passengerName(item)].some((value) => String(value || "").toLowerCase().includes(search)))
    ))
  }, [filters, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="text-2xl font-semibold text-slate-950">Tickets & EMDs</h2>
              <p className="mt-1 text-sm text-slate-600">Internal mirrors only. Live issuance is disabled.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={() => openModal("ticket")}>Create manual ticket</button>
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={() => openModal("emd")}>Create manual EMD</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => openModal("ticket_exchange")}>Start ticket exchange</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => openModal("emd_exchange")}>Start EMD exchange</button>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/booking-workspaces">Booking workspaces</a>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-[180px_minmax(0,1fr)_180px_180px_180px]">
            <div className="flex rounded-md border border-slate-300 p-1">
              <button className={`flex-1 rounded px-2 py-1.5 text-sm font-semibold ${tab === "tickets" ? "bg-blue-600 text-white" : "text-slate-700"}`} type="button" onClick={() => setTab("tickets")}>Tickets</button>
              <button className={`flex-1 rounded px-2 py-1.5 text-sm font-semibold ${tab === "emds" ? "bg-blue-600 text-white" : "text-slate-700"}`} type="button" onClick={() => setTab("emds")}>EMDs</button>
            </div>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search ticket, EMD, passenger" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {statuses.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.provider} onChange={(event) => setFilters({ ...filters, provider: event.target.value })}>
              <option value="">All providers</option>
              {providers.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service key" value={filters.service_key} onChange={(event) => setFilters({ ...filters, service_key: event.target.value.toUpperCase() })} disabled={tab !== "emds"} />
          </section>

          {tab === "tickets" ? <TicketList items={filteredTickets} /> : <EmdList items={filteredEmds} />}
          {modal ? <MirrorModal form={form} modal={modal} onChange={(updates) => setForm({ ...form, ...updates })} onClose={() => setModal("")} onSubmit={submitModal} working={working} /> : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function MirrorModal({ form, modal, onChange, onClose, onSubmit, working }) {
  const isTicket = modal === "ticket"
  const isEmd = modal === "emd"
  const isExchange = modal === "ticket_exchange" || modal === "emd_exchange"
  const title = {
    ticket: "Create manual ticket",
    emd: "Create manual EMD",
    ticket_exchange: "Start ticket exchange",
    emd_exchange: "Start EMD exchange",
  }[modal]
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <form className="max-h-[90vh] w-full max-w-6xl overflow-auto rounded-lg bg-white shadow-xl" onSubmit={onSubmit}>
        <div className="flex items-start justify-between gap-3 border-b border-slate-200 p-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Internal mirror only</p>
            <h3 className="text-xl font-semibold text-slate-950">{title}</h3>
            <p className="mt-1 text-sm text-slate-600">No provider action, issuance, exchange, refund, or void is performed.</p>
          </div>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onClose}>Close</button>
        </div>
        <div className="space-y-5 p-5">
          {isTicket ? <ManualTicketForm form={form} onChange={onChange} /> : null}
          {isEmd ? <ManualEmdForm form={form} onChange={onChange} /> : null}
          {isExchange ? <ExchangeForm form={form} modal={modal} onChange={onChange} /> : null}
        </div>
        <div className="flex justify-end border-t border-slate-200 p-5">
          <button className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working}>{working ? "Working..." : title}</button>
        </div>
      </form>
    </div>
  )
}

function ManualTicketForm({ form, onChange }) {
  return (
    <>
      <FormSection title="Ticket basics">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <Field label="Booking workspace id optional" value={form.booking_workspace_id} onChange={(value) => onChange({ booking_workspace_id: value })} />
          <Field label="Booking record id optional" value={form.booking_record_id} onChange={(value) => onChange({ booking_record_id: value })} />
          <Field label="Existing trip id/reference optional" value={form.trip_id} onChange={(value) => onChange({ trip_id: value })} />
          <Field label="Client id optional" value={form.client_id} onChange={(value) => onChange({ client_id: value })} />
          <Field label="Passenger id optional" value={form.passenger_id} onChange={(value) => onChange({ passenger_id: value })} />
          <Field label="Passenger display name optional" value={form.passenger_display_name} onChange={(value) => onChange({ passenger_display_name: value })} />
          <Field label="Passenger first name optional" value={form.passenger_first_name} onChange={(value) => onChange({ passenger_first_name: value })} />
          <Field label="Passenger last name optional" value={form.passenger_last_name} onChange={(value) => onChange({ passenger_last_name: value })} />
          <Field label="Ticket number" value={form.ticket_number} onChange={(value) => onChange({ ticket_number: value })} />
          <Field label="Validating carrier" value={form.validating_carrier} onChange={(value) => onChange({ validating_carrier: value.toUpperCase() })} />
          <Select label="Issuing provider" value={form.issuing_provider} options={providers} onChange={(value) => onChange({ issuing_provider: value })} />
          <Select label="Status" value={form.issue_status} options={statuses} onChange={(value) => onChange({ issue_status: value })} />
          <TextArea label="Internal notes" value={form.internal_notes} onChange={(value) => onChange({ internal_notes: value })} plain />
        </div>
      </FormSection>
      <FormSection title="Pricing">
        <PricingFields form={form} onChange={onChange} amountLabel="Base fare" />
      </FormSection>
      <TicketCouponsEditor form={form} onChange={onChange} />
      <AdvancedTicketSnapshots form={form} onChange={onChange} />
    </>
  )
}

function ManualEmdForm({ form, onChange }) {
  return (
    <>
      <FormSection title="EMD basics">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <Field label="Booking workspace id optional" value={form.booking_workspace_id} onChange={(value) => onChange({ booking_workspace_id: value })} />
          <Field label="Booking record id optional" value={form.booking_record_id} onChange={(value) => onChange({ booking_record_id: value })} />
          <Field label="Ticket record id optional" value={form.ticket_record_id} onChange={(value) => onChange({ ticket_record_id: value })} />
          <Field label="Existing trip id/reference optional" value={form.trip_id} onChange={(value) => onChange({ trip_id: value })} />
          <Field label="Client id optional" value={form.client_id} onChange={(value) => onChange({ client_id: value })} />
          <Field label="Passenger id optional" value={form.passenger_id} onChange={(value) => onChange({ passenger_id: value })} />
          <Field label="EMD number" value={form.emd_number} onChange={(value) => onChange({ emd_number: value })} />
          <Select label="EMD type" value={form.emd_type} options={emdTypes} onChange={(value) => onChange({ emd_type: value })} />
          <Select label="Status" value={form.emd_status} options={emdStatuses} onChange={(value) => onChange({ emd_status: value })} />
          <TextArea label="Internal notes" value={form.internal_notes} onChange={(value) => onChange({ internal_notes: value })} plain />
        </div>
      </FormSection>
      <FormSection title="Service">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          <Field label="Service key" value={form.service_key} onChange={(value) => onChange({ service_key: value.toUpperCase() })} />
          <Field label="Service catalogue id optional" value={form.service_catalogue_id} onChange={(value) => onChange({ service_catalogue_id: value })} />
          <Field label="Service label" value={form.service_label} onChange={(value) => onChange({ service_label: value })} />
          <Field label="Service category" value={form.service_category} onChange={(value) => onChange({ service_category: value })} />
          <Field label="Related ticket coupon ids optional" value={form.related_ticket_coupon_ids} onChange={(value) => onChange({ related_ticket_coupon_ids: value })} />
          <Field label="Related segment references optional" value={form.related_segment_references} onChange={(value) => onChange({ related_segment_references: value })} />
        </div>
      </FormSection>
      <FormSection title="Pricing">
        <PricingFields form={form} onChange={onChange} amountLabel="Amount" />
      </FormSection>
      <EmdCouponsEditor form={form} onChange={onChange} />
      <AdvancedEmdSnapshots form={form} onChange={onChange} />
    </>
  )
}

function ExchangeForm({ form, modal, onChange }) {
  const exchangeOptions = modal === "emd_exchange" ? ["exchange", "reissue", "void", "refund", "service_change", "other"] : ["exchange", "reissue", "void", "refund", "name_correction", "schedule_change_reissue", "other"]
  return (
    <FormSection title={modal === "emd_exchange" ? "EMD exchange" : "Ticket exchange"}>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        <Field label="Original record id" value={form.original_record_id} onChange={(value) => onChange({ original_record_id: value })} required />
        <Select label="Operation type" value={form.operation_type} options={exchangeOptions} onChange={(value) => onChange({ operation_type: value })} />
        <Field label="Booking record id optional" value={form.booking_record_id} onChange={(value) => onChange({ booking_record_id: value })} />
        <Field label="Existing trip id/reference optional" value={form.trip_id} onChange={(value) => onChange({ trip_id: value })} />
        <Field label="Currency" value={form.currency} onChange={(value) => onChange({ currency: value.toUpperCase() })} />
        <TextArea label="Reason / notes" value={form.internal_notes} onChange={(value) => onChange({ internal_notes: value })} plain />
      </div>
    </FormSection>
  )
}

function PricingFields({ amountLabel, form, onChange }) {
  return (
    <div className="grid gap-3 md:grid-cols-4">
      <Field label="Currency" value={form.currency} onChange={(value) => onChange({ currency: value.toUpperCase() })} />
      <Field label={amountLabel} type="number" value={form.base_fare_amount} onChange={(value) => onChange({ base_fare_amount: value })} />
      <Field label="Taxes" type="number" value={form.taxes_amount} onChange={(value) => onChange({ taxes_amount: value })} />
      <Field label="Total" type="number" value={form.total_amount} onChange={(value) => onChange({ total_amount: value })} />
    </div>
  )
}

function TicketCouponsEditor({ form, onChange }) {
  function update(index, updates) {
    onChange({ ticket_coupons: form.ticket_coupons.map((item, itemIndex) => itemIndex === index ? { ...item, ...updates } : item) })
  }
  function add() {
    onChange({ ticket_coupons: [...form.ticket_coupons, { ...emptyTicketCoupon, coupon_number: String(form.ticket_coupons.length + 1) }] })
  }
  function remove(index) {
    onChange({ ticket_coupons: form.ticket_coupons.filter((_, itemIndex) => itemIndex !== index) })
  }
  return (
    <FormSection title="Ticket coupons">
      <RepeatableHeader label="Ticket coupon" onAdd={add} />
      <div className="space-y-3">
        {form.ticket_coupons.map((coupon, index) => (
          <div className="rounded-lg border border-slate-200 p-3" key={`ticket-coupon-${index}`}>
            <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-4">
              <Field label="Coupon number" value={coupon.coupon_number} onChange={(value) => update(index, { coupon_number: value })} />
              <Field label="Marketing airline" value={coupon.marketing_airline} onChange={(value) => update(index, { marketing_airline: value.toUpperCase() })} />
              <Field label="Operating airline" value={coupon.operating_airline} onChange={(value) => update(index, { operating_airline: value.toUpperCase() })} />
              <Field label="Flight number" value={coupon.flight_number} onChange={(value) => update(index, { flight_number: value })} />
              <Field label="Departure airport" value={coupon.departure_airport} onChange={(value) => update(index, { departure_airport: value.toUpperCase() })} />
              <Field label="Arrival airport" value={coupon.arrival_airport} onChange={(value) => update(index, { arrival_airport: value.toUpperCase() })} />
              <Field label="Departure date" type="date" value={coupon.departure_date} onChange={(value) => update(index, { departure_date: value })} />
              <Field label="Departure time" type="time" value={coupon.departure_time} onChange={(value) => update(index, { departure_time: value })} />
              <Field label="Cabin" value={coupon.cabin} onChange={(value) => update(index, { cabin: value })} />
              <Field label="RBD" value={coupon.rbd} onChange={(value) => update(index, { rbd: value.toUpperCase() })} />
              <Field label="Status" value={coupon.status} onChange={(value) => update(index, { status: value })} />
              <Field label="Segment reference optional" value={coupon.segment_reference} onChange={(value) => update(index, { segment_reference: value })} />
            </div>
            <RemoveButton disabled={form.ticket_coupons.length === 1} label="Remove coupon" onClick={() => remove(index)} />
          </div>
        ))}
      </div>
    </FormSection>
  )
}

function EmdCouponsEditor({ form, onChange }) {
  function update(index, updates) {
    onChange({ emd_coupons: form.emd_coupons.map((item, itemIndex) => itemIndex === index ? { ...item, ...updates } : item) })
  }
  function add() {
    onChange({ emd_coupons: [...form.emd_coupons, { ...emptyEmdCoupon, coupon_number: String(form.emd_coupons.length + 1) }] })
  }
  function remove(index) {
    onChange({ emd_coupons: form.emd_coupons.filter((_, itemIndex) => itemIndex !== index) })
  }
  return (
    <FormSection title="EMD coupons">
      <RepeatableHeader label="EMD coupon" onAdd={add} />
      <div className="space-y-3">
        {form.emd_coupons.map((coupon, index) => (
          <div className="rounded-lg border border-slate-200 p-3" key={`emd-coupon-${index}`}>
            <div className="grid gap-3 md:grid-cols-3">
              <Field label="Coupon number" value={coupon.coupon_number} onChange={(value) => update(index, { coupon_number: value })} />
              <Field label="RFIC optional" value={coupon.rfic} onChange={(value) => update(index, { rfic: value.toUpperCase() })} />
              <Field label="RFISC optional" value={coupon.rfisc} onChange={(value) => update(index, { rfisc: value.toUpperCase() })} />
              <Field label="Service description" value={coupon.service_description} onChange={(value) => update(index, { service_description: value })} />
              <Field label="Status" value={coupon.status} onChange={(value) => update(index, { status: value })} />
              <Field label="Related segment reference optional" value={coupon.related_segment_reference} onChange={(value) => update(index, { related_segment_reference: value })} />
              <Field label="Related ticket coupon reference optional" value={coupon.related_ticket_coupon_reference} onChange={(value) => update(index, { related_ticket_coupon_reference: value })} />
            </div>
            <RemoveButton disabled={form.emd_coupons.length === 1} label="Remove coupon" onClick={() => remove(index)} />
          </div>
        ))}
      </div>
    </FormSection>
  )
}

function AdvancedTicketSnapshots({ form, onChange }) {
  return (
    <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced raw snapshots</summary>
      <p className="mt-2 text-sm text-slate-600">Advanced only. Structured fields above are used unless a raw override is provided.</p>
      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        <TextArea label="passenger_snapshot_json override" value={form.passenger_snapshot_json} onChange={(value) => onChange({ passenger_snapshot_json: value })} />
        <TextArea label="segments_snapshot_json override" value={form.segments_snapshot_json} onChange={(value) => onChange({ segments_snapshot_json: value })} />
        <TextArea label="pricing_snapshot_json override" value={form.pricing_snapshot_json} onChange={(value) => onChange({ pricing_snapshot_json: value })} />
      </div>
    </details>
  )
}

function AdvancedEmdSnapshots({ form, onChange }) {
  return (
    <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced raw snapshots</summary>
      <p className="mt-2 text-sm text-slate-600">Advanced only. Structured fields above are used unless a raw override is provided.</p>
      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        <TextArea label="linked_service_snapshot_json override" value={form.linked_service_snapshot_json} onChange={(value) => onChange({ linked_service_snapshot_json: value })} />
        <TextArea label="linked_segment_ids override" value={form.linked_segment_ids} onChange={(value) => onChange({ linked_segment_ids: value })} />
        <TextArea label="linked_ticket_coupon_ids override" value={form.linked_ticket_coupon_ids} onChange={(value) => onChange({ linked_ticket_coupon_ids: value })} />
      </div>
    </details>
  )
}

function TicketList({ items }) {
  if (!items.length) return <EmptyState title="No tickets found" body="Create draft ticket mirrors from a booking workspace." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="grid grid-cols-[1fr_1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <span>Ticket</span><span>Passenger</span><span>Booking workspace</span><span>Provider</span><span>Status</span><span>Amount</span>
      </div>
      <div className="divide-y divide-slate-100">
        {items.map((item) => (
          <a className="grid grid-cols-[1fr_1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 px-4 py-4 text-sm text-slate-700 hover:bg-blue-50/60" href={`/agency/tickets/${item.id}`} key={item.id}>
            <span className="font-semibold text-slate-950">{item.ticket_number || "Draft ticket"}</span>
            <span>{passengerName(item)}</span>
            <span>{item.booking_workspace_id || "Not linked"}</span>
            <span>{label(item.issuing_provider)}</span>
            <span>{label(item.issue_status || item.status)}</span>
            <span>{money(item.total_amount, item.currency)}</span>
          </a>
        ))}
      </div>
    </div>
  )
}

function EmdList({ items }) {
  if (!items.length) return <EmptyState title="No EMDs found" body="Create draft EMD mirrors from booking services." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="grid grid-cols-[1fr_1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <span>EMD</span><span>Service</span><span>Passenger</span><span>Provider</span><span>Status</span><span>Amount</span>
      </div>
      <div className="divide-y divide-slate-100">
        {items.map((item) => (
          <a className="grid grid-cols-[1fr_1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 px-4 py-4 text-sm text-slate-700 hover:bg-blue-50/60" href={`/agency/emds/${item.id}`} key={item.id}>
            <span className="font-semibold text-slate-950">{item.emd_number || "Draft EMD"}</span>
            <span>{item.service_label || item.service_key || "Manual service"}</span>
            <span>{passengerName(item)}</span>
            <span>{label(item.issuing_provider)}</span>
            <span>{label(item.issue_status || item.status)}</span>
            <span>{money(item.total_amount ?? item.amount, item.currency)}</span>
          </a>
        ))}
      </div>
    </div>
  )
}

function FormSection({ title, children }) {
  return (
    <section className="space-y-3 border-t border-slate-200 pt-4 first:border-t-0 first:pt-0">
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      {children}
    </section>
  )
}

function RepeatableHeader({ label: itemLabel, onAdd }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <p className="text-sm text-slate-600">{itemLabel} rows</p>
      <button className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-semibold" type="button" onClick={onAdd}>Add {itemLabel.toLowerCase()}</button>
    </div>
  )
}

function RemoveButton({ disabled, label: buttonLabel, onClick }) {
  return (
    <button className="mt-3 rounded-md border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-600 disabled:opacity-50" type="button" onClick={onClick} disabled={disabled}>
      {buttonLabel}
    </button>
  )
}

function Field({ label: fieldLabel, required, type = "text", value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" required={required} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label: fieldLabel, value, options, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{label(option)}</option>)}
      </select>
    </label>
  )
}

function TextArea({ label: fieldLabel, plain, value, onChange }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {fieldLabel}
      <textarea className={`mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-xs ${plain ? "" : "font-mono"}`} spellCheck={plain ? undefined : false} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function buildManualTicketPayload(form) {
  const passengerSnapshot = valueOrOverride("Passenger snapshot", form.passenger_snapshot_json, buildPassengerSnapshot(form))
  const segmentsSnapshot = valueOrOverride("Ticket coupon snapshot", form.segments_snapshot_json, buildTicketCouponsSnapshot(form.ticket_coupons))
  const pricingSnapshot = valueOrOverride("Pricing snapshot", form.pricing_snapshot_json, buildTicketPricingSnapshot(form))
  return {
    booking_record_id: form.booking_record_id || null,
    booking_workspace_id: form.booking_workspace_id || null,
    trip_id: form.trip_id || null,
    client_id: form.client_id || null,
    passenger_id: form.passenger_id || null,
    passenger_snapshot_json: asObject(passengerSnapshot, "Passenger snapshot"),
    ticket_number: form.ticket_number || null,
    validating_carrier: form.validating_carrier || null,
    issuing_provider: form.issuing_provider || "manual",
    issue_status: form.issue_status || "draft",
    currency: form.currency || null,
    base_fare_amount: amount(form.base_fare_amount),
    taxes_amount: amount(form.taxes_amount),
    total_amount: amount(form.total_amount),
    pricing_snapshot_json: asObject(pricingSnapshot, "Pricing snapshot"),
    segments_snapshot_json: asArray(segmentsSnapshot, "Ticket coupon snapshot"),
    internal_notes: form.internal_notes || null,
    source_context: "standalone_manual",
  }
}

function buildManualEmdPayload(form) {
  const coupons = buildEmdCouponsSnapshot(form.emd_coupons)
  const linkedService = valueOrOverride("Linked service snapshot", form.linked_service_snapshot_json, buildEmdServiceSnapshot(form, coupons))
  const linkedSegmentIds = valueOrOverride("Linked segment ids", form.linked_segment_ids, mergeUnique(splitIds(form.related_segment_references), coupons.map((item) => item.related_segment_reference).filter(Boolean)))
  const linkedTicketCouponIds = valueOrOverride("Linked ticket coupon ids", form.linked_ticket_coupon_ids, mergeUnique(splitIds(form.related_ticket_coupon_ids), coupons.map((item) => item.related_ticket_coupon_reference).filter(Boolean)))
  return {
    booking_record_id: form.booking_record_id || null,
    booking_workspace_id: form.booking_workspace_id || null,
    ticket_record_id: form.ticket_record_id || null,
    trip_id: form.trip_id || null,
    client_id: form.client_id || null,
    passenger_id: form.passenger_id || null,
    emd_number: form.emd_number || null,
    emd_type: form.emd_type || "manual_mirror",
    issue_status: form.emd_status || "draft",
    service_key: form.service_key || null,
    service_catalogue_id: form.service_catalogue_id || null,
    service_label: form.service_label || null,
    service_category: form.service_category || null,
    linked_service_snapshot_json: asObject(linkedService, "Linked service snapshot"),
    linked_segment_ids: asArray(linkedSegmentIds, "Linked segment ids"),
    linked_ticket_coupon_ids: asArray(linkedTicketCouponIds, "Linked ticket coupon ids"),
    currency: form.currency || null,
    amount: amount(form.base_fare_amount),
    taxes_amount: amount(form.taxes_amount),
    total_amount: amount(form.total_amount),
    internal_notes: form.internal_notes || null,
    source_context: "standalone_manual",
  }
}

function buildPassengerSnapshot(form) {
  const displayName = form.passenger_display_name || [form.passenger_first_name, form.passenger_last_name].filter(Boolean).join(" ").trim()
  return compactObject({
    id: form.passenger_id,
    passenger_id: form.passenger_id,
    display_name: displayName,
    first_name: form.passenger_first_name,
    last_name: form.passenger_last_name,
  })
}

function buildTicketCouponsSnapshot(rows) {
  return rows.map((row, index) => compactObject({
    id: hasMeaningfulValues(row, ["marketing_airline", "flight_number", "departure_airport", "arrival_airport", "segment_reference"]) ? row.segment_reference || `manual-coupon-${index + 1}` : "",
    coupon_number: numberOrNull(row.coupon_number) || index + 1,
    sequence: numberOrNull(row.coupon_number) || index + 1,
    marketing_airline_code: row.marketing_airline,
    operating_airline_code: row.operating_airline,
    flight_number: row.flight_number,
    origin_airport_code: row.departure_airport,
    destination_airport_code: row.arrival_airport,
    departure_date: row.departure_date,
    departure_time: row.departure_time,
    departure_datetime: combineDateTime(row.departure_date, row.departure_time),
    cabin: row.cabin,
    booking_class: row.rbd,
    rbd: row.rbd,
    status: row.status,
    segment_reference: row.segment_reference,
  })).filter((item) => hasMeaningfulValues(item, ["marketing_airline_code", "flight_number", "origin_airport_code", "destination_airport_code", "departure_date", "segment_reference"]))
}

function buildTicketPricingSnapshot(form) {
  const summary = compactObject({
    currency: form.currency || "EUR",
    base_fare_amount: amount(form.base_fare_amount),
    taxes_amount: amount(form.taxes_amount),
    total_amount: amount(form.total_amount),
  })
  return Object.keys(summary).length ? { summary } : {}
}

function buildEmdCouponsSnapshot(rows) {
  return rows.map((row, index) => compactObject({
    coupon_number: numberOrNull(row.coupon_number) || index + 1,
    rfic: row.rfic,
    rfisc: row.rfisc,
    service_description: row.service_description,
    status: row.status,
    related_segment_reference: row.related_segment_reference,
    related_ticket_coupon_reference: row.related_ticket_coupon_reference,
  })).filter((item) => hasMeaningfulValues(item, ["rfic", "rfisc", "service_description", "related_segment_reference", "related_ticket_coupon_reference"]))
}

function buildEmdServiceSnapshot(form, coupons) {
  return compactObject({
    service_key: form.service_key,
    service_catalogue_id: form.service_catalogue_id,
    service_label: form.service_label,
    service_category: form.service_category,
    currency: form.currency,
    amount: amount(form.base_fare_amount),
    taxes_amount: amount(form.taxes_amount),
    total_amount: amount(form.total_amount),
    emd_coupons: coupons,
  })
}

function valueOrOverride(labelText, rawValue, fallback) {
  const parsed = parseOptionalJsonOverride(labelText, rawValue)
  return parsed === undefined ? fallback : parsed
}

function parseOptionalJsonOverride(labelText, value) {
  const text = String(value || "").trim()
  if (!text) return undefined
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`${labelText} raw override must be valid JSON.`)
  }
}

function asArray(value, labelText) {
  if (Array.isArray(value)) return value
  throw new Error(`${labelText} must be a JSON array.`)
}

function asObject(value, labelText) {
  if (value && typeof value === "object" && !Array.isArray(value)) return value
  throw new Error(`${labelText} must be a JSON object.`)
}

function compactObject(item) {
  return Object.fromEntries(Object.entries(item).filter(([, value]) => value !== "" && value !== null && value !== undefined))
}

function hasMeaningfulValues(item, keys) {
  return keys.some((key) => String(item[key] || "").trim())
}

function splitIds(value) {
  return String(value || "").split(/[,\n]/).map((item) => item.trim()).filter(Boolean)
}

function mergeUnique(...lists) {
  return [...new Set(lists.flat().filter(Boolean))]
}

function combineDateTime(dateValue, timeValue) {
  if (!dateValue) return undefined
  return timeValue ? `${dateValue}T${timeValue}:00` : dateValue
}

function passengerName(item) {
  const passenger = item.passenger_snapshot_json || {}
  return passenger.display_name || passenger.snapshot_display_name || `${passenger.first_name || ""} ${passenger.last_name || ""}`.trim() || item.passenger_id || "Passenger"
}

function defaultForm() {
  return {
    booking_record_id: "",
    booking_workspace_id: "",
    trip_id: "",
    client_id: "",
    passenger_id: "",
    passenger_display_name: "",
    passenger_first_name: "",
    passenger_last_name: "",
    ticket_record_id: "",
    ticket_number: "",
    validating_carrier: "",
    issuing_provider: "manual",
    issue_status: "draft",
    emd_number: "",
    emd_type: "manual_mirror",
    emd_status: "draft",
    service_key: "",
    service_catalogue_id: "",
    service_label: "",
    service_category: "",
    related_ticket_coupon_ids: "",
    related_segment_references: "",
    original_record_id: "",
    operation_type: "exchange",
    currency: "EUR",
    base_fare_amount: "",
    taxes_amount: "",
    total_amount: "",
    ticket_coupons: [{ ...emptyTicketCoupon }],
    emd_coupons: [{ ...emptyEmdCoupon }],
    passenger_snapshot_json: "",
    segments_snapshot_json: "",
    pricing_snapshot_json: "",
    linked_service_snapshot_json: "",
    linked_segment_ids: "",
    linked_ticket_coupon_ids: "",
    internal_notes: "",
  }
}

function amount(value) {
  if (value === "" || value === null || value === undefined) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function numberOrNull(value) {
  return amount(value)
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function money(amountValue, currency) {
  if (amountValue === null || amountValue === undefined || amountValue === "") return "Not priced"
  return `${Number(amountValue).toFixed(2)} ${currency || "EUR"}`
}
