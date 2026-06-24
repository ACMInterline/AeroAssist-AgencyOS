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
      const [requests, intakes] = agency ? await Promise.all([
        apiGet(`/api/agencies/${agency.id}/requests`).catch(() => ({ items: [] })),
        apiGet(`/api/request-intakes?agency_id=${agency.id}`).catch(() => ({ items: [] })),
      ]) : [{ items: [] }, { items: [] }]
      setState({ me: context.me, agency, settings, staff: staff.items, requests: requests.items, intakes: intakes.items })
    }
    loadAgency().catch((err) => setError(err.message))
  }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        {!state?.agency ? (
          <EmptyState title="No agency workspace yet" body="Create your first agency workspace from Platform > Agencies to begin operating AeroAssist." />
        ) : (
        <div className="space-y-6">
          <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <div className="grid gap-6 p-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Agency Workspace</p>
                <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{state?.agency?.branding?.brand_name || state?.agency?.name}</h2>
                <p className="mt-2 text-sm text-slate-600">{state?.agency?.legal_name}</p>
              </div>
              <StatusBadge status={state?.agency?.status} />
            </div>
            <div className="flex flex-wrap items-center gap-3 lg:justify-end">
              <a className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold" href="/agency/requests/new">Create request</a>
              <a className="rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" href="/agency/request-intakes">Review intakes</a>
              <a className="rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" href="/agency/settings">Brand settings</a>
            </div>
            </div>
            <dl className="grid gap-4 border-t border-slate-100 p-6 sm:grid-cols-2 xl:grid-cols-4">
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
              <div className="rounded-md bg-slate-50 p-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Open requests</dt>
                <dd className="mt-2 text-lg font-semibold text-slate-950">{(state?.requests || []).filter((request) => !["closed", "cancelled", "archived"].includes(request.status)).length}</dd>
              </div>
              <div className="rounded-md bg-slate-50 p-4">
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Queued intakes</dt>
                <dd className="mt-2 text-lg font-semibold text-slate-950">{(state?.intakes || []).filter((intake) => ["new", "triaged"].includes(intake.status)).length}</dd>
              </div>
            </dl>
          </section>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <a className="group rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/requests">
              <h3 className="text-sm font-semibold text-slate-900">Operational requests</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Work active cases, passengers, segments, services, messages, and tasks.</p>
            </a>
            <a className="group rounded-lg border border-slate-200 bg-white p-6 hover:border-blue-300" href="/agency/request-intakes">
              <h3 className="text-sm font-semibold text-slate-900">Intake queue</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Review public and portal submissions before conversion.</p>
            </a>
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
