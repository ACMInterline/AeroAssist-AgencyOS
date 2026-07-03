import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"
import { agencyModuleGroups } from "../../lib/moduleCatalog"

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
            {agencyModuleGroups.map((group) => (
              <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={group.items[0]?.href || "/agency"} key={group.title}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold text-slate-900">{group.title}</h3>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600">{group.safety}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600">{group.description}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full bg-blue-50 px-2 py-1 text-[11px] font-semibold text-blue-700">{group.audience}</span>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600">{group.items.length} tools</span>
                </div>
              </a>
            ))}
          </section>
        </div>
        )}
      </ProtectedRoute>
    </AgencyLayout>
  )
}
