import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import { useAuthorization } from "../../context/AuthorizationContext"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const emptyForm = {
  supplier_reference: "",
  supplier_name: "",
  booking_workspace_id: "",
  description: "",
  expected_cost_amount: "",
  actual_cost_amount: "",
  currency: "EUR",
  notes: "",
}

export default function SupplierCostsPage() {
  const authorization = useAuthorization()
  const [state, setState] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [filter, setFilter] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [costs, bookings] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/finance/supplier-costs`),
      apiGet(`/api/agencies/${context.agency.id}/booking-workspaces`),
    ])
    setState({ ...context, costs: costs.items || [], bookings: bookings.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const visible = useMemo(() => {
    const needle = filter.toLowerCase()
    return (state?.costs || []).filter((item) => !needle || [item.supplier_cost_reference, item.supplier_reference, item.supplier_name].some((value) => String(value || "").toLowerCase().includes(needle)))
  }, [filter, state])

  async function create(event) {
    event.preventDefault()
    const workspace = state.bookings.find((item) => item.id === form.booking_workspace_id)
    try {
      await apiPost(`/api/agencies/${state.agency.id}/finance/supplier-costs`, {
        supplier_reference: form.supplier_reference,
        supplier_name: form.supplier_name || null,
        client_id: workspace?.client_id || workspace?.booking_record?.client_id || null,
        trip_id: workspace?.trip_id || workspace?.booking_record?.trip_id || null,
        booking_id: workspace?.booking_record_id || workspace?.booking_record?.id || null,
        booking_workspace_id: workspace?.id || null,
        currency: form.currency.toUpperCase(),
        description: form.description,
        expected_cost_amount: Number(form.expected_cost_amount || 0),
        actual_cost_amount: Number(form.actual_cost_amount || 0),
        notes: form.notes || null,
      })
      setForm(emptyForm)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function confirm(costId) {
    try {
      await apiPost(`/api/agencies/${state.agency.id}/finance/supplier-costs/${costId}/confirm`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const canEdit = authorization.hasPermission("edit_commercial_ledger")

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Finance", href: "/agency/finance" }, { label: "Supplier costs" }]}
            eyebrow="Agency private"
            title="Supplier costs"
            description="Record expected and actual supplier charges separately from client invoices. These values are visible only to authorized finance roles."
          />
          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div> : null}

          {canEdit ? <section className="rounded-md border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Add supplier cost</h3>
            <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={create}>
              <Field label="Supplier reference" required value={form.supplier_reference} onChange={(value) => setForm({ ...form, supplier_reference: value })} />
              <Field label="Supplier name" value={form.supplier_name} onChange={(value) => setForm({ ...form, supplier_name: value })} />
              <label className="grid gap-1 text-sm font-medium text-slate-700 md:col-span-2">Booking context<select className="rounded-md border border-slate-300 px-3 py-2 font-normal" value={form.booking_workspace_id} onChange={(event) => setForm({ ...form, booking_workspace_id: event.target.value })}><option value="">No booking selected</option>{(state?.bookings || []).map((item) => <option key={item.id} value={item.id}>{item.workspace_number || item.booking_reference || item.id} · {item.title || "Booking"}</option>)}</select></label>
              <Field label="Cost description" required value={form.description} onChange={(value) => setForm({ ...form, description: value })} />
              <Field label="Currency" required value={form.currency} onChange={(value) => setForm({ ...form, currency: value })} />
              <Field label="Expected cost" type="number" value={form.expected_cost_amount} onChange={(value) => setForm({ ...form, expected_cost_amount: value })} />
              <Field label="Actual cost" type="number" value={form.actual_cost_amount} onChange={(value) => setForm({ ...form, actual_cost_amount: value })} />
              <label className="grid gap-1 text-sm font-medium text-slate-700 md:col-span-2">Internal notes<textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2 font-normal" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label>
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold md:col-span-2" type="submit">Create draft cost</button>
            </form>
          </section> : null}

          <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search supplier costs" value={filter} onChange={(event) => setFilter(event.target.value)} />
          {visible.length ? <div className="divide-y divide-slate-100 rounded-md border border-slate-200 bg-white">{visible.map((item) => <div className="grid gap-3 p-4 md:grid-cols-[1fr_auto_auto_auto]" key={item.id}><div><p className="font-semibold text-slate-950">{item.supplier_name || item.supplier_reference}</p><p className="mt-1 text-sm text-slate-600">{item.supplier_cost_reference} · {item.supplier_reference}</p></div><Value label="Expected" value={money(item.expected_cost_amount, item.currency)} /><Value label="Actual" value={money(item.actual_cost_amount, item.currency)} /><div className="flex items-center gap-3"><span className="text-sm font-medium capitalize text-slate-700">{item.status}</span>{canEdit && item.status === "draft" ? <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" onClick={() => confirm(item.id)} type="button">Confirm</button> : null}</div></div>)}</div> : <EmptyState title="No supplier costs" body="Supplier costs remain separate from client invoice lines and appear here after an authorized finance user records them." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 font-normal" type={type} min={type === "number" ? "0" : undefined} step={type === "number" ? "0.01" : undefined} required={required} value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Value({ label, value }) {
  return <div><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-1 text-sm font-semibold text-slate-900">{value}</p></div>
}

function money(value, currency) {
  return `${Number(value || 0).toFixed(2)} ${currency || ""}`.trim()
}
