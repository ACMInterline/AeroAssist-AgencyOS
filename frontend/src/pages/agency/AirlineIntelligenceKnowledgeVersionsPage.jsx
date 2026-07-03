import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AirlineIntelligenceKnowledgeVersionsPage() {
  const [state, setState] = useState(null)
  const [selectedVersionId, setSelectedVersionId] = useState("")
  const [error, setError] = useState("")

  async function load(openVersionId = selectedVersionId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/airline-intelligence-knowledge-versions`
    const [summary, current, preview, versions] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/current`),
      apiGet(`${base}/preview`),
      apiGet(`${base}/versions`),
    ])
    const versionItems = versions.items || []
    const nextVersionId = openVersionId || current.version?.id || preview.version?.id || versionItems[0]?.id || ""
    const detail = nextVersionId ? await apiGet(`${base}/versions/${nextVersionId}`) : null
    setSelectedVersionId(nextVersionId)
    setState({
      ...context,
      base,
      summary,
      current,
      preview,
      versions: versionItems,
      detail,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = useMemo(() => [
    ["Visible versions", state?.summary?.visible_versions?.length || 0],
    ["Published metadata", state?.summary?.published_metadata_version_count || 0],
    ["Preview versions", state?.preview?.version ? 1 : 0],
    ["Version items", state?.summary?.version_item_count || 0],
    ["Channels", state?.summary?.release_channel_count || 0],
    ["Assignments", state?.summary?.release_assignment_count || 0],
  ], [state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Knowledge Versions</h2>
            <p className="mt-1 text-sm text-slate-600">Read-only airline knowledge visibility. Raw staged payloads are hidden.</p>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Agency visibility summary</h3>
            <p className="mt-2 text-sm text-slate-600">{state?.summary?.plain_language_overview || "Airline intelligence knowledge versions are read-only and metadata-only."}</p>
          </section>

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <VersionSpotlight title="Current visible version" detail={state?.current} />
            <VersionSpotlight title="Preview version" detail={state?.preview} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <h3 className="font-semibold text-slate-950">Visible knowledge versions</h3>
              </div>
              {!state?.versions?.length ? <EmptyState title="No visible versions" body="Platform owners have not assigned a visible or preview airline intelligence version yet." /> : (
                <div className="divide-y divide-slate-100">
                  {state.versions.map((version) => (
                    <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedVersionId === version.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(version.id)} key={version.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{version.version_code}</p>
                          <p className="mt-1 text-sm text-slate-600">{version.title}</p>
                        </div>
                        <Status text={label(version.agency_visibility_mode)} ready={version.agency_visibility_mode === "visible"} />
                      </div>
                      <p className="mt-2 text-sm text-slate-600">{version.coverage_summary || "Coverage summary pending."}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-4">
              {!state?.detail?.version ? <EmptyState title="Select a version" body="Visible airline knowledge summaries will appear here." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">{state.detail.version.title}</h3>
                        <p className="mt-1 text-sm text-slate-600">{state.detail.version.coverage_summary || "Coverage summary pending."}</p>
                      </div>
                      <Status text={label(state.detail.version.status)} ready={state.detail.version.status === "published"} />
                    </div>
                    <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
                      <Flag label="CRM safe" enabled={state.detail.version.crm_safe} />
                      <Flag label="CMS metadata safe" enabled={state.detail.version.cms_safe} />
                      <Flag label="Client portal metadata safe" enabled={state.detail.version.client_portal_safe} />
                      <Flag label="Offer builder safe" enabled={state.detail.version.offer_builder_safe} />
                    </div>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">What changed</h3>
                    </div>
                    <div className="divide-y divide-slate-100">
                      {(state.detail.items || []).map((item) => (
                        <div className="p-4" key={item.id}>
                          <p className="font-semibold text-slate-950">{item.target_airline_code || "Airline"} · {label(item.target_domain)}</p>
                          <p className="mt-1 text-sm text-slate-600">{item.agency_plain_language_summary || item.target_record_key}</p>
                        </div>
                      ))}
                      {!state.detail.items?.length ? <EmptyState title="No visible item summaries" body="This version has no included agency-visible item summaries yet." /> : null}
                    </div>
                  </section>
                </>
              )}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function VersionSpotlight({ title, detail }) {
  const version = detail?.version
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      {version ? (
        <>
          <p className="mt-2 text-sm font-semibold text-slate-950">{version.version_code} · {version.title}</p>
          <p className="mt-1 text-sm text-slate-600">{version.coverage_summary || "Coverage summary pending."}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Status text={label(version.status)} ready={version.status === "published"} />
            <Status text={label(version.agency_visibility_mode)} ready={version.agency_visibility_mode === "visible"} />
          </div>
        </>
      ) : (
        <p className="mt-2 text-sm text-slate-600">No version available.</p>
      )}
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

function Flag({ label, enabled }) {
  return <span className={`rounded-md px-3 py-2 ${enabled ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-500"}`}>{label}: {enabled ? "Ready" : "Off"}</span>
}

function Status({ text, ready }) {
  const tone = ready ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
