import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"

export default function AgencyDashboardPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function loadAgency() {
      const me = await apiGet("/api/auth/me")
      const agencies = await apiGet("/api/agencies")
      const agency = agencies.items[0]
      const settings = agency ? await apiGet(`/api/agencies/${agency.id}/settings`) : null
      const staff = agency ? await apiGet(`/api/agencies/${agency.id}/staff`) : { items: [] }
      setState({ me, agency, settings: settings?.settings, staff: staff.items })
    }
    loadAgency().catch((err) => setError(err.message))
  }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
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
            <EmptyState title="CRM coming next" body="Client and passenger records begin in Phase 3, after foundation setup." />
            <EmptyState title="Requests coming next" body="Request intake and timelines are Phase 4 work." />
            <EmptyState title="Offers coming next" body="Manual offer builder and snapshots are Phase 6 work." />
            <EmptyState title="Airline Intelligence later" body="Phase 5 starts with curated knowledge search, not airline policy automation." />
            <EmptyState title="Documents and payments later" body="Document output and financial tracking arrive after core agency workflows." />
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
