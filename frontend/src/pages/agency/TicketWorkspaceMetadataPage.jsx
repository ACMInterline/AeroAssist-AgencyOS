import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statusOptions = ["draft", "review", "ready", "archived"]
const documentStatusOptions = ["draft_metadata", "issued", "voided", "exchanged", "refunded", "partially_refunded", "cancelled", "unknown"]

const defaultFilters = {
  status: "",
  document_status: "",
  validating_carrier: "",
  issue_date: "",
  passenger: "",
  booking_reference: "",
  currency: "",
}

export default function TicketWorkspaceMetadataPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [tickets, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/ticket-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/ticket-workspaces/summary`),
    ])
    setState({
      ...context,
      tickets: tickets.items || [],
      summary: tickets.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.status, filters.document_status, filters.validating_carrier, filters.issue_date, filters.passenger, filters.booking_reference, filters.currency])

  const metrics = [
    ["Tickets", state?.tickets?.length || 0],
    ["Ready", state?.summary?.by_status?.ready || 0],
    ["Issued docs", state?.summary?.by_document_status?.issued || 0],
    ["Documents", state?.summary?.linked_document_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Daily Work</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Tickets</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only ticket workspace metadata. These records do not issue, reissue, void, refund, exchange, process payments, connect to GDS or NDC, call airline APIs, calculate fares, validate coupons, run background workers, or integrate external providers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No ticket issuance</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Ticket filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-7">
              <SelectField label="Workspace status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <SelectField label="Document status" value={filters.document_status} onChange={(value) => setFilters({ ...filters, document_status: value })} options={documentStatusOptions.map((item) => [item, formatType(item)])} placeholder="All document statuses" />
              <Field label="Validating carrier" value={filters.validating_carrier} onChange={(value) => setFilters({ ...filters, validating_carrier: value })} />
              <Field label="Issue date" type="date" value={filters.issue_date} onChange={(value) => setFilters({ ...filters, issue_date: value })} />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Booking reference" value={filters.booking_reference} onChange={(value) => setFilters({ ...filters, booking_reference: value })} />
              <Field label="Currency" value={filters.currency} onChange={(value) => setFilters({ ...filters, currency: value.toUpperCase() })} />
            </div>
          </section>

          {state?.tickets?.length ? <TicketList tickets={state.tickets} /> : <EmptyState title="No ticket workspaces" body="Ticket workspace metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function TicketList({ tickets }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Ticket reference</th>
            <th className="px-4 py-3">Statuses</th>
            <th className="px-4 py-3">Passenger</th>
            <th className="px-4 py-3">Carrier and dates</th>
            <th className="px-4 py-3">Booking links</th>
            <th className="px-4 py-3">Fare construction</th>
            <th className="px-4 py-3">Coupons</th>
            <th className="px-4 py-3">Pricing components</th>
            <th className="px-4 py-3">Linked records</th>
            <th className="px-4 py-3">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {tickets.map((ticket) => (
            <tr key={ticket.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{ticket.ticket_display_name}</p>
                <p className="mt-1 text-xs text-slate-500">{ticket.ticket_reference}</p>
                <a className="mt-2 inline-flex text-xs font-semibold text-blue-700 hover:text-blue-900" href={`/agency/journeys?source_entity_type=ticket_workspace&source_entity_id=${encodeURIComponent(ticket.id)}`}>View Journey Snapshot</a>
                <p className="mt-1 text-xs text-slate-500">{ticket.ticket_number || "Ticket number unset"}</p>
                <p className="mt-2 text-xs text-slate-500">{ticket.ticket_type || "Ticket type unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p className="font-semibold text-slate-700">Workspace</p>
                <StatusBadge status={ticket.ticket_status} />
                <p className="mt-3 font-semibold text-slate-700">Ticket document</p>
                <DocumentStatusBadge status={ticket.ticket_document_status} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{ticket.passenger_name || ticket.passenger?.label || "Passenger unset"}</p>
                <p className="mt-1">{ticket.passenger_id || "Passenger ID unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Carrier: {ticket.validating_carrier || "Unset"}</p>
                <p className="mt-1">Issue date: {formatDate(ticket.issue_date)}</p>
                <p className="mt-1">Issuing agent: {ticket.issuing_agent || "Unset"}</p>
                <p className="mt-1">Office: {ticket.issuing_office || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Booking reference: {ticket.booking_reference || "Unset"}</p>
                <p className="mt-1">Airline PNR: {ticket.airline_pnr || "Unset"}</p>
                <p className="mt-1">GDS locator: {ticket.gds_record_locator || "Unset"}</p>
                <p className="mt-1">Trip: {ticket.trip_workspace?.label || ticket.trip_workspace_id || "Unset"}</p>
                <p className="mt-1">Offer: {ticket.offer_workspace?.label || ticket.offer_workspace_id || "Unset"}</p>
                <p className="mt-1">Booking: {ticket.booking_workspace?.label || ticket.booking_workspace_id || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Fare basis: {ticket.fare_basis_summary || "Unset"}</p>
                <p className="mt-1">Fare: {formatMoney(ticket.fare_amount, ticket.currency)}</p>
                <p className="mt-1">Taxes: {formatMoney(ticket.taxes_amount, ticket.currency)}</p>
                <p className="mt-1">Total: {formatMoney(ticket.total_amount, ticket.currency)}</p>
                <p className="mt-2 font-semibold text-slate-700">Fare calculation line</p>
                <p className="mt-1">{ticket.fare_calculation_line || "Unset"}</p>
                <p className="mt-1">NUC total: {formatMoney(ticket.fare_calculation_nuc_total, ticket.fare_calculation_currency)}</p>
                <p className="mt-1">ROE: {ticket.fare_calculation_roe || "Unset"}</p>
                <p className="mt-1">Equivalent fare paid: {formatMoney(ticket.equivalent_fare_paid, ticket.equivalent_fare_currency)}</p>
                <p className="mt-2 font-semibold text-slate-700">Payment</p>
                <p className="mt-1">Form of payment: {ticket.form_of_payment || "Unset"}</p>
                <p className="mt-1">Payment reference: {ticket.payment_reference || "Unset"}</p>
                <p className="mt-1">Payment restrictions: {ticket.payment_restrictions || "Unset"}</p>
                <p className="mt-1">Commission: {ticket.commission_summary || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Summary: {ticket.coupon_status_summary || ticket.coupon_summary || "Unset"}</p>
                <CouponDetails details={ticket.coupon_details} />
                <p className="mt-1">Baggage: {ticket.baggage_summary || "Unset"}</p>
                <p className="mt-1">Endorsements: {ticket.endorsement_summary || "Unset"}</p>
                <p className="mt-1">Restrictions: {ticket.restrictions_summary || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <TaxBreakdown items={ticket.tax_breakdown} />
                <PricingUnits items={ticket.pricing_units} />
                <FareComponents items={ticket.fare_components} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Flights" items={ticket.flight_workspaces?.map((item) => item.label || item.flight_workspace_id)} />
                <ReferenceLine label="EMDs" items={ticket.linked_emds?.map((item) => item.label || item.emd_id)} />
                <ReferenceLine label="Documents" items={ticket.linked_documents?.map((item) => item.label || item.document_id)} />
                <ReferenceLine label="Exchange refs" items={ticket.exchange_reference_ids} />
                <ReferenceLine label="Refund refs" items={ticket.refund_reference_ids} />
                <ReferenceLine label="Void refs" items={ticket.void_reference_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Fare construction: {ticket.fare_construction_notes || "No fare construction notes"}</p>
                <p>Lifecycle: {ticket.lifecycle_notes || "No lifecycle notes"}</p>
                <p className="mt-1">Operational: {ticket.operational_notes || "No operational notes"}</p>
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

function Field({ label, type = "text", value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" type={type} value={value} onChange={(event) => onChange(event.target.value)} />
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

function CouponDetails({ details }) {
  const coupons = details || []
  if (!coupons.length) return <p className="mt-1">Coupon details: None</p>
  return (
    <div className="mt-2 space-y-2">
      {coupons.map((coupon, index) => (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-2" key={`${coupon.coupon_number || index}-${coupon.segment_reference || "coupon"}`}>
          <p className="font-semibold text-slate-700">Coupon {coupon.coupon_number || index + 1}: {formatType(coupon.coupon_status)}</p>
          <p className="mt-1">{coupon.origin || "Origin unset"} to {coupon.destination || "destination unset"}</p>
          <p className="mt-1">Segment: {coupon.segment_reference || "Unset"}</p>
          <p className="mt-1">Flight: {coupon.flight_workspace_id || "Unset"}</p>
          <p className="mt-1">Marketing carrier: {coupon.marketing_carrier || "Unset"}</p>
          <p className="mt-1">Operating carrier: {coupon.operating_carrier || "Unset"}</p>
          <p className="mt-1">Fare component: {coupon.fare_component_reference || "Unset"}</p>
          <p className="mt-1">Pricing unit: {coupon.pricing_unit_reference || "Unset"}</p>
          <p className="mt-1">Coupon-level fare basis: {coupon.fare_basis || "Unset"}</p>
          <p className="mt-1">Validity: {formatDate(coupon.not_valid_before)} to {formatDate(coupon.not_valid_after)}</p>
          <p className="mt-1">Baggage: {coupon.baggage_summary || "Unset"}</p>
          <p className="mt-1">Remarks: {coupon.remarks || "Unset"}</p>
        </div>
      ))}
    </div>
  )
}

function TaxBreakdown({ items }) {
  const taxes = items || []
  if (!taxes.length) return <p>Tax breakdown: None</p>
  return (
    <div>
      <p className="font-semibold text-slate-700">Tax breakdown</p>
      {taxes.map((tax, index) => (
        <p className="mt-1" key={`${tax.tax_code || "tax"}-${index}`}>{formatTax(tax)}</p>
      ))}
    </div>
  )
}

function PricingUnits({ items }) {
  const units = items || []
  if (!units.length) return <p className="mt-2">Pricing units: None</p>
  return (
    <div className="mt-2 space-y-2">
      <p className="font-semibold text-slate-700">Pricing units</p>
      {units.map((unit, index) => (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-2" key={`${unit.pricing_unit_reference || "unit"}-${index}`}>
          <p>{unit.pricing_unit_reference || `Unit ${index + 1}`}: {unit.pricing_unit_type || "Type unset"}</p>
          <p className="mt-1">{unit.origin || "Origin unset"} to {unit.destination || "destination unset"}</p>
          <p className="mt-1">Fare components: {formatList(unit.fare_component_references)}</p>
          <p className="mt-1">NUC amount: {formatMoney(unit.nuc_amount, unit.currency)}</p>
          <p className="mt-1">Notes: {unit.notes || "Unset"}</p>
        </div>
      ))}
    </div>
  )
}

function FareComponents({ items }) {
  const components = items || []
  if (!components.length) return <p className="mt-2">Fare components: None</p>
  return (
    <div className="mt-2 space-y-2">
      <p className="font-semibold text-slate-700">Fare components</p>
      {components.map((component, index) => (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-2" key={`${component.fare_component_reference || "component"}-${index}`}>
          <p>{component.fare_component_reference || `Component ${index + 1}`}: {component.origin || "Origin unset"} to {component.destination || "destination unset"}</p>
          <p className="mt-1">Carrier: {component.carrier || "Unset"}</p>
          <p className="mt-1">Fare basis: {component.fare_basis || "Unset"}</p>
          <p className="mt-1">Booking class: {component.booking_class || "Unset"}</p>
          <p className="mt-1">NUC amount: {formatMoney(component.nuc_amount, null)}</p>
          <p className="mt-1">Mileage/routing: {component.mileage_or_routing_note || "Unset"}</p>
          <p className="mt-1">Rule: {component.rule_reference || "Unset"}</p>
          <p className="mt-1">Notes: {component.notes || "Unset"}</p>
        </div>
      ))}
    </div>
  )
}

function StatusBadge({ status }) {
  const tones = {
    ready: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    review: "bg-sky-50 text-sky-700 ring-sky-200",
    archived: "bg-zinc-100 text-zinc-600 ring-zinc-200",
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[status] || "bg-slate-100 text-slate-700 ring-slate-200"}`}>{formatType(status)}</span>
}

