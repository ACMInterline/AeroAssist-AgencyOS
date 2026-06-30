import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function PlatformGdsParserPage() {
  const [state, setState] = useState(null)
  const [selectedProfileId, setSelectedProfileId] = useState("")
  const [versionForm, setVersionForm] = useState({ version_label: "", change_notes: "" })
  const [evaluationForm, setEvaluationForm] = useState({ parser_version_id: "" })
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(profileId = selectedProfileId) {
    const [summary, profiles, samples, evaluations] = await Promise.all([
      apiGet("/api/platform/summary"),
      apiGet("/api/platform/gds-parser/profiles"),
      apiGet("/api/platform/gds-parser/training-samples"),
      apiGet("/api/platform/gds-parser/evaluations"),
    ])
    const nextProfileId = profileId || profiles.items?.[0]?.id || ""
    const versions = nextProfileId ? await apiGet(`/api/platform/gds-parser/profiles/${nextProfileId}/versions`) : { items: [] }
    setSelectedProfileId(nextProfileId)
    setState({
      summary,
      profiles: profiles.items || [],
      versions: versions.items || [],
      samples: samples.items || [],
      evaluations: evaluations.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function seedDefaults() {
    setWorking("seed")
    setError("")
    setMessage("")
    try {
      const result = await apiPost("/api/platform/gds-parser/profiles/seed-defaults", {})
      setMessage(`Parser defaults ready. Profiles created ${result.created_profile_count || 0}; versions created ${result.created_version_count || 0}.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function changeProfile(profileId) {
    setSelectedProfileId(profileId)
    await load(profileId)
  }

  async function createVersion(event) {
    event.preventDefault()
    setWorking("version")
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/platform/gds-parser/profiles/${selectedProfileId}/versions`, {
        version_label: versionForm.version_label,
        change_notes: versionForm.change_notes,
        rules_json: { source: "platform_governance_ui", external_services: false },
        extraction_schema_json: { entities: ["passenger", "segment", "ticket", "emd", "ssr", "osi", "pricing"] },
        known_limitations_json: [{ code: "foundation_rules", message: "Conservative deterministic parser rules." }],
      })
      setVersionForm({ version_label: "", change_notes: "" })
      setMessage("Draft parser version created.")
      await load(selectedProfileId)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function activateVersion(versionId) {
    setWorking(versionId)
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/platform/gds-parser/profiles/${selectedProfileId}/versions/${versionId}/activate`, {})
      setMessage("Parser version activated.")
      await load(selectedProfileId)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function reviewSample(sampleId, sampleStatus) {
    setWorking(`${sampleStatus}-${sampleId}`)
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/platform/gds-parser/training-samples/${sampleId}/review`, {
        sample_status: sampleStatus,
        review_notes: `Platform ${sampleStatus} review.`,
      })
      setMessage(`Training sample ${label(sampleStatus)}.`)
      await load(selectedProfileId)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createEvaluation(event) {
    event.preventDefault()
    setWorking("evaluation")
    setError("")
    setMessage("")
    try {
      await apiPost("/api/platform/gds-parser/evaluations", {
        parser_profile_id: selectedProfileId,
        parser_version_id: evaluationForm.parser_version_id,
        sample_ids: [],
      })
      setMessage("Evaluation run completed.")
      await load(selectedProfileId)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  const selectedProfile = useMemo(() => (state?.profiles || []).find((profile) => profile.id === selectedProfileId), [state, selectedProfileId])
  const activeVersion = useMemo(() => (state?.versions || []).find((version) => version.status === "active"), [state])

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">GDS Parser</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Parser Governance</h2>
              <p className="mt-1 text-sm text-slate-600">Profiles, versions, training samples, and evaluation runs for the deterministic parser foundation.</p>
            </div>
            <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={seedDefaults} disabled={working === "seed"}>
              {working === "seed" ? "Seeding..." : "Seed defaults"}
            </button>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Profiles" value={state?.profiles?.length || 0} />
            <Metric label="Versions" value={state?.versions?.length || 0} />
            <Metric label="Training samples" value={state?.samples?.length || 0} />
            <Metric label="Evaluations" value={state?.evaluations?.length || 0} />
          </section>

          <section className="grid gap-4 lg:grid-cols-[340px_minmax(0,1fr)]">
            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-100 px-5 py-4">
                <h3 className="font-semibold text-slate-950">Parser profiles</h3>
              </div>
              {state?.profiles?.length ? (
                <div className="divide-y divide-slate-100">
                  {state.profiles.map((profile) => (
                    <button className={`w-full px-5 py-4 text-left text-sm hover:bg-slate-50 ${profile.id === selectedProfileId ? "bg-blue-50" : ""}`} type="button" key={profile.id} onClick={() => changeProfile(profile.id)}>
                      <span className="block font-semibold text-slate-950">{profile.title}</span>
                      <span className="text-slate-600">{label(profile.provider_family)} · {label(profile.input_format)}</span>
                      <span className="mt-1 block text-xs text-slate-500">{profile.default_for_provider_family ? "Default profile" : "Profile"} · {profile.active ? "active" : "inactive"}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <EmptyState title="No parser profiles" body="Seed defaults to create governed parser profile records." />
              )}
            </div>

            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">{selectedProfile?.title || "Parser versions"}</h3>
                <p className="mt-1 text-sm text-slate-600">Active version: {activeVersion?.version_label || "none"}</p>
                <div className="mt-4 overflow-hidden rounded-md border border-slate-200">
                  <div className="grid grid-cols-[1fr_100px_160px_120px] gap-3 bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <span>Version</span><span>Status</span><span>Limitations</span><span>Action</span>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {(state?.versions || []).map((version) => (
                      <div className="grid grid-cols-[1fr_100px_160px_120px] gap-3 px-3 py-3 text-sm" key={version.id}>
                        <span><span className="block font-semibold text-slate-950">{version.version_label}</span><span className="text-slate-500">{version.change_notes || "No notes"}</span></span>
                        <span>{label(version.status)}</span>
                        <span>{version.known_limitations_json?.length || 0}</span>
                        <span>{version.status === "active" ? "Active" : <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => activateVersion(version.id)} disabled={working === version.id}>Activate</button>}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-[220px_1fr_auto]" onSubmit={createVersion}>
                <Field label="Draft version label" value={versionForm.version_label} onChange={(value) => setVersionForm({ ...versionForm, version_label: value })} required />
                <Field label="Change notes" value={versionForm.change_notes} onChange={(value) => setVersionForm({ ...versionForm, change_notes: value })} />
                <button className="aa-primary-action self-end rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "version" || !versionForm.version_label || !selectedProfileId}>{working === "version" ? "Creating..." : "Create draft version"}</button>
              </form>
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="font-semibold text-slate-950">Training samples</h3>
            </div>
            {state?.samples?.length ? (
              <div className="divide-y divide-slate-100">
                {state.samples.map((sample) => (
                  <div className="grid gap-3 p-4 text-sm lg:grid-cols-[1.3fr_120px_120px_120px_220px]" key={sample.id}>
                    <span><span className="block font-semibold text-slate-950">{sample.sample_title || "Untitled sample"}</span><span className="text-slate-500">{label(sample.provider_family)} · {label(sample.input_format)}</span></span>
                    <span>{label(sample.scope)}</span>
                    <span>{label(sample.difficulty)}</span>
                    <span>{label(sample.sample_status)}</span>
                    <span className="flex flex-wrap gap-2">
                      <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => reviewSample(sample.id, "approved")}>Approve</button>
                      <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => reviewSample(sample.id, "rejected")}>Reject</button>
                      <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => reviewSample(sample.id, "promoted")}>Promote</button>
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No training samples" body="Agency parser runs can be submitted as governed samples for platform review." />
            )}
          </section>

          <section className="grid gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
            <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createEvaluation}>
              <h3 className="font-semibold text-slate-950">Create evaluation</h3>
              <Select label="Parser version" value={evaluationForm.parser_version_id} options={[["", "Select version"], ...(state?.versions || []).map((version) => [version.id, `${version.version_label} (${label(version.status)})`])]} onChange={(value) => setEvaluationForm({ ...evaluationForm, parser_version_id: value })} />
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "evaluation" || !evaluationForm.parser_version_id}>{working === "evaluation" ? "Evaluating..." : "Run evaluation"}</button>
            </form>

            <section className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-100 px-5 py-4">
                <h3 className="font-semibold text-slate-950">Evaluation runs</h3>
              </div>
              {state?.evaluations?.length ? (
                <div className="divide-y divide-slate-100">
                  {state.evaluations.map((item) => (
                    <div className="grid gap-3 p-4 text-sm md:grid-cols-[1fr_100px_120px_120px_120px]" key={item.id}>
                      <span>{item.created_at ? new Date(item.created_at).toLocaleString() : item.id}</span>
                      <span>{label(item.evaluation_status)}</span>
                      <span>{item.sample_count || 0} samples</span>
                      <span>{item.exact_match_count || 0} exact</span>
                      <span>{formatConfidence(item.average_confidence)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No evaluations" body="Run an evaluation against approved/promoted samples." />
              )}
            </section>
          </section>

          <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced profile/version JSON</summary>
            <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify({ selectedProfile, versions: state?.versions || [] }, null, 2)}</pre>
          </details>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Field({ label: fieldLabel, value, onChange, required = false }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} required={required} />
    </label>
  )
}

function Select({ label: fieldLabel, value, options, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => <option value={optionValue} key={optionValue}>{optionLabel}</option>)}
      </select>
    </label>
  )
}

function Metric({ label: metricLabel, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metricLabel}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function formatConfidence(value) {
  if (value === null || value === undefined || value === "") return "not set"
  const number = Number(value)
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : String(value)
}

function label(value) {
  return String(value || "not set").replaceAll("_", " ")
}
