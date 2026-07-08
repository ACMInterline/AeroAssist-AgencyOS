import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statusOptions = ["draft", "review", "ready", "archived"]
const typeOptions = ["ancillary", "service", "penalty", "residual", "misc"]
const aOrSOptions = ["EMD-A", "EMD-S"]

const defaultFilters = {
  status: "",
  emd_type: "",
  emd_a_or_s: "",
  validating_carrier: "",
  passenger: "",
  rfic: "",
  rfisc: "",
  service_category: "",
  issue_date: "",
}

export default function EmdWorkspaceMetadataPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [emds, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/emd-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/emd-workspaces/summary`),
    ])
    setState({
      ...context,
      emds: emds.items || [],
      summary: emds.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.status, filters.emd_type, filters.emd_a_or_s, filters.validating_carrier, filters.passenger, filters.rfic, filters.rfisc, filters.service_category, filters.issue_date])

  const metrics = [
    ["EMDs", state?.emds?.length || 0],
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
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">EMDs</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only EMD workspace metadata. These records do not issue, exchange, refund, void, validate RFIC/RFISC, transmit SSR/OSI, process payments, connect to GDS or NDC, call airline APIs, run background workers, or create duplicate EMD architecture.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No EMD issuance</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">EMD filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-9">
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <SelectField label="Type" value={filters.emd_type} onChange={(value) => setFilters({ ...filters, emd_type: value })} options={typeOptions.map((item) => [item, formatType(item)])} placeholder="All types" />
              <SelectField label="A/S" value={filters.emd_a_or_s} onChange={(value) => setFilters({ ...filters, emd_a_or_s: value })} options={aOrSOptions.map((item) => [item, item])} placeholder="All" />
              <Field label="Carrier" value={filters.validating_carrier} onChange={(value) => setFilters({ ...filters, validating_carrier: value.toUpperCase() })} />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="RFIC" value={filters.rfic} onChange={(value) => setFilters({ ...filters, rfic: value.toUpperCase() })} />
              <Field label="RFISC" value={filters.rfisc} onChange={(value) => setFilters({ ...filters, rfisc: value.toUpperCase() })} />
              <Field label="Service category" value={filters.service_category} onChange={(value) => setFilters({ ...filters, service_category: value })} />
              <Field label="Issue date" type="date" value={filters.issue_date} onChange={(value) => setFilters({ ...filters, issue_date: value })} />
            </div>
          </section>

          {state?.emds?.length ? <EmdList emds={state.emds} /> : <EmptyState title="No EMD workspaces" body="EMD workspace metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function EmdList({ emds }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">EMD reference</th>
            <th className="px-4 py-3">Statuses</th>
            <th className="px-4 py-3">Passenger</th>
            <th className="px-4 py-3">Carrier and issue</th>
            <th className="px-4 py-3">Ticket links</th>
            <th className="px-4 py-3">Service</th>
            <th className="px-4 py-3">Coupons</th>
            <th className="px-4 py-3">Amounts</th>
            <th className="px-4 py-3">References</th>
            <th className="px-4 py-3">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {emds.map((emd) => (
            <tr key={emd.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{emd.emd_display_name}</p>
                <p className="mt-1 text-xs text-slate-500">{emd.emd_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{emd.emd_number || "EMD number unset"}</p>
                <p className="mt-2 text-xs text-slate-500">{emd.emd_type || "Type unset"} {emd.emd_a_or_s ? `(${emd.emd_a_or_s})` : ""}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p className="font-semibold text-slate-700">Workspace</p>
                <StatusBadge status={emd.emd_status} />
                <p className="mt-3 font-semibold text-slate-700">EMD document</p>
                <DocumentStatusBadge status={emd.emd_document_status} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{emd.passenger_name || "Passenger unset"}</p>
                <p className="mt-1">{emd.passenger_id || "Passenger ID unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Validating carrier: {emd.validating_carrier || "Unset"}</p>
                <p className="mt-1">Issue date: {formatDate(emd.issue_date)}</p>
                <p className="mt-1">Issuing agent: {emd.issuing_agent || "Unset"}</p>
                <p className="mt-1">Office: {emd.issuing_office || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Booking reference: {emd.booking_reference || "Unset"}</p>
                <p className="mt-1">Airline PNR: {emd.airline_pnr || "Unset"}</p>
                <p className="mt-1">GDS locator: {emd.gds_record_locator || "Unset"}</p>
                <p className="mt-1">Associated ticket: {emd.associated_ticket_number || "Unset"}</p>
                <ReferenceLine label="Ticket coupons" items={emd.associated_ticket_coupon_numbers} />
                <ReferenceLine label="Associated flights" items={emd.associated_flight_workspace_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>RFIC/RFISC: {emd.rfic || "Unset"} / {emd.rfisc || "Unset"}</p>
                <p className="mt-1">Reason: {emd.service_reason || "Unset"}</p>
                <p className="mt-1">Description: {emd.service_description || "Unset"}</p>
                <p className="mt-1">Category: {emd.service_category || "Unset"}</p>
                <p className="mt-1">Service status: {emd.service_status || "Unset"}</p>
                <p className="mt-1">Quantity: {emd.service_quantity ?? "Unset"}</p>
                <p className="mt-1">Route scope: {emd.service_route_scope || "Unset"}</p>
                <p className="mt-1">Segment scope: {emd.service_segment_scope || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Summary: {emd.emd_coupon_status_summary || "Unset"}</p>
                <CouponDetails details={emd.emd_coupon_details} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Fare: {formatMoney(emd.fare_amount, emd.currency)}</p>
                <p className="mt-1">Taxes: {formatMoney(emd.taxes_amount, emd.currency)}</p>
                <p className="mt-1">Total: {formatMoney(emd.total_amount, emd.currency)}</p>
                <p className="mt-2">Form of payment: {emd.form_of_payment || "Unset"}</p>
                <p className="mt-1">Payment reference: {emd.payment_reference || "Unset"}</p>
                <p className="mt-1">Payment restrictions: {emd.payment_restrictions || "Unset"}</p>
                <TaxBreakdown items={emd.tax_breakdown} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="SSR" items={emd.ssr_ids} />
                <ReferenceLine label="OSI" items={emd.osi_ids} />
                <ReferenceLine label="Ancillary services" items={emd.ancillary_service_ids} />
                <ReferenceLine label="Exchange refs" items={emd.exchange_reference_ids} />
                <ReferenceLine label="Refund refs" items={emd.refund_reference_ids} />
                <ReferenceLine label="Void refs" items={emd.void_reference_ids} />
                <ReferenceLine label="Documents" items={emd.linked_document_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Lifecycle: {emd.lifecycle_notes || "No lifecycle notes"}</p>
                <p className="mt-1">Operational: {emd.operational_notes || "No operational notes"}</p>
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
          <p className="mt-1">Associated ticket: {coupon.associated_ticket_number || "Unset"}</p>
          <p className="mt-1">Associated ticket coupon: {coupon.associated_ticket_coupon_number || "Unset"}</p>
          <p className="mt-1">RFIC/RFISC: {coupon.rfic || "Unset"} / {coupon.rfisc || "Unset"}</p>
          <p className="mt-1">Service: {coupon.service_description || "Unset"}</p>
          <p className="mt-1">Validity: {formatDate(coupon.not_valid_before)} to {formatDate(coupon.not_valid_after)}</p>
          <p className="mt-1">Amount: {formatMoney(coupon.amount, coupon.currency)}</p>
          <p className="mt-1">Remarks: {coupon.remarks || "Unset"}</p>
        </div>
      ))}
    </div>
  )
}

function TaxBreakdown({ items }) {
  const taxes = items || []
  if (!taxes.length) return <p className="mt-2">Tax breakdown: None</p>
  return (
    <div className="mt-2">
      <p className="font-semibold text-slate-700">Tax breakdown</p>
      {taxes.map((tax, index) => (
        <p className="mt-1" key={`${tax.tax_code || "tax"}-${index}`}>{formatTax(tax)}</p>
      ))}
    </div>
  )
}

function StatusBadge({ status }) {
  return <span className="mt-1 inline-flex rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">{formatType(status || "draft")}</span>
}

function DocumentStatusBadge({ status }) {
  return <span className="mt-1 inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{formatType(status || "draft_metadata")}</span>
}

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const query = params.toString()
  return query ? `?${query}` : ""
}

function formatList(items) {
  const list = (items || []).filter(Boolean)
  return list.length ? list.join(", ") : "None"
}

function formatType(value) {
  if (!value) return "Unset"
  return String(value).replaceAll("_", " ")
}

function formatDate(value) {
  if (!value) return "Unset"
  return String(value).slice(0, 10)
}

function formatMoney(value, currency) {
  if (value === undefined || value === null || value === "") return "Unset"
  return `${value} ${currency || ""}`.trim()
}

function formatTax(tax) {
  return `${tax.tax_code || "Tax"} ${formatMoney(tax.amount, tax.currency)} ${tax.description || ""}`.trim()
}
