import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "ready_to_issue", "issued", "voided", "refunded", "exchanged", "cancelled"]
const emdTypes = ["emd_a", "emd_s", "manual_mirror", "unknown"]

export default function EmdDetailPage({ emdRecordId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ emd_number: "", emd_type: "manual_mirror", reason_for_issuance_code: "", reason_for_issuance_subcode: "", issue_status: "draft", currency: "EUR", amount: "", taxes_amount: "", total_amount: "", internal_notes: "" })
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [detail, serviceCases] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/emds/${emdRecordId}`),
      apiGet(`/api/agencies/${context.agency.id}/passenger-services`),
    ])
    setState({ ...context, ...detail, serviceCases: serviceCases.items || [] })
    setForm({
      emd_number: detail.emd?.emd_number || "",
      emd_type: detail.emd?.emd_type || "manual_mirror",
      reason_for_issuance_code: detail.emd?.reason_for_issuance_code || detail.emd?.rfic_code || "",
      reason_for_issuance_subcode: detail.emd?.reason_for_issuance_subcode || detail.emd?.rfisc_code || "",
      issue_status: detail.emd?.issue_status || detail.emd?.status || "draft",
      currency: detail.emd?.currency || "EUR",
      amount: amountValue(detail.emd?.amount),
      taxes_amount: amountValue(detail.emd?.taxes_amount),
      total_amount: amountValue(detail.emd?.total_amount),
      internal_notes: detail.emd?.internal_notes || "",
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [emdRecordId])

  async function save(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await apiPut(`/api/agencies/${state.agency.id}/emds/${emdRecordId}`, {
        emd_number: form.emd_number || null,
        emd_type: form.emd_type,
        reason_for_issuance_code: form.reason_for_issuance_code || null,
        reason_for_issuance_subcode: form.reason_for_issuance_subcode || null,
        issue_status: form.issue_status,
        currency: form.currency || null,
        amount: numberOrNull(form.amount),
        taxes_amount: numberOrNull(form.taxes_amount),
        total_amount: numberOrNull(form.total_amount),
        internal_notes: form.internal_notes || null,
      })
      setMessage("EMD mirror updated.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const emd = state?.emd
  const passenger = emd?.passenger_snapshot_json || {}
  const serviceCase = state?.serviceCases?.find((item) => (item.emd_record_ids || []).includes(emdRecordId))
    || state?.serviceCases?.find((item) => emd?.service_key && item.trip_id === emd?.trip_id && item.passenger_id === emd?.passenger_id && (item.service_key === emd.service_key || item.service_type === emd.service_key))
    || null
  const serviceHref = serviceCase
    ? `/agency/passenger-services?service_id=${encodeURIComponent(serviceCase.id)}&emd_record_id=${encodeURIComponent(emdRecordId)}${emd?.booking_workspace_id ? `&booking_workspace_id=${encodeURIComponent(emd.booking_workspace_id)}` : ""}${emd?.booking_record_id ? `&booking_record_id=${encodeURIComponent(emd.booking_record_id)}` : ""}`
    : "/agency/passenger-services"

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <a className="text-sm font-medium text-blue-700" href="/agency/tickets-emds">Back to Tickets & EMDs</a>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{label(emd?.issue_status || emd?.status)} · {label(emd?.issuing_provider)}</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{emd?.emd_number || "Draft EMD mirror"}</h2>
                <p className="mt-1 text-sm text-slate-600">Provider EMD issuance is disabled in this phase.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {emd?.booking_workspace_id ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/booking-workspaces/${emd.booking_workspace_id}`}>Booking workspace</a> : null}
                <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/after-sales?emd_record_id=${encodeURIComponent(emdRecordId)}${emd?.booking_workspace_id ? `&booking_workspace_id=${encodeURIComponent(emd.booking_workspace_id)}` : ""}`}>Open after-sales case</a>
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-400" type="button" disabled>Issue EMD</button>
              </div>
            </div>
          </div>

          <WorkflowContinuityPanel
            breadcrumbs={[
              { label: "Tickets & EMDs", href: "/agency/tickets-emds" },
              ...(emd?.booking_workspace_id ? [{ label: "Booking", href: `/agency/booking-workspaces/${emd.booking_workspace_id}` }] : []),
            ]}
            currentLabel={emd?.emd_number || "Draft EMD mirror"}
            status={emd?.issue_status || emd?.status}
            validation={serviceCase
              ? { state: "ready", label: "Passenger service linked", reason: "Continue with the canonical service fulfilment record." }
              : { state: "warning", label: "Service link needs review", reason: "Select the matching passenger service before continuing." }}
            previous={emd?.booking_workspace_id
              ? { label: "Back to booking", href: `/agency/booking-workspaces/${emd.booking_workspace_id}` }
              : { label: "Back to Tickets & EMDs", href: "/agency/tickets-emds" }}
            next={{ label: serviceCase ? "Continue to passenger service" : "Review passenger services", href: serviceHref }}
            relatedRecords={[
              { label: "Booking", value: emd?.booking_workspace_id || "none", href: emd?.booking_workspace_id ? `/agency/booking-workspaces/${emd.booking_workspace_id}` : undefined },
              { label: "Coupons", value: state?.coupons?.length || 0 },
              { label: "Passenger service", value: serviceCase?.service_label || serviceCase?.service_key || "not linked", href: serviceCase ? serviceHref : undefined },
            ]}
          />

          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div> : null}
          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div> : null}

          <section className="grid gap-4 lg:grid-cols-4">
            <Metric label="Passenger" value={passengerName(passenger, emd?.passenger_id)} />
            <Metric label="Service" value={emd?.service_label || emd?.service_key || "Manual service"} />
            <Metric label="Coupons" value={state?.coupons?.length || 0} />
            <Metric label="Amount" value={money(emd?.total_amount ?? emd?.amount, emd?.currency)} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <Panel title="Manual Update">
              <form className="space-y-3" onSubmit={save}>
                <Field label="EMD number" value={form.emd_number} onChange={(value) => setForm({ ...form, emd_number: value })} />
                <Select label="EMD type" value={form.emd_type} options={emdTypes} onChange={(value) => setForm({ ...form, emd_type: value })} />
                <Field label="RFIC" value={form.reason_for_issuance_code} onChange={(value) => setForm({ ...form, reason_for_issuance_code: value.toUpperCase() })} />
                <Field label="RFISC" value={form.reason_for_issuance_subcode} onChange={(value) => setForm({ ...form, reason_for_issuance_subcode: value.toUpperCase() })} />
                <Select label="Issue status" value={form.issue_status} options={statuses} onChange={(value) => setForm({ ...form, issue_status: value })} />
                <Field label="Currency" value={form.currency} onChange={(value) => setForm({ ...form, currency: value.toUpperCase() })} />
                <Field label="Amount" value={form.amount} onChange={(value) => setForm({ ...form, amount: value })} />
                <Field label="Taxes" value={form.taxes_amount} onChange={(value) => setForm({ ...form, taxes_amount: value })} />
                <Field label="Total" value={form.total_amount} onChange={(value) => setForm({ ...form, total_amount: value })} />
                <Textarea label="Internal notes" value={form.internal_notes} onChange={(value) => setForm({ ...form, internal_notes: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="submit">Save EMD mirror</button>
              </form>
            </Panel>

            <div className="space-y-4">
              <Panel title="Service Catalogue Mapping">
                <JsonBlock value={state?.service_mapping} />
              </Panel>
              <Panel title="Coupons by Service / Segment">
                <SnapshotList items={state?.coupons} render={(item) => `${item.coupon_number}. ${item.service_label || item.service_key || "Service"}${item.segment_id ? ` · ${item.segment_id}` : ""} · ${label(item.coupon_status)}`} />
              </Panel>
              <section className="grid gap-4 lg:grid-cols-2">
                <Panel title="Linked Service"><JsonBlock value={emd?.linked_service_snapshot_json} /></Panel>
                <Panel title="Pricing"><JsonBlock value={emd?.pricing_snapshot_json} /></Panel>
              </section>
              <Panel title="Linked Ticket">
                <p className="text-sm text-slate-700">{state?.ticket_summary?.ticket_number || state?.ticket_summary?.id || "No linked ticket"}</p>
              </Panel>
              <Panel title="Warnings">
                <SnapshotList items={state?.warnings} render={(item) => item.message || JSON.stringify(item)} />
              </Panel>
              <Panel title="Timeline">
                <SnapshotList items={state?.timeline} render={(item) => `${item.title}${item.description ? ` · ${item.description}` : ""}`} />
              </Panel>
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold text-slate-950">{value}</p></div>
}

function Field({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Textarea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<textarea className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, options, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{labelValue(option)}</option>)}</select></label>
}

function SnapshotList({ items, render }) {
  const list = items || []
  if (!list.length) return <p className="text-sm text-slate-500">None recorded.</p>
  return <div className="divide-y divide-slate-100 rounded-md border border-slate-200">{list.map((item, index) => <div className="p-3 text-sm text-slate-700" key={item.id || index}>{render(item)}</div>)}</div>
}

function JsonBlock({ value }) {
  const hasValue = value && Object.keys(value).length
  if (!hasValue) return <p className="text-sm text-slate-500">None recorded.</p>
  return <pre className="max-h-72 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">{JSON.stringify(value, null, 2)}</pre>
}

function passengerName(passenger, fallback) {
  return passenger.display_name || passenger.snapshot_display_name || `${passenger.first_name || ""} ${passenger.last_name || ""}`.trim() || fallback || "Passenger"
}

function amountValue(value) {
  return value === null || value === undefined ? "" : String(value)
}

function numberOrNull(value) {
  return value === "" || value === null || value === undefined ? null : Number(value)
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function labelValue(value) {
  return String(value || "").replaceAll("_", " ")
}

function money(amount, currency) {
  if (amount === null || amount === undefined || amount === "") return "Not priced"
  return `${Number(amount).toFixed(2)} ${currency || "EUR"}`
}