function DocumentStatusBadge({ status }) {
  const tones = {
    issued: "bg-blue-50 text-blue-700 ring-blue-200",
    voided: "bg-amber-50 text-amber-700 ring-amber-200",
    exchanged: "bg-cyan-50 text-cyan-700 ring-cyan-200",
    refunded: "bg-purple-50 text-purple-700 ring-purple-200",
    partially_refunded: "bg-fuchsia-50 text-fuchsia-700 ring-fuchsia-200",
    cancelled: "bg-zinc-100 text-zinc-600 ring-zinc-200",
    unknown: "bg-slate-100 text-slate-700 ring-slate-200",
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[status] || "bg-slate-100 text-slate-700 ring-slate-200"}`}>{formatType(status)}</span>
}

function queryString(filters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatList(items) {
  const values = (items || []).filter(Boolean)
  return values.length ? values.join(", ") : "None"
}

function formatType(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString() : "Unset"
}

function formatMoney(value, currency) {
  if (value === null || value === undefined || value === "") return "Unset"
  return `${currency ? `${currency} ` : ""}${Number(value).toLocaleString()}`
}

function formatTax(tax) {
  const code = tax.tax_code || tax.code || "Tax"
  const amount = tax.amount === null || tax.amount === undefined ? "amount unset" : formatMoney(tax.amount, tax.currency)
  const note = tax.description || tax.notes
  return note ? `${code}: ${amount} (${note})` : `${code}: ${amount}`
}
