import { useEffect, useMemo, useState } from "react"
import { CheckCircle2, CircleAlert, Layers3, RefreshCw, ShieldCheck } from "lucide-react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const splitValues = (value) => value.split(",").map((item) => item.trim()).filter(Boolean)

function Status({ children }) {
  const value = String(children || "unknown")
  const color = value.includes("blocked") || value.includes("critical") ? "bg-red-50 text-red-700" : value.includes("ready") || value === "passed" || value === "released" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${color}`}>{value.replaceAll("_", " ")}</span>
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value ?? 0}</p></div>
}

export default function AirlineIntelligenceReadinessPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [airlineCode, setAirlineCode] = useState("")
  const [services, setServices] = useState("PETC,WCHC,UMNR")
  const [candidate, setCandidate] = useState({ assessment: "", agencies: "", modules: "offer_builder,operational_advisor", rollback: "", publication: "", version: "", effectiveFrom: "", client: "", internal: "" })
  const [wave, setWave] = useState({ name: "", airlines: "", services: "PETC,WCHC,UMNR", reviewer: "", due: "" })

  async function load() {
    const [me, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/platform/airline-intelligence-readiness"),
    ])
    setState({ me, ...response })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function runAssessment(event) {
    event.preventDefault()
    setNotice("")
    try {
      const response = await apiPost("/api/platform/airline-intelligence-readiness/assessments/run", { airline_code: airlineCode.toUpperCase(), required_service_families: splitValues(services) })
      setNotice(`Assessment ${response.assessment.assessment_reference} completed at ${response.assessment.readiness_score}/100.`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function createCandidate(event) {
    event.preventDefault()
    setNotice("")
    try {
      const response = await apiPost("/api/platform/airline-intelligence-readiness/release-candidates", {
        readiness_assessment_id: candidate.assessment,
        candidate_name: "Controlled airline intelligence release",
        assigned_agency_ids: splitValues(candidate.agencies),
        usable_modules: splitValues(candidate.modules),
        rollback_reference: candidate.rollback,
        publication_id: candidate.publication || null,
        version_snapshot_id: candidate.version,
        effective_from: candidate.effectiveFrom,
        client_facing_summary: candidate.client,
        internal_release_notes: candidate.internal,
      })
      setNotice(`Release candidate ${response.candidate.candidate_reference} created as ${response.candidate.candidate_status.replaceAll("_", " ")}.`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function createWave(event) {
    event.preventDefault()
    setNotice("")
    try {
      const response = await apiPost("/api/platform/airline-intelligence-readiness/population-waves", {
        wave_name: wave.name,
        wave_status: "planning",
        airline_codes: splitValues(wave.airlines),
        service_family_targets: splitValues(wave.services),
        responsible_reviewer: wave.reviewer,
        due_date: wave.due || null,
      })
      setNotice(`Population wave ${response.population_wave.wave_reference} created. No publication was triggered.`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const summary = state?.summary || {}
  const assessments = state?.assessments || []
  const assessmentOptions = useMemo(() => assessments.map((item) => ({ value: item.id, label: `${item.airline_code} · ${item.assessment_reference} · ${item.readiness_score}/100` })), [assessments])

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase text-blue-700">Epic 55 Release Governance</p>
              <h1 className="mt-2 text-2xl font-semibold text-slate-950">Airline Intelligence Readiness</h1>
              <p className="mt-1 max-w-5xl text-sm text-slate-600">Deterministic readiness, release gates, and population-wave metadata across canonical airline intelligence sources. Human release authority remains final; this page never auto-publishes, seeds production, calls providers, or mutates historical snapshots.</p>
            </div>
            <button type="button" title="Refresh readiness" onClick={() => load().catch((err) => setError(err.message))} className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-700"><RefreshCw className="h-4 w-4" /></button>
          </header>

          {notice ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div> : null}
          {error ? <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <Metric label="Assessments" value={summary.assessment_count} />
            <Metric label="Average score" value={summary.average_readiness_score} />
            <Metric label="Release ready" value={summary.release_ready_count} />
            <Metric label="Candidates" value={summary.release_candidate_count} />
            <Metric label="Blocked gates" value={summary.blocked_gate_count} />
            <Metric label="Critical issues" value={summary.critical_issue_count} />
          </section>

          <section className="grid gap-4 xl:grid-cols-3">
            <form onSubmit={runAssessment} className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-blue-700" /><h2 className="font-semibold text-slate-950">Run deterministic assessment</h2></div>
              <label className="mt-4 block text-xs font-semibold text-slate-600">Airline code<input required maxLength="3" value={airlineCode} onChange={(event) => setAirlineCode(event.target.value)} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" /></label>
              <label className="mt-3 block text-xs font-semibold text-slate-600">Required service families<input value={services} onChange={(event) => setServices(event.target.value)} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" /></label>
              <button className="mt-4 inline-flex items-center gap-2 rounded-md bg-blue-700 px-3 py-2 text-sm font-semibold text-white"><CheckCircle2 className="h-4 w-4" />Assess</button>
            </form>

            <form onSubmit={createCandidate} className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-2"><Layers3 className="h-4 w-4 text-blue-700" /><h2 className="font-semibold text-slate-950">Create release candidate</h2></div>
              <select required value={candidate.assessment} onChange={(event) => setCandidate({ ...candidate, assessment: event.target.value })} className="mt-4 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"><option value="">Select assessment</option>{assessmentOptions.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select>
              <div className="mt-3 grid gap-2 sm:grid-cols-2"><input required placeholder="Agency IDs" value={candidate.agencies} onChange={(event) => setCandidate({ ...candidate, agencies: event.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" /><input required placeholder="Usable modules" value={candidate.modules} onChange={(event) => setCandidate({ ...candidate, modules: event.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" /></div>
              <div className="mt-2 grid gap-2 sm:grid-cols-2"><input required placeholder="Version snapshot" value={candidate.version} onChange={(event) => setCandidate({ ...candidate, version: event.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" /><input required placeholder="Rollback reference" value={candidate.rollback} onChange={(event) => setCandidate({ ...candidate, rollback: event.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" /></div>
              <div className="mt-2 grid gap-2 sm:grid-cols-2"><input placeholder="Published record ID" value={candidate.publication} onChange={(event) => setCandidate({ ...candidate, publication: event.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" /><input required type="date" value={candidate.effectiveFrom} onChange={(event) => setCandidate({ ...candidate, effectiveFrom: event.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" /></div>
              <input required placeholder="Client-facing summary" value={candidate.client} onChange={(event) => setCandidate({ ...candidate, client: event.target.value })} className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" /><input required placeholder="Internal release instruction" value={candidate.internal} onChange={(event) => setCandidate({ ...candidate, internal: event.target.value })} className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
              <button className="mt-4 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-800">Create and evaluate gates</button>
            </form>

            <form onSubmit={createWave} className="rounded-lg border border-slate-200 bg-white p-5">
              <h2 className="font-semibold text-slate-950">Track population wave</h2>
              <input required placeholder="Wave name" value={wave.name} onChange={(event) => setWave({ ...wave, name: event.target.value })} className="mt-4 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
              <input required placeholder="Airline codes" value={wave.airlines} onChange={(event) => setWave({ ...wave, airlines: event.target.value })} className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" />
              <input placeholder="Service families" value={wave.services} onChange={(event) => setWave({ ...wave, services: event.target.value })} className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
              <div className="mt-2 grid gap-2 sm:grid-cols-2"><input placeholder="Reviewer" value={wave.reviewer} onChange={(event) => setWave({ ...wave, reviewer: event.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" /><input type="date" value={wave.due} onChange={(event) => setWave({ ...wave, due: event.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" /></div>
              <button className="mt-4 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-800">Create wave metadata</button>
            </form>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-slate-950">Airline readiness matrix</h2>
            {(state?.readiness_matrix || []).length ? <div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[900px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Score</th><th className="px-3 py-2">Confidence</th><th className="px-3 py-2">Freshness</th><th className="px-3 py-2">Service coverage</th><th className="px-3 py-2">Blockers</th><th className="px-3 py-2">Recent changes</th></tr></thead><tbody>{state.readiness_matrix.map((item) => <tr className="border-t border-slate-200" key={item.assessment_id}><td className="px-3 py-3 font-semibold">{item.airline_code}</td><td className="px-3 py-3"><Status>{item.status}</Status></td><td className="px-3 py-3">{item.score}/100</td><td className="px-3 py-3">{item.confidence}/100</td><td className="px-3 py-3">{item.freshness}/100</td><td className="px-3 py-3">{item.service_coverage}/100</td><td className="px-3 py-3">{item.critical_blockers}</td><td className="px-3 py-3 text-slate-600">{item.recent_changes?.slice(0, 2).join(", ") || "None recorded"}</td></tr>)}</tbody></table></div> : <EmptyState title="No readiness assessments" body="Run a deterministic assessment to populate the matrix." />}
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Panel title="Release candidates" items={state?.release_candidates || []} render={(item) => <div><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-950">{item.airline_code} · {item.candidate_name}</p><p className="mt-1 text-xs text-slate-500">{item.candidate_reference} · rollback {item.rollback_reference || "missing"}</p></div><Status>{item.candidate_status}</Status></div><div className="mt-3 grid grid-cols-3 gap-3 text-sm text-slate-600"><p>Score {item.readiness_score}</p><p>{item.assigned_agency_ids?.length || 0} agencies</p><p>{item.gate_ids?.length || 0} gates</p></div></div>} />
            <Panel title="Release gates" items={state?.release_gates || []} render={(item) => <div className="flex items-center justify-between gap-3"><div><p className="font-semibold text-slate-950">{item.label}</p><p className="mt-1 text-sm text-slate-600">{item.observed_signal}</p></div><Status>{item.gate_status}</Status></div>} />
            <Panel title="Population waves" items={state?.population_waves || []} render={(item) => <div><div className="flex items-start justify-between gap-3"><p className="font-semibold text-slate-950">{item.wave_name}</p><Status>{item.wave_status}</Status></div><p className="mt-2 text-sm text-slate-600">{item.airline_codes?.join(", ")} · {item.service_family_targets?.join(", ") || "All services"}</p><p className="mt-1 text-xs text-slate-500">{item.completion_percentage}% complete · no automatic publication</p></div>} />
            <Panel title="Blocker register" items={state?.blockers || []} render={(item) => <div className="flex gap-3"><CircleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" /><div><div className="flex flex-wrap items-center gap-2"><p className="font-semibold text-slate-950">{item.title}</p><Status>{item.severity}</Status></div><p className="mt-1 text-sm text-slate-600">{item.description}</p><p className="mt-1 text-xs text-slate-500">{item.remediation_guidance}</p></div></div>} />
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Panel({ title, items, render }) {
  return <section><div className="flex items-center justify-between gap-3"><h2 className="text-lg font-semibold text-slate-950">{title}</h2><span className="text-sm text-slate-500">{items.length}</span></div>{items.length ? <div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{items.slice(0, 12).map((item) => <div className="py-4" key={item.id}>{render(item)}</div>)}</div> : <EmptyState title={`No ${title.toLowerCase()}`} body="Governance metadata will appear here when records are created." />}</section>
}
