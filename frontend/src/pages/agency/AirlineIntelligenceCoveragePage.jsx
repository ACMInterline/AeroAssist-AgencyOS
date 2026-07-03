import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AirlineIntelligenceCoveragePage() {
  const [state, setState] = useState(null)
  const [selectedPackId, setSelectedPackId] = useState("")
  const [error, setError] = useState("")

  async function load(openPackId = selectedPackId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/airline-intelligence-data-packs`
    const [summary, coverage, packs] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/coverage`),
      apiGet(`${base}/packs`),
    ])
    const nextPackId = openPackId || packs.items?.[0]?.id || ""
    const detail = nextPackId ? await apiGet(`${base}/packs/${nextPackId}`) : null
    setSelectedPackId(nextPackId)
    setState({
      ...context,
      base,
      summary,
      coverage,
      packs: packs.items || [],
      detail,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const snapshot = state?.coverage?.coverage_snapshot
  const cards = useMemo(() => [
    ["Profiles", snapshot?.airlines_with_profiles || 0],
    ["Fleet", snapshot?.airlines_with_fleet || 0],
    ["Routes", snapshot?.airlines_with_routes || 0],
    ["Fare families", snapshot?.airlines_with_fare_families || 0],
    ["Baggage / ancillaries", snapshot?.airlines_with_ancillaries || 0],
    ["Special services rules", snapshot?.airlines_with_special_services_rules || 0],
    ["Offer builder readiness", snapshot?.airlines_safe_for_offer_builder || state?.summary?.offer_builder_safe_pack_count || 0],
    ["Website / CMS readiness", snapshot?.airlines_safe_for_cms_display || state?.summary?.cms_display_safe_pack_count || 0],
    ["Client portal future readiness", snapshot?.airlines_safe_for_client_portal_later || state?.summary?.client_portal_safe_pack_count || 0],
  ], [snapshot, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Coverage</h2>
            <p className="mt-1 text-sm text-slate-600">What airline data is available for your agency, shown as read-only coverage and readiness metadata.</p>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">What airline data is available?</h3>
            <p className="mt-2 text-sm text-slate-600">{state?.summary?.plain_language_overview || "Platform-owned data packs show which airline facts are ready for agency review. They do not create bookings, prices, tickets, or website/client portal content."}</p>
          </section>

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-5">
            {cards.map(([label, value]) => <CoverageCard label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <h3 className="font-semibold text-slate-950">Packs available to this agency</h3>
              </div>
              {!state?.packs?.length ? <EmptyState title="No airline data packs yet" body="Platform owners have not staged airline data coverage for agency review." /> : (
                <div className="divide-y divide-slate-100">
                  {state.packs.map((pack) => (
                    <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedPackId === pack.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(pack.id)} key={pack.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{pack.name}</p>
                          <p className="mt-1 text-sm text-slate-600">{(pack.airline_codes || []).join(", ") || "No airline code"} · {label(pack.pack_type)}</p>
                        </div>
                        <Status pack={pack} />
                      </div>
                      <p className="mt-2 text-sm text-slate-600">{pack.human_summary || pack.operator_guidance || "No agency summary yet."}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-4">
              {!state?.detail?.pack ? <EmptyState title="Select a data pack" body="Choose a pack to see read-only airline coverage details." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">{state.detail.pack.name}</h3>
                        <p className="mt-1 text-sm text-slate-600">{state.detail.pack.human_summary || "Read-only airline data coverage."}</p>
                      </div>
                      <Status pack={state.detail.pack} />
                    </div>
                    <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
                      <Flag label="Internal CRM" enabled={state.detail.pack.safe_for_agency_internal_crm} />
                      <Flag label="Offers" enabled={state.detail.pack.safe_for_offer_builder} />
                      <Flag label="Client documents" enabled={state.detail.pack.safe_for_agency_display} />
                      <Flag label="Agency website content" enabled={state.detail.pack.safe_for_cms_display} />
                      <Flag label="Future client portal display" enabled={state.detail.pack.safe_for_client_portal_later} />
                      <Flag label="Operationally verified" enabled={state.detail.pack.is_operationally_verified} />
                    </div>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">Read-only coverage items</h3>
                    </div>
                    <div className="divide-y divide-slate-100">
                      {(state.detail.items || []).map((item) => (
                        <div className="p-4 text-sm" key={item.id}>
                          <div className="grid gap-3 md:grid-cols-[90px_180px_1fr_150px]">
                            <span className="font-semibold text-slate-950">{item.airline_iata_code || "-"}</span>
                            <span>{label(item.target_domain)}</span>
                            <span>{item.display_name}</span>
                            <span className="text-slate-600">{friendlyItemStatus(item)}</span>
                          </div>
                          <p className="mt-2 text-slate-600">{item.plain_language_summary || "Needs platform verification."}</p>
                          {item.warnings?.length ? <div className="mt-3 flex flex-wrap gap-2">{item.warnings.map((warning) => <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700 ring-1 ring-amber-200" key={warning}>{warning}</span>)}</div> : null}
                        </div>
                      ))}
                    </div>
                  </section>
                </>
              )}
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">What this means for your agency</h3>
            <div className="mt-3 grid gap-3 text-sm md:grid-cols-2 xl:grid-cols-5">
              <Meaning label="Offers" enabled={(state?.summary?.offer_builder_safe_pack_count || 0) > 0} text="Reviewed data can support future offer context." />
              <Meaning label="Client documents" enabled={(state?.summary?.agency_display_safe_pack_count || 0) > 0} text="Safe agency display metadata can later support document explanations." />
              <Meaning label="Agency website" enabled={(state?.summary?.cms_display_safe_pack_count || 0) > 0} text="CMS-ready flags are staging only; nothing is published here." />
              <Meaning label="Client portal later" enabled={(state?.summary?.client_portal_safe_pack_count || 0) > 0} text="Portal readiness is future-facing only." />
              <Meaning label="Special services" enabled={(snapshot?.airlines_with_special_services_rules || 0) > 0} text="Special-service coverage can support staff review." />
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function CoverageCard({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Flag({ label, enabled }) {
  return <span className={`rounded-md px-3 py-2 ${enabled ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-500"}`}>{label}: {enabled ? "Ready to review" : "Needs verification"}</span>
}

function Meaning({ label, enabled, text }) {
  return (
    <div className={`rounded-md p-3 ${enabled ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-600"}`}>
      <p className="font-semibold">{label}</p>
      <p className="mt-1">{text}</p>
    </div>
  )
}

function Status({ pack }) {
  const text = pack.is_demo_data ? "Demo/sample data" : pack.is_operationally_verified ? "Ready to review" : "Needs platform verification"
  const tone = pack.is_operationally_verified && !pack.is_demo_data ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function friendlyItemStatus(item) {
  if (item.is_demo_data) return "Demo/sample data"
  if (!item.is_operationally_verified) return "Needs platform verification"
  if (item.validation_status === "valid") return "Ready to review"
  return label(item.validation_status || item.verification_status)
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
