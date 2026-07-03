import { useEffect, useMemo, useState } from "react"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import FileCheck2 from "lucide-react/dist/esm/icons/file-check-2.js"
import GitBranch from "lucide-react/dist/esm/icons/git-branch.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"

const reviewBase = "/api/platform/airline-intelligence-data-pack-reviews"
const packBase = "/api/platform/airline-intelligence-data-packs"

const defaultMapping = {
  item_id: "",
  source_payload_path: "payload",
  target_collection: "airline_intelligence_profiles",
  target_field_path: "metadata_json",
  mapping_status: "draft",
  mapping_confidence: 0.8,
  would_create_record: false,
  would_update_record: false,
  safe_for_agency_internal_crm: false,
  safe_for_agency_display: false,
  safe_for_cms_display: false,
  safe_for_client_portal_later: false,
  safe_for_offer_builder: false,
}

export default function AirlineIntelligenceDataPackReviewsPage() {
  const [state, setState] = useState(null)
  const [selectedPackId, setSelectedPackId] = useState("")
  const [selectedReviewId, setSelectedReviewId] = useState("")
  const [mappingForm, setMappingForm] = useState(defaultMapping)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(openPackId = selectedPackId, openReviewId = selectedReviewId) {
    const [me, summary, packs, reviews] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${reviewBase}/summary`),
      apiGet(`${packBase}/packs`),
      apiGet(`${reviewBase}/reviews`),
    ])
    const packItems = packs.items || []
    const nextPackId = openPackId || packItems[0]?.id || ""
    const reviewItems = reviews.items || []
    const nextReviewId = openReviewId || reviewItems.find((item) => item.pack_id === nextPackId)?.id || reviewItems[0]?.id || ""
    const detail = nextReviewId ? await apiGet(`${reviewBase}/reviews/${nextReviewId}`) : null
    setSelectedPackId(nextPackId)
    setSelectedReviewId(nextReviewId)
    setState({ me, summary, packs: packItems, reviews: reviewItems, detail })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedPack = useMemo(() => state?.packs?.find((pack) => pack.id === selectedPackId), [state, selectedPackId])
  const selectedReview = state?.detail?.review
  const items = state?.detail?.items || state?.detail?.pack?.items || []
  const packItems = state?.detail?.pack ? state.detail.field_mappings || [] : []
  const metrics = [
    ["Reviews", state?.summary?.review_count || 0],
    ["Checklist items", state?.summary?.review_checklist_item_count || 0],
    ["Field mappings", state?.summary?.field_mapping_count || 0],
    ["Open conflicts", state?.summary?.open_conflict_count || 0],
    ["Ready", state?.summary?.promotion_ready_count || 0],
    ["Snapshots", state?.summary?.review_snapshot_count || 0],
  ]

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

  function createReview() {
    if (!selectedPackId) return
    runAction("review", async () => {
      const result = await apiPost(`${reviewBase}/packs/${selectedPackId}/reviews`, {
        review_title: `${selectedPack?.name || "Airline data pack"} review`,
        plain_language_coverage_summary: selectedPack?.human_summary || "Review coverage for agency-safe airline intelligence.",
        safe_for_agency_internal_crm: Boolean(selectedPack?.safe_for_agency_internal_crm),
        safe_for_agency_display: Boolean(selectedPack?.safe_for_agency_display),
        safe_for_cms_display: Boolean(selectedPack?.safe_for_cms_display),
        safe_for_client_portal_later: Boolean(selectedPack?.safe_for_client_portal_later),
        safe_for_offer_builder: Boolean(selectedPack?.safe_for_offer_builder),
      })
      setMessage("Review checklist created.")
      await load(selectedPackId, result.review.id)
    })
  }

  function updateReview(updates) {
    if (!selectedReviewId) return
    runAction("status", async () => {
      await apiPatch(`${reviewBase}/reviews/${selectedReviewId}`, updates)
      setMessage("Review status updated.")
      await load(selectedPackId, selectedReviewId)
    })
  }

  function updateChecklist(item, status) {
    runAction(`check-${item.id}`, async () => {
      await apiPatch(`${reviewBase}/checklist-items/${item.id}`, { status })
      setMessage("Checklist updated.")
      await load(selectedPackId, selectedReviewId)
    })
  }

  function addMapping(event) {
    event.preventDefault()
    if (!selectedPackId) return
    runAction("mapping", async () => {
      await apiPost(`${reviewBase}/packs/${selectedPackId}/field-mappings`, {
        ...mappingForm,
        item_id: mappingForm.item_id || null,
        mapping_confidence: Number(mappingForm.mapping_confidence || 0),
      })
      setMessage("Field mapping added.")
      setMappingForm(defaultMapping)
      await load(selectedPackId, selectedReviewId)
    })
  }

  function detectConflicts() {
    if (!selectedPackId) return
    runAction("conflicts", async () => {
      const result = await apiPost(`${reviewBase}/packs/${selectedPackId}/detect-conflicts`, {})
      setMessage(result.plain_language_summary || "Conflict check complete.")
      await load(selectedPackId, selectedReviewId)
    })
  }

  function resolveConflict(conflict, status) {
    runAction(`conflict-${conflict.id}`, async () => {
      await apiPatch(`${reviewBase}/conflicts/${conflict.id}`, { status })
      setMessage("Conflict metadata updated.")
      await load(selectedPackId, selectedReviewId)
    })
  }

  function markReadiness() {
    if (!selectedPackId) return
    runAction("readiness", async () => {
      await apiPost(`${reviewBase}/packs/${selectedPackId}/promotion-readiness`, {
        review_id: selectedReviewId || null,
        safe_for_agency_internal_crm: Boolean(selectedReview?.safe_for_agency_internal_crm),
        safe_for_agency_display: Boolean(selectedReview?.safe_for_agency_display),
        safe_for_cms_display: Boolean(selectedReview?.safe_for_cms_display),
        safe_for_client_portal_later: Boolean(selectedReview?.safe_for_client_portal_later),
        safe_for_offer_builder: Boolean(selectedReview?.safe_for_offer_builder),
      })
      setMessage("Promotion-readiness metadata recorded.")
      await load(selectedPackId, selectedReviewId)
    })
  }

  function createSnapshot() {
    if (!selectedReviewId) return
    runAction("snapshot", async () => {
      await apiPost(`${reviewBase}/reviews/${selectedReviewId}/snapshots`, {
        snapshot_type: "status_changed",
        metadata_json: { note: "Manual platform review snapshot" },
      })
      setMessage("Review snapshot created.")
      await load(selectedPackId, selectedReviewId)
    })
  }

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Data Pack Reviews</h2>
              <p className="mt-1 text-sm text-slate-600">Review checklists, field mappings, conflicts, and promotion-readiness metadata.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={detectConflicts} disabled={!selectedPackId || working === "conflicts"}><RefreshCw className="h-4 w-4" />Conflicts</button>
              <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createSnapshot} disabled={!selectedReviewId || working === "snapshot"}><FileCheck2 className="h-4 w-4" />Snapshot</button>
              <button className="inline-flex items-center gap-2 aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={markReadiness} disabled={!selectedPackId || working === "readiness"}><CheckCircle2 className="h-4 w-4" />Readiness</button>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 p-4">
                  <h3 className="font-semibold text-slate-950">Data packs</h3>
                </div>
                {!state?.packs?.length ? <EmptyState title="No data packs" body="Create a data pack before starting review." /> : (
                  <div className="divide-y divide-slate-100">
                    {state.packs.map((pack) => (
                      <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedPackId === pack.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(pack.id, "")} key={pack.id}>
                        <p className="font-semibold text-slate-950">{pack.name}</p>
                        <p className="mt-1 text-sm text-slate-600">{(pack.airline_codes || []).join(", ") || "No airline code"} · {label(pack.verification_status)}</p>
                      </button>
                    ))}
                  </div>
                )}
                <div className="border-t border-slate-200 p-4">
                  <button className="inline-flex w-full items-center justify-center gap-2 aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createReview} disabled={!selectedPackId || working === "review"}><GitBranch className="h-4 w-4" />Start review</button>
                </div>
              </section>

              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 p-4">
                  <h3 className="font-semibold text-slate-950">Reviews</h3>
                </div>
                {!state?.reviews?.length ? <EmptyState title="No reviews yet" body="Start a review from a staged data pack." /> : (
                  <div className="divide-y divide-slate-100">
                    {state.reviews.map((review) => (
                      <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedReviewId === review.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(review.pack_id, review.id)} key={review.id}>
                        <p className="font-semibold text-slate-950">{review.review_title || "Data pack review"}</p>
                        <p className="mt-1 text-sm text-slate-600">{label(review.status)} · {review.open_conflict_count || 0} open conflict(s)</p>
                      </button>
                    ))}
                  </div>
                )}
              </section>
            </div>

            {!selectedReview ? <EmptyState title="Select or start a review" body="Review details will appear here." /> : (
              <div className="space-y-4">
                <section className="rounded-lg border border-slate-200 bg-white p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-950">{selectedReview.review_title || "Data pack review"}</h3>
                      <p className="mt-1 text-sm text-slate-600">{selectedReview.plain_language_coverage_summary || "Coverage summary pending."}</p>
                    </div>
                    <Status text={label(selectedReview.status)} ready={selectedReview.promotion_ready} />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => updateReview({ status: "approved" })}>Approve</button>
                    <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => updateReview({ status: "rejected", rejection_reason: "Needs more source review." })}>Reject</button>
                    <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => updateReview({ status: "in_review" })}>Needs review</button>
                  </div>
                </section>

                <section className="rounded-lg border border-slate-200 bg-white">
                  <div className="border-b border-slate-200 p-4">
                    <h3 className="font-semibold text-slate-950">Checklist</h3>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {(state.detail.checklist_items || []).map((item) => (
                      <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm" key={item.id}>
                        <div>
                          <p className="font-semibold text-slate-950">{item.label}</p>
                          <p className="mt-1 text-slate-600">{item.description || label(item.scope)}</p>
                        </div>
                        <div className="flex gap-2">
                          <Status text={label(item.status)} ready={item.status === "passed" || item.status === "waived"} />
                          <button className="rounded-md border border-slate-300 px-2 py-1 font-semibold" type="button" onClick={() => updateChecklist(item, "passed")}>Pass</button>
                          <button className="rounded-md border border-slate-300 px-2 py-1 font-semibold" type="button" onClick={() => updateChecklist(item, "failed")}>Fail</button>
                          <button className="rounded-md border border-slate-300 px-2 py-1 font-semibold" type="button" onClick={() => updateChecklist(item, "waived")}>Waive</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-lg border border-slate-200 bg-white p-5">
                  <h3 className="font-semibold text-slate-950">Field mapping</h3>
                  <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={addMapping}>
                    <Select label="Item" value={mappingForm.item_id} onChange={(value) => setMappingForm({ ...mappingForm, item_id: value })} options={[["", "Pack level"], ...((state.detail.items || []).map((item) => [item.id, item.display_name]))]} />
                    <Input label="Source path" value={mappingForm.source_payload_path} onChange={(value) => setMappingForm({ ...mappingForm, source_payload_path: value })} />
                    <Input label="Target collection" value={mappingForm.target_collection} onChange={(value) => setMappingForm({ ...mappingForm, target_collection: value })} />
                    <Input label="Target field" value={mappingForm.target_field_path} onChange={(value) => setMappingForm({ ...mappingForm, target_field_path: value })} />
                    <Select label="Status" value={mappingForm.mapping_status} onChange={(value) => setMappingForm({ ...mappingForm, mapping_status: value })} options={["draft", "reviewed", "approved", "rejected"].map((value) => [value, label(value)])} />
                    <Input label="Confidence" value={mappingForm.mapping_confidence} type="number" step="0.1" onChange={(value) => setMappingForm({ ...mappingForm, mapping_confidence: value })} />
                    <button className="inline-flex items-center justify-center gap-2 aa-primary-action rounded-md px-3 py-2 text-sm font-semibold md:col-span-2" type="submit"><GitBranch className="h-4 w-4" />Add mapping</button>
                  </form>
                  <div className="mt-4 divide-y divide-slate-100 border-t border-slate-100">
                    {(state.detail.field_mappings || packItems).map((mapping) => (
                      <div className="grid gap-2 py-3 text-sm md:grid-cols-[1fr_1fr_120px]" key={mapping.id}>
                        <span>{mapping.source_payload_path} → {mapping.target_field_path}</span>
                        <span className="text-slate-600">{mapping.target_collection}</span>
                        <Status text={label(mapping.mapping_status)} ready={mapping.mapping_status === "approved"} />
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-lg border border-slate-200 bg-white">
                  <div className="border-b border-slate-200 p-4">
                    <h3 className="font-semibold text-slate-950">Conflicts and readiness</h3>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {(state.detail.conflicts || []).map((conflict) => (
                      <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm" key={conflict.id}>
                        <div>
                          <p className="font-semibold text-slate-950">{conflict.plain_language_summary}</p>
                          <p className="mt-1 text-slate-600">{conflict.suggested_resolution || label(conflict.conflict_type)}</p>
                        </div>
                        <div className="flex gap-2">
                          <Status text={label(conflict.status)} ready={conflict.status !== "open"} />
                          <button className="rounded-md border border-slate-300 px-2 py-1 font-semibold" type="button" onClick={() => resolveConflict(conflict, "acknowledged")}>Acknowledge</button>
                          <button className="rounded-md border border-slate-300 px-2 py-1 font-semibold" type="button" onClick={() => resolveConflict(conflict, "resolved")}>Resolve</button>
                        </div>
                      </div>
                    ))}
                    {(state.detail.promotion_readiness || []).map((item) => (
                      <div className="p-4 text-sm" key={item.id}>
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <p className="font-semibold text-slate-950">{item.readiness_summary || "Promotion-readiness metadata"}</p>
                          <Status text={label(item.status)} ready={item.ready_for_promotion} />
                        </div>
                        {item.blocked_reason ? <p className="mt-2 text-slate-600">{item.blocked_reason}</p> : null}
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            )}
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

function Input({ label, value, onChange, type = "text", step }) {
  return (
    <label className="block text-sm">
      <span className="font-semibold text-slate-700">{label}</span>
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" type={type} step={step} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="block text-sm">
      <span className="font-semibold text-slate-700">{label}</span>
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => <option value={optionValue} key={optionValue}>{optionLabel}</option>)}
      </select>
    </label>
  )
}

function Status({ text, ready }) {
  const tone = ready ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
