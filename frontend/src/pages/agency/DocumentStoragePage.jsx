import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function DocumentStoragePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const agencyId = context.agency.id
    const [summary, health, providers, readiness, records] = await Promise.all([
      apiGet(`/api/documents/storage/summary?agency_id=${agencyId}`),
      apiGet(`/api/documents/storage/health?agency_id=${agencyId}`),
      apiGet(`/api/documents/delivery-providers?agency_id=${agencyId}`),
      apiGet(`/api/documents/delivery-providers/readiness?agency_id=${agencyId}`),
      apiGet(`/api/documents/storage?agency_id=${agencyId}`),
    ])
    setState({ ...context, summary: summary.summary, health: health.health, providers: providers.items, readiness: readiness.readiness, records: records.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function archiveRecord(recordId) {
    setError("")
    setNotice("")
    try {
      await apiPost(`/api/documents/storage/${recordId}/archive`, {})
      setNotice("Storage record archived.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function markMissing(recordId) {
    setError("")
    setNotice("")
    try {
      await apiPost(`/api/documents/storage/${recordId}/mark-missing`, {})
      setNotice("Storage record marked missing.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Documents</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Storage / Delivery Readiness</h2>
            <p className="mt-1 text-sm text-slate-600">Automatic delivery is disabled in Phase 25. Manual delivery is the only active provider. No public links are enabled.</p>
          </div>
          {notice ? <p className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p> : null}

          <section className="grid gap-4 md:grid-cols-3">
            <SummaryCard title="Storage Health" items={[
              ["Configured", state?.health?.configured ? "yes" : "no"],
              ["Writable", state?.health?.directory_writable ? "yes" : "no"],
              ["Files", state?.health?.total_file_count ?? 0],
              ["Bytes", state?.health?.total_bytes ?? 0],
            ]} />
            <SummaryCard title="Lifecycle Counts" items={[
              ["Total", state?.summary?.total ?? 0],
              ["Active", state?.summary?.by_status?.active ?? 0],
              ["Archived", state?.summary?.by_status?.archived ?? 0],
              ["Missing", state?.summary?.by_status?.missing ?? 0],
            ]} />
            <SummaryCard title="Delivery Guards" items={[
              ["Automatic", state?.readiness?.automatic_delivery_enabled ? "enabled" : "disabled"],
              ["Public links", state?.readiness?.public_links_enabled ? "enabled" : "disabled"],
              ["Object storage", state?.readiness?.object_storage_enabled ? "enabled" : "disabled"],
              ["Manual", "enabled"],
            ]} />
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="text-sm font-semibold text-slate-950">Delivery Provider Readiness</h3>
            <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {state?.providers?.map((provider) => (
                <div className="rounded-md border border-slate-200 p-4" key={provider.provider_type}>
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-slate-950">{provider.provider_type.replaceAll("_", " ")}</p>
                    <StatusBadge status={provider.enabled ? "active" : provider.mode} />
                  </div>
                  <p className="mt-2 text-sm text-slate-600">Configured: {provider.configured ? "yes" : "no"}</p>
                  {provider.warnings?.length ? <p className="mt-2 text-xs text-slate-500">{provider.warnings[0]}</p> : null}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="text-sm font-semibold text-slate-950">Storage Records</h3>
            {state?.records?.length ? (
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {state.records.map((record) => (
                  <div className="grid gap-3 p-4 lg:grid-cols-[1fr_auto]" key={record.id}>
                    <div>
                      <p className="font-semibold text-slate-950">{record.filename_original || record.related_entity_id}</p>
                      <p className="mt-1 text-sm text-slate-600">{record.document_type} · {record.content_type || "unknown"} · {record.size_bytes || 0} bytes</p>
                      <p className="mt-1 text-xs text-slate-500">{record.related_entity_type} · {record.related_entity_id}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={record.storage_status} />
                      {record.storage_status === "active" ? (
                        <button className="rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" type="button" onClick={() => archiveRecord(record.id)}>Archive</button>
                      ) : null}
                      {record.storage_status !== "missing" ? (
                        <button className="rounded-md border border-amber-200 px-3 py-2 text-sm font-semibold text-amber-700 hover:bg-amber-50" type="button" onClick={() => markMissing(record.id)}>Mark missing</button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-4">
                <EmptyState title="No storage records" body="Generated document exports will appear here after storage metadata is registered." />
              </div>
            )}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function SummaryCard({ title, items }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
      <dl className="mt-4 space-y-2 text-sm">
        {items.map(([label, value]) => (
          <div className="flex justify-between gap-3" key={label}>
            <dt className="text-slate-500">{label}</dt>
            <dd className="font-semibold text-slate-900">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
