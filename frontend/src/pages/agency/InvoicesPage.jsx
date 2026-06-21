import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import InvoiceStatusBadge from "../../components/InvoiceStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function InvoicesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const invoices = await apiGet(`/api/agencies/${context.agency.id}/invoices`)
      setState({ ...context, invoices: invoices.items })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.invoices || []).filter((invoice) => {
      const matchesSearch = !search || [invoice.invoice_number, invoice.client?.display_name, invoice.booking?.booking_reference].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch && (!filters.status || invoice.status === filters.status)
    })
  }, [filters, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Finance Tracking</p>
            <h2 className="text-2xl font-semibold text-slate-950">Invoices</h2>
            <p className="mt-1 text-sm text-slate-600">Tracking only. This is not full accounting or tax filing.</p>
          </div>
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search invoices" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {["draft", "issued", "partially_paid", "paid", "overdue", "voided", "cancelled", "archived"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
          </section>
          {filtered.length ? (
            <div className="grid gap-4">
              {filtered.map((invoice) => (
                <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={`/agency/invoices/${invoice.id}`} key={invoice.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{invoice.invoice_number}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{invoice.client?.display_name || "Client"}</h3>
                      <p className="mt-1 text-sm text-slate-600">{invoice.booking?.booking_reference || "No booking linked"}</p>
                    </div>
                    <InvoiceStatusBadge status={invoice.status} />
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-3">
                    <span>Total: {invoice.total_amount} {invoice.currency}</span>
                    <span>Paid: {invoice.paid_amount} {invoice.currency}</span>
                    <span>Due: {invoice.due_amount} {invoice.currency}</span>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <EmptyState title="No invoices found" body="Invoices can be created from booking detail." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
