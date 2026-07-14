import { useEffect, useMemo, useState } from "react"
import Play from "lucide-react/dist/esm/icons/play.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  return <span className="inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{String(children || "unknown").replaceAll("_", " ")}</span>
}

function Score({ value }) {
  const score = Number(value || 0)
  const tone = score >= 80 ? "bg-emerald-100 text-emerald-800" : score >= 50 ? "bg-amber-100 text-amber-800" : "bg-rose-100 text-rose-800"
  return <span className={`inline-flex min-w-12 justify-center rounded-md px-2 py-1 text-xs font-semibold ${tone}`}>{score}</span>
}

export default function AirlineServiceCoveragePage() {
  const [state, setState] = useState(null)
  const [airline, setAirline] = useState("")
  const [family, setFamily] = useState("")
  const [assessmentAirline, setAssessmentAirline] = useState("")
  const [assessmentFamily, setAssessmentFamily] = useState("petc")
  const [running, setRunning] = useState(false)
  const [error, setError] = useState("")

  async function load() {
    const params = new URLSearchParams()
    if (airline) params.set("airline_code", airline)
    if (family) params.set("service_family", family)
    const query = params.toString() ? `?${params}` : ""
    const [summary, payload] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/airline-service-coverage${query}`)])
    setState({ currentUser: summary.current_user, ...payload })
  }

  async function runAssessment(event) {
    event.preventDefault()
    setRunning(true)
    setError("")
    try {
      await apiPost("/api/platform/airline-service-coverage/assessments", {
        airline_codes: assessmentAirline.split(",").map((value) => value.trim()).filter(Boolean),
        service_families: assessmentFamily.split(",").map((value) => value.trim()).filter(Boolean),
      })
      setAirline(assessmentAirline.split(",")[0]?.trim() || "")
      setFamily(assessmentFamily.split(",")[0]?.trim() || "")
      await load()
    } catch (err) { setError(err.message) } finally { setRunning(false) }
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])
  const priorityGaps = useMemo(() => [...(state?.gaps || [])].sort((a, b) => Number(b.critical) - Number(a.critical)).slice(0, 20), [state])

  return (
    <PlatformLayout user={state?.currentUser}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header><p className="text-sm font-semibold uppercase text-blue-700">Knowledge operations</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Service Coverage</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Published usability, deterministic coverage scores, critical knowledge gaps, and remediation ownership by airline and service scope.</p></header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Metric label="Airlines" value={state?.summary?.airline_count} /><Metric label="Coverage cells" value={state?.summary?.cell_count} /><Metric label="Operationally ready" value={state?.summary?.operational_ready_cell_count} /><Metric label="Critical gaps" value={state?.summary?.critical_gap_count} /><Metric label="Usability score" value={state?.summary?.score_summary?.operational_usability} /></section>

          <form className="grid gap-3 border-y border-slate-200 py-4 md:grid-cols-[1fr_1fr_auto]" onSubmit={runAssessment}>
            <label className="text-sm font-medium text-slate-700">Airline codes<input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" placeholder="LH, BA" value={assessmentAirline} onChange={(event) => setAssessmentAirline(event.target.value)} required /></label>
            <label className="text-sm font-medium text-slate-700">Service families or codes<input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" placeholder="PETC, WCHC" value={assessmentFamily} onChange={(event) => setAssessmentFamily(event.target.value)} required /></label>
            <button type="submit" disabled={running} className="mt-auto inline-flex items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"><Play className="h-4 w-4" />{running ? "Assessing" : "Run assessment"}</button>
          </form>

          <form className="flex flex-wrap gap-2" onSubmit={(event) => { event.preventDefault(); load().catch((err) => setError(err.message)) }}><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline" value={airline} onChange={(event) => setAirline(event.target.value)} /><select className="min-w-56 rounded-md border border-slate-300 px-3 py-2 text-sm" value={family} onChange={(event) => setFamily(event.target.value)}><option value="">All service families</option>{state?.filters?.service_catalog?.map((item) => <option key={item.service_family} value={item.service_family}>{item.service_family.replaceAll("_", " ")}</option>)}</select><button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold"><RefreshCw className="h-4 w-4" />Refresh</button></form>

          <section><div className="flex flex-wrap items-end justify-between gap-2"><div><h2 className="font-semibold text-slate-950">Airline × service matrix</h2><p className="mt-1 text-sm text-slate-500">Score heatmap and readiness guard result</p></div><Status>{state?.assessment_id ? "assessment loaded" : "no assessment"}</Status></div><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[980px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Service</th><th className="px-3 py-2">Coverage</th><th className="px-3 py-2">Complete</th><th className="px-3 py-2">Confidence</th><th className="px-3 py-2">Freshness</th><th className="px-3 py-2">Tests</th><th className="px-3 py-2">Publish</th><th className="px-3 py-2">Usability</th><th className="px-3 py-2">Critical gaps</th></tr></thead><tbody>{state?.cells?.map((cell) => <tr className="border-t border-slate-200" key={cell.id}><td className="px-3 py-3 font-semibold">{cell.airline_code}</td><td className="px-3 py-3"><span className="block font-medium">{cell.service_family.replaceAll("_", " ")}</span><span className="text-xs text-slate-500">{cell.service_code || "All variants"}</span></td><td className="px-3 py-3"><Status>{cell.coverage_status}</Status></td><td className="px-3 py-3"><Score value={cell.completeness_score} /></td><td className="px-3 py-3"><Score value={cell.confidence_score} /></td><td className="px-3 py-3"><Score value={cell.freshness_score} /></td><td className="px-3 py-3"><Score value={cell.test_coverage_score} /></td><td className="px-3 py-3"><Score value={cell.publication_readiness_score} /></td><td className="px-3 py-3"><Score value={cell.operational_usability_score} /></td><td className="px-3 py-3 font-semibold text-rose-700">{cell.critical_gap_types?.length || 0}</td></tr>)}</tbody></table></div>{!state?.cells?.length ? <p className="mt-4 text-sm text-slate-600">No coverage assessment matches this view.</p> : null}</section>

          <div className="grid gap-6 xl:grid-cols-2">
            <section><h2 className="font-semibold text-slate-950">Priority gap register</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{priorityGaps.map((gap) => <div className="py-3" key={gap.id}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold text-slate-950">{gap.airline_code} · {gap.service_family.replaceAll("_", " ")}</p><p className="mt-1 text-sm text-slate-600">{gap.description}</p></div><Status>{gap.severity}</Status></div><p className="mt-2 text-xs text-slate-500">{gap.remediation_guidance}</p></div>)}</div></section>
            <section><h2 className="font-semibold text-slate-950">Remediation and population progress</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.remediation_plans?.map((plan) => <div className="py-3" key={plan.id}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold text-slate-950">{plan.airline_code}</p><p className="mt-1 text-sm text-slate-600">{plan.gap_ids?.length || 0} governed actions · toolkit {plan.population_toolkit_id ? "linked" : "not linked"}</p></div><Status>{plan.priority}</Status></div><div className="mt-3 h-2 overflow-hidden rounded bg-slate-100"><div className="h-full bg-blue-600" style={{ width: `${Math.max(0, Math.min(100, plan.progress_percent || 0))}%` }} /></div></div>)}</div></section>
          </div>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
