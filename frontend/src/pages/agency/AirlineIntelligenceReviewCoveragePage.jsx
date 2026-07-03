import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AirlineIntelligenceReviewCoveragePage() {
  const [state, setState] = useState(null)
  const [selectedReviewId, setSelectedReviewId] = useState("")
  const [error, setError] = useState("")

  async function load(openReviewId = selectedReviewId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/airline-intelligence-data-pack-reviews`
    const [summary, coverage, reviews] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/coverage`),
      apiGet(`${base}/reviews`),
    ])
    const reviewItems = reviews.items || []
    const nextReviewId = openReviewId || reviewItems[0]?.id || ""
    const detail = nextReviewId ? await apiGet(`${base}/reviews/${nextReviewId}`) : null
    setSelectedReviewId(nextReviewId)
    setState({
      ...context,
      base,
      summary,
      coverage,
      reviews: reviewItems,
      detail,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = useMemo(() => [
    ["Reviewed packs", state?.summary?.review_count || 0],
    ["Ready metadata", state?.summary?.promotion_ready_count || 0],
    ["Open issues", state?.summary?.open_conflict_count || 0],
    ["Internal CRM", state?.summary?.agency_internal_crm_safe_count || 0],
    ["Agency display", state?.summary?.agency_display_safe_count || 0],
    ["Website / CMS", state?.summary?.cms_display_safe_count || 0],
    ["Client portal later", state?.summary?.client_portal_safe_count || 0],
    ["Offer builder", state?.summary?.offer_builder_safe_count || 0],
  ], [state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Review Coverage</h2>
            <p className="mt-1 text-sm text-slate-600">Reviewed airline intelligence coverage and safe-use readiness for agency work.</p>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Coverage summary</h3>
            <p className="mt-2 text-sm text-slate-600">{state?.summary?.plain_language_overview || "Reviewed airline intelligence coverage is read-only and metadata-only."}</p>
          </section>

          <section className="grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <h3 className="font-semibold text-slate-950">Reviewed coverage</h3>
              </div>
              {!state?.reviews?.length ? <EmptyState title="No reviewed coverage yet" body="Platform owners have not marked airline data pack reviews for agency visibility." /> : (
                <div className="divide-y divide-slate-100">
                  {state.reviews.map((review) => (
                    <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedReviewId === review.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(review.id)} key={review.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{review.pack_name || "Airline data pack"}</p>
                          <p className="mt-1 text-sm text-slate-600">{label(review.status)}</p>
                        </div>
                        <Status text={review.promotion_ready ? "Ready metadata" : "Needs review"} ready={review.promotion_ready} />
                      </div>
                      <p className="mt-2 text-sm text-slate-600">{review.plain_language_coverage_summary || "No coverage summary yet."}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-4">
              {!state?.detail?.review ? <EmptyState title="Select reviewed coverage" body="Choose a review to see safe-use readiness." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">{state.detail.review.pack_name || state.detail.pack?.name || "Airline data pack"}</h3>
                        <p className="mt-1 text-sm text-slate-600">{state.detail.coverage_summary || state.detail.review.plain_language_coverage_summary}</p>
                      </div>
                      <Status text={label(state.detail.review.status)} ready={state.detail.review.promotion_ready} />
                    </div>
                    <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
                      <Flag label="Internal CRM" enabled={state.detail.review.safe_for_agency_internal_crm} />
                      <Flag label="Agency display" enabled={state.detail.review.safe_for_agency_display} />
                      <Flag label="Website / CMS" enabled={state.detail.review.safe_for_cms_display} />
                      <Flag label="Client portal later" enabled={state.detail.review.safe_for_client_portal_later} />
                      <Flag label="Offer builder" enabled={state.detail.review.safe_for_offer_builder} />
                      <Flag label="Promotion-ready metadata" enabled={state.detail.review.promotion_ready} />
                    </div>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">Readiness history</h3>
                    </div>
                    <div className="divide-y divide-slate-100">
                      {(state.detail.promotion_readiness || []).map((item) => (
                        <div className="p-4 text-sm" key={item.id}>
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <p className="font-semibold text-slate-950">{item.readiness_summary || "Promotion-readiness metadata"}</p>
                            <Status text={label(item.status)} ready={item.ready_for_promotion} />
                          </div>
                          {item.blocked_reason ? <p className="mt-2 text-slate-600">{item.blocked_reason}</p> : null}
                          <div className="mt-3 grid gap-2 md:grid-cols-3">
                            <Flag label="Checklist complete" enabled={item.checklist_complete} />
                            <Flag label="Mappings approved" enabled={(item.approved_mapping_count || 0) > 0} />
                            <Flag label="No open conflicts" enabled={(item.open_conflict_count || 0) === 0} />
                          </div>
                        </div>
                      ))}
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

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Flag({ label, enabled }) {
  return <span className={`rounded-md px-3 py-2 ${enabled ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-500"}`}>{label}: {enabled ? "Ready" : "Needs review"}</span>
}

function Status({ text, ready }) {
  const tone = ready ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
