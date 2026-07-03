import { useEffect, useMemo, useState } from "react"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import FileCheck2 from "lucide-react/dist/esm/icons/file-check-2.js"
import GitBranch from "lucide-react/dist/esm/icons/git-branch.js"
import Layers3 from "lucide-react/dist/esm/icons/layers-3.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const base = "/api/platform/airline-intelligence-knowledge-versions"
const packBase = "/api/platform/airline-intelligence-data-packs"
const reviewBase = "/api/platform/airline-intelligence-data-pack-reviews"

const defaultVersion = {
  version_code: "",
  title: "",
  description: "",
  agency_visibility_mode: "hidden",
  crm_safe: false,
  cms_safe: false,
  client_portal_safe: false,
  offer_builder_safe: false,
}

const defaultChannel = {
  channel_code: "",
  name: "",
  audience: "internal_only",
  description: "",
}

export default function AirlineIntelligenceKnowledgeVersionsPage() {
  const [state, setState] = useState(null)
  const [selectedVersionId, setSelectedVersionId] = useState("")
  const [selectedPackId, setSelectedPackId] = useState("")
  const [selectedReviewId, setSelectedReviewId] = useState("")
  const [versionForm, setVersionForm] = useState(defaultVersion)
  const [channelForm, setChannelForm] = useState(defaultChannel)
  const [compareBaseId, setCompareBaseId] = useState("")
  const [compareVersionId, setCompareVersionId] = useState("")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(openVersionId = selectedVersionId, openPackId = selectedPackId, openReviewId = selectedReviewId) {
    const [me, summary, versions, channels, assignments, comparisons, rollbackPlans, packs, reviews] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/versions`),
      apiGet(`${base}/release-channels`),
      apiGet(`${base}/release-assignments`),
      apiGet(`${base}/comparisons`),
      apiGet(`${base}/rollback-plans`),
      apiGet(`${packBase}/packs`),
      apiGet(`${reviewBase}/reviews`),
    ])
    const versionItems = versions.items || []
    const packItems = packs.items || []
    const reviewItems = reviews.items || []
    const nextVersionId = openVersionId || versionItems[0]?.id || ""
    const nextPackId = openPackId || packItems[0]?.id || ""
    const nextReviewId = openReviewId || reviewItems.find((item) => item.pack_id === nextPackId)?.id || reviewItems[0]?.id || ""
    const [versionDetail, packDetail, reviewDetail] = await Promise.all([
      nextVersionId ? apiGet(`${base}/versions/${nextVersionId}`) : Promise.resolve(null),
      nextPackId ? apiGet(`${packBase}/packs/${nextPackId}`) : Promise.resolve(null),
      nextReviewId ? apiGet(`${reviewBase}/reviews/${nextReviewId}`) : Promise.resolve(null),
    ])
    setSelectedVersionId(nextVersionId)
    setSelectedPackId(nextPackId)
    setSelectedReviewId(nextReviewId)
    setCompareBaseId((current) => current || versionItems[1]?.id || "")
    setCompareVersionId((current) => current || nextVersionId)
    setState({
      me,
      summary,
      versions: versionItems,
      channels: channels.items || [],
      assignments: assignments.items || [],
      comparisons: comparisons.items || [],
      rollbackPlans: rollbackPlans.items || [],
      packs: packItems,
      reviews: reviewItems,
      versionDetail,
      packDetail,
      reviewDetail,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedVersion = state?.versionDetail?.version
  const sourceItems = state?.packDetail?.items || []
  const reviewMappings = state?.reviewDetail?.field_mappings || []
  const reviewReadiness = state?.reviewDetail?.promotion_readiness || []
  const metrics = useMemo(() => [
    ["Versions", state?.summary?.knowledge_version_count || 0],
    ["Items", state?.summary?.version_item_count || 0],
    ["Channels", state?.summary?.release_channel_count || 0],
    ["Assignments", state?.summary?.release_assignment_count || 0],
    ["Comparisons", state?.summary?.comparison_count || 0],
    ["Rollback plans", state?.summary?.rollback_plan_count || 0],
    ["Published metadata", state?.summary?.published_metadata_version_count || 0],
    ["Agency visible", state?.summary?.agency_visible_version_count || 0],
  ], [state])

  async function runAction(name, action) {
    setWorking(name)
    setError("")
    setMessage("")
    try {
      await action()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  function createVersion(event) {
    event.preventDefault()
    runAction("create-version", async () => {
      const review = state?.reviews?.find((item) => item.id === selectedReviewId)
      const readinessId = reviewReadiness[0]?.id
      const result = await apiPost(`${base}/versions`, {
        ...versionForm,
        source_pack_ids: selectedPackId ? [selectedPackId] : [],
        source_review_ids: selectedReviewId ? [selectedReviewId] : [],
        source_promotion_readiness_ids: readinessId ? [readinessId] : [],
        coverage_summary: review?.plain_language_coverage_summary || state?.packDetail?.pack?.human_summary || "",
      })
      setMessage("Knowledge version draft created.")
      setVersionForm(defaultVersion)
      await load(result.version.id, selectedPackId, selectedReviewId)
    })
  }

  function addReviewedItem(item) {
    if (!selectedVersionId) return
    const mapping = reviewMappings.find((entry) => entry.item_id === item.id)
    const readiness = reviewReadiness[0]
    runAction(`item-${item.id}`, async () => {
      await apiPost(`${base}/versions/${selectedVersionId}/items`, {
        source_pack_item_id: item.id,
        target_domain: item.target_domain,
        target_record_key: item.target_record_key || item.display_name,
        target_airline_code: item.airline_iata_code,
        field_mapping_id: mapping?.id || null,
        conflict_ids: [],
        readiness_id: readiness?.id || null,
        inclusion_status: "included",
        inclusion_reason: "Included from reviewed staged airline intelligence.",
        normalized_payload_preview: item.normalized_payload || {},
        agency_plain_language_summary: item.plain_language_summary || item.display_name,
      })
      setMessage("Version item included.")
      await load(selectedVersionId, selectedPackId, selectedReviewId)
    })
  }

  function versionAction(action, label) {
    if (!selectedVersionId) return
    runAction(action, async () => {
      const payload = action === "approve" ? { approved_by: state?.me?.user?.email || "platform" } : action === "mark-published-metadata" ? { published_by: state?.me?.user?.email || "platform", agency_visibility_mode: "visible" } : {}
      await apiPost(`${base}/versions/${selectedVersionId}/${action}`, payload)
      setMessage(label)
      await load(selectedVersionId, selectedPackId, selectedReviewId)
    })
  }

  function createChannel(event) {
    event.preventDefault()
    runAction("channel", async () => {
      await apiPost(`${base}/release-channels`, channelForm)
      setMessage("Release channel metadata created.")
      setChannelForm(defaultChannel)
      await load(selectedVersionId, selectedPackId, selectedReviewId)
    })
  }

  function assignVersion(channel) {
    if (!selectedVersionId) return
    runAction(`assign-${channel.id}`, async () => {
      await apiPost(`${base}/release-assignments`, {
        channel_id: channel.id,
        version_id: selectedVersionId,
        status: channel.audience === "internal_only" ? "planned" : "active",
        notes: "Metadata-only version assignment.",
      })
      setMessage("Release assignment metadata created.")
      await load(selectedVersionId, selectedPackId, selectedReviewId)
    })
  }

  function compareVersions() {
    if (!compareBaseId || !compareVersionId) return
    runAction("compare", async () => {
      await apiPost(`${base}/comparisons`, { base_version_id: compareBaseId, compare_version_id: compareVersionId })
      setMessage("Version comparison generated.")
      await load(selectedVersionId, selectedPackId, selectedReviewId)
    })
  }

  function createRollbackPlan() {
    if (!compareBaseId || !compareVersionId) return
    runAction("rollback", async () => {
      await apiPost(`${base}/rollback-plans`, {
        from_version_id: compareVersionId,
        to_version_id: compareBaseId,
        reason: "Manual metadata rollback readiness review.",
        impact_summary: "Rollback plan is metadata-only and does not mutate airline intelligence records.",
      })
      setMessage("Rollback plan metadata created.")
      await load(selectedVersionId, selectedPackId, selectedReviewId)
    })
  }

  function createSnapshot() {
    if (!selectedVersionId) return
    runAction("snapshot", async () => {
      await apiPost(`${base}/versions/${selectedVersionId}/snapshots`, {
        snapshot_type: "manual",
        metadata_json: { note: "Manual knowledge version snapshot" },
      })
      setMessage("Immutable version snapshot created.")
      await load(selectedVersionId, selectedPackId, selectedReviewId)
    })
  }

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Knowledge Versions</h2>
              <p className="mt-1 text-sm text-slate-600">Publication status is metadata-only; operational airline tables and public channels are not changed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={() => versionAction("freeze", "Version frozen.")} disabled={!selectedVersionId || working === "freeze"}><FileCheck2 className="h-4 w-4" />Freeze</button>
              <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={() => versionAction("approve", "Version approved.")} disabled={!selectedVersionId || working === "approve"}><CheckCircle2 className="h-4 w-4" />Approve</button>
              <button className="inline-flex items-center gap-2 aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={() => versionAction("mark-published-metadata", "Published metadata marked.")} disabled={!selectedVersionId || working === "mark-published-metadata"}><Layers3 className="h-4 w-4" />Published metadata</button>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 p-4">
                  <h3 className="font-semibold text-slate-950">Versions</h3>
                </div>
                {!state?.versions?.length ? <EmptyState title="No knowledge versions" body="Create a draft version from reviewed airline intelligence." /> : (
                  <div className="divide-y divide-slate-100">
                    {state.versions.map((version) => (
                      <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedVersionId === version.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(version.id, selectedPackId, selectedReviewId)} key={version.id}>
                        <p className="font-semibold text-slate-950">{version.version_code}</p>
                        <p className="mt-1 text-sm text-slate-600">{version.title} · {label(version.status)}</p>
                      </button>
                    ))}
                  </div>
                )}
              </section>

              <form className="rounded-lg border border-slate-200 bg-white p-4" onSubmit={createVersion}>
                <h3 className="font-semibold text-slate-950">Create draft version</h3>
                <div className="mt-4 space-y-3">
                  <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Version code" value={versionForm.version_code} onChange={(event) => setVersionForm({ ...versionForm, version_code: event.target.value })} required />
                  <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Title" value={versionForm.title} onChange={(event) => setVersionForm({ ...versionForm, title: event.target.value })} required />
                  <textarea className="min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Description" value={versionForm.description} onChange={(event) => setVersionForm({ ...versionForm, description: event.target.value })} />
                  <select className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={versionForm.agency_visibility_mode} onChange={(event) => setVersionForm({ ...versionForm, agency_visibility_mode: event.target.value })}>
                    <option value="hidden">Hidden</option>
                    <option value="preview">Preview</option>
                    <option value="visible">Visible</option>
                  </select>
                  <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={versionForm.crm_safe} onChange={(event) => setVersionForm({ ...versionForm, crm_safe: event.target.checked })} />CRM safe</label>
                  <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={versionForm.cms_safe} onChange={(event) => setVersionForm({ ...versionForm, cms_safe: event.target.checked })} />CMS safe metadata</label>
                  <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={versionForm.offer_builder_safe} onChange={(event) => setVersionForm({ ...versionForm, offer_builder_safe: event.target.checked })} />Offer builder safe</label>
                  <button className="inline-flex w-full items-center justify-center gap-2 aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "create-version"}><GitBranch className="h-4 w-4" />Create version</button>
                </div>
              </form>
            </div>

            <div className="space-y-4">
              {!selectedVersion ? <EmptyState title="Select a version" body="Version detail will appear here." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">{selectedVersion.title}</h3>
                        <p className="mt-1 text-sm text-slate-600">{selectedVersion.coverage_summary || "Coverage summary pending."}</p>
                      </div>
                      <Status text={label(selectedVersion.status)} ready={["approved", "published"].includes(selectedVersion.status)} />
                    </div>
                    <div className="mt-4 grid gap-2 text-sm md:grid-cols-4">
                      <Flag label="CRM" enabled={selectedVersion.crm_safe} />
                      <Flag label="CMS metadata" enabled={selectedVersion.cms_safe} />
                      <Flag label="Client portal metadata" enabled={selectedVersion.client_portal_safe} />
                      <Flag label="Offer builder" enabled={selectedVersion.offer_builder_safe} />
                    </div>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">Reviewed staged items</h3>
                      <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={selectedPackId} onChange={(event) => load(selectedVersionId, event.target.value, "")}>
                        {state.packs.map((pack) => <option value={pack.id} key={pack.id}>{pack.name}</option>)}
                      </select>
                    </div>
                    {!sourceItems.length ? <EmptyState title="No staged items" body="Select a reviewed data pack with staged items." /> : (
                      <div className="divide-y divide-slate-100">
                        {sourceItems.map((item) => (
                          <div className="flex flex-wrap items-start justify-between gap-3 p-4" key={item.id}>
                            <div>
                              <p className="font-semibold text-slate-950">{item.display_name}</p>
                              <p className="mt-1 text-sm text-slate-600">{item.airline_iata_code || "Airline"} · {label(item.target_domain)} · {item.plain_language_summary}</p>
                            </div>
                            <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={() => addReviewedItem(item)} disabled={!selectedVersionId || working === `item-${item.id}`}>Include</button>
                          </div>
                        ))}
                      </div>
                    )}
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">Version items</h3>
                    </div>
                    <div className="divide-y divide-slate-100">
                      {(state.versionDetail?.items || []).map((item) => (
                        <div className="p-4" key={item.id}>
                          <p className="font-semibold text-slate-950">{item.target_airline_code || "Airline"} · {label(item.target_domain)}</p>
                          <p className="mt-1 text-sm text-slate-600">{item.agency_plain_language_summary || item.target_record_key}</p>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section className="grid gap-4 lg:grid-cols-2">
                    <form className="rounded-lg border border-slate-200 bg-white p-4" onSubmit={createChannel}>
                      <h3 className="font-semibold text-slate-950">Release channel</h3>
                      <div className="mt-4 space-y-3">
                        <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Channel code" value={channelForm.channel_code} onChange={(event) => setChannelForm({ ...channelForm, channel_code: event.target.value })} required />
                        <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Name" value={channelForm.name} onChange={(event) => setChannelForm({ ...channelForm, name: event.target.value })} required />
                        <select className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={channelForm.audience} onChange={(event) => setChannelForm({ ...channelForm, audience: event.target.value })}>
                          <option value="internal_only">Internal only</option>
                          <option value="pilot_agencies">Pilot agencies</option>
                          <option value="all_agencies">All agencies</option>
                          <option value="platform">Platform</option>
                        </select>
                        <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="submit">Create channel</button>
                      </div>
                    </form>

                    <section className="rounded-lg border border-slate-200 bg-white">
                      <div className="border-b border-slate-200 p-4">
                        <h3 className="font-semibold text-slate-950">Assignments</h3>
                      </div>
                      <div className="divide-y divide-slate-100">
                        {state.channels.map((channel) => (
                          <div className="flex items-center justify-between gap-3 p-4" key={channel.id}>
                            <div>
                              <p className="font-semibold text-slate-950">{channel.name}</p>
                              <p className="text-sm text-slate-600">{label(channel.audience)}</p>
                            </div>
                            <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => assignVersion(channel)}>Assign</button>
                          </div>
                        ))}
                      </div>
                    </section>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white p-4">
                    <div className="flex flex-wrap items-end gap-3">
                      <div>
                        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Base</label>
                        <select className="mt-1 block rounded-md border border-slate-300 px-3 py-2 text-sm" value={compareBaseId} onChange={(event) => setCompareBaseId(event.target.value)}>
                          <option value="">Select</option>
                          {state.versions.map((version) => <option value={version.id} key={version.id}>{version.version_code}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Compare</label>
                        <select className="mt-1 block rounded-md border border-slate-300 px-3 py-2 text-sm" value={compareVersionId} onChange={(event) => setCompareVersionId(event.target.value)}>
                          <option value="">Select</option>
                          {state.versions.map((version) => <option value={version.id} key={version.id}>{version.version_code}</option>)}
                        </select>
                      </div>
                      <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={compareVersions}><RefreshCw className="h-4 w-4" />Compare</button>
                      <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={createRollbackPlan}>Rollback plan</button>
                      <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={createSnapshot}>Snapshot</button>
                    </div>
                  </section>
                </>
              )}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
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
  return <span className={`rounded-md px-3 py-2 ${enabled ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-500"}`}>{label}: {enabled ? "Safe" : "Off"}</span>
}

function Status({ text, ready }) {
  const tone = ready ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
