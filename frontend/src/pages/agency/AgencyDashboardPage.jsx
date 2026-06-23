import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AgencyDashboardPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function loadAgency() {
      const context = await loadCurrentAgency()
      const agency = context.agency
      const workspaces = agency ? await apiGet(`/api/agencies/${agency.id}/workspaces`) : { items: [] }
      const settings = workspaces.items[0] || null
      const staff = agency ? await apiGet(`/api/agencies/${agency.id}/staff`) : { items: [] }
      setState({ me: context.me, agency, settings, staff: staff.items })
    }
    loadAgency().catch((err) => setError(err.message))
  }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        {!state?.agency ? (
          <EmptyState title="No agency workspace yet" body="Create your first agency workspace from Platform > Agencies to begin operating AeroAssist." />
        ) : (
        <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Agency Workspace</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-950">{state?.agency?.name}</h2>
                <p className="mt-2 text-sm text-slate-600">{state?.agency?.legal_name}</p>
              </div>
              <StatusBadge status={state?.agency?.status} />
            </div>
            <dl className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-md bg-slate-50 p-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Currency</dt>
                <dd className="mt-2 text-lg font-semibold text-slate-950">{state?.agency?.default_currency}</dd>
              </div>
              <div className="rounded-md bg-slate-50 p-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Timezone</dt>
                <dd className="mt-2 text-lg font-semibold text-slate-950">{state?.agency?.timezone}</dd>
              </div>
              <div className="rounded-md bg-slate-50 p-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Brand</dt>
                <dd className="mt-2 text-lg font-semibold text-slate-950">{state?.settings?.brand_name}</dd>
              </div>
              <div className="rounded-md bg-slate-50 p-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Staff</dt>
                <dd className="mt-2 text-lg font-semibold text-slate-950">{state?.staff?.length || 0}</dd>
              </div>
            </dl>
          </section>
          <section className="grid gap-4">
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/clients">
              <h3 className="text-sm font-semibold text-slate-900">Clients</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Manage agency-owned client account/contact records.</p>
            </a>
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/passengers">
              <h3 className="text-sm font-semibold text-slate-900">Passengers</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Manage traveler profiles separately from clients.</p>
            </a>
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/requests">
              <h3 className="text-sm font-semibold text-slate-900">Requests</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Capture inquiries, intended segments, services, messages, tasks, and timeline events.</p>
            </a>
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/offers">
              <h3 className="text-sm font-semibold text-slate-900">Offers</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Build manual offers with route alternatives, fare options, price lines, and send snapshots.</p>
            </a>
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/bookings">
              <h3 className="text-sm font-semibold text-slate-900">Bookings</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Track PNRs, passengers, segments, tickets, EMDs, invoices, payments, and operational timeline.</p>
            </a>
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/invoices">
              <h3 className="text-sm font-semibold text-slate-900">Invoices</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Manage invoice line items, issued status, paid amount, and due amount without full accounting.</p>
            </a>
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/payments">
              <h3 className="text-sm font-semibold text-slate-900">Payments</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Record manual payments received outside AgencyOS and track reconciliation status.</p>
            </a>
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/airline-intelligence">
              <h3 className="text-sm font-semibold text-slate-900">Airline Intelligence</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Search published platform knowledge and maintain agency-specific annotations.</p>
            </a>
            <a className="rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/documents">
              <h3 className="text-sm font-semibold text-slate-900">Documents</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Review rendered documents, export files, and manual delivery records.</p>
            </a>
          </section>
        </div>
        )}
      </ProtectedRoute>
    </AgencyLayout>
  )
}
