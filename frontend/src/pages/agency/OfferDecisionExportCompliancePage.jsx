import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  governance_record_id: "",
  title: "Offer decision export compliance evidence",
  requirement_name: "Governance requirement satisfied",
  check_name: "Compliance evidence check",
  result_name: "Compliance result metadata",
  exception_title: "Compliance exception metadata",
}

export default function OfferDecisionExportCompliancePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [selectedEvidenceId, setSelectedEvidenceId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextEvidenceId = selectedEvidenceId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-export-compliance`
    const governanceBase = `/api/agencies/${context.agency.id}/offer-decision-export-governance`
    const [summary, evidenceResult, governanceResult] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/evidence`),
      apiGet(`${governanceBase}/governance-records`),
    ])
    const evidence = evidenceResult.items || []
    const chosenEvidenceId = nextEvidenceId || evidence[0]?.id || ""
    const detail = chosenEvidenceId ? await apiGet(`${base}/evidence/${chosenEvidenceId}`) : null
    setSelectedEvidenceId(chosenEvidenceId)
    setState({
      ...context,
      base,
      summary,
      evidence,
      governanceRecords: governanceResult.items || [],
      detail,
    })
    const firstRecord = governanceResult.items?.[0]
    setForm((current) => ({ ...current, governance_record_id: current.governance_record_id || firstRecord?.id || "" }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedEvidence = state?.detail?.evidence || state?.evidence?.find((item) => item.id === selectedEvidenceId)
  const firstRequirement = state?.detail?.requirements?.[0]
  const firstCheck = state?.detail?.checks?.[0]
  const firstException = state?.detail?.exceptions?.find((item) => item.exception_status === "open")
  const metrics = useMemo(() => [
    ["Evidence", state?.summary?.evidence_count],
    ["Requirements", state?.summary?.requirement_count],
    ["Checks", state?.summary?.check_count],
    ["Results", state?.summary?.result_count],
    ["Exceptions", state?.summary?.exception_count],
    ["Snapshots", state?.summary?.snapshot_count],
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

  function createEvidence(event) {
    event.preventDefault()
    runAction("evidence", async () => {
      const result = await apiPost(`${state.base}/evidence`, {
        governance_record_id: form.governance_record_id || null,
        title: form.title || null,
        evidence_scope: "governance_record",
        evidence_summary_json: { source: "agency_compliance_page" },
      })
      setMessage("Compliance evidence metadata created.")
      await load(result.evidence.id)
    })
  }

  function updateEvidenceStatus(statusValue) {
    if (!selectedEvidenceId) return
    runAction("status", async () => {
      await apiPatch(`${state.base}/evidence/${selectedEvidenceId}`, {
        evidence_status: statusValue,
        status_reason: "Human compliance metadata review recorded.",
      })
      setMessage("Compliance evidence status metadata recorded.")
      await load(selectedEvidenceId)
    })
  }

  function addRequirement() {
    if (!selectedEvidenceId) return
    runAction("requirement", async () => {
      await apiPost(`${state.base}/evidence/${selectedEvidenceId}/requirements`, {
        requirement_type: "governance_rule",
        requirement_status: "pending",
        requirement_name: form.requirement_name,
        description: "Compliance requirement metadata only.",
        source_reference_metadata: "Governance record reference metadata.",
      })
      setMessage("Compliance requirement metadata added.")
      await load(selectedEvidenceId)
    })
  }

  function satisfyRequirement() {
    if (!firstRequirement) return
    runAction("requirement-status", async () => {
      await apiPatch(`${state.base}/requirements/${firstRequirement.id}`, {
        requirement_status: "satisfied",
        description: "Requirement satisfaction metadata recorded by a human reviewer.",
      })
      setMessage("Requirement status metadata recorded.")
      await load(selectedEvidenceId)
    })
  }

  function addCheck() {
    if (!selectedEvidenceId) return
    runAction("check", async () => {
      await apiPost(`${state.base}/evidence/${selectedEvidenceId}/checks`, {
        requirement_id: firstRequirement?.id || null,
        check_type: "manual_review",
        check_status: "passed",
        check_name: form.check_name,
        check_metadata_json: { manual_review: true },
      })
      setMessage("Compliance check metadata added.")
      await load(selectedEvidenceId)
    })
  }

  function markCheckFailed() {
    if (!firstCheck) return
    runAction("check-status", async () => {
      await apiPatch(`${state.base}/checks/${firstCheck.id}`, {
        check_status: "failed",
        check_metadata_json: { failure_recorded: true },
      })
      setMessage("Failed check metadata recorded.")
      await load(selectedEvidenceId)
    })
  }

  function addResult(statusValue = "passed") {
    if (!selectedEvidenceId) return
    runAction("result", async () => {
      await apiPost(`${state.base}/evidence/${selectedEvidenceId}/results`, {
        requirement_id: firstRequirement?.id || null,
        check_id: firstCheck?.id || null,
        result_status: statusValue,
        result_name: form.result_name,
        result_summary: "Pass/fail compliance evidence metadata only.",
        evidence_reference_metadata: "Immutable evidence reference metadata.",
      })
      setMessage("Compliance result metadata added.")
      await load(selectedEvidenceId)
    })
  }

  function addException() {
    if (!selectedEvidenceId) return
    runAction("exception", async () => {
      await apiPost(`${state.base}/evidence/${selectedEvidenceId}/exceptions`, {
        requirement_id: firstRequirement?.id || null,
        check_id: firstCheck?.id || null,
        exception_type: "requirement_gap",
        severity: "medium",
        title: form.exception_title,
        description: "Human-entered compliance exception metadata only.",
      })
      setMessage("Compliance exception metadata added.")
      await load(selectedEvidenceId)
    })
  }

  function resolveException() {
    if (!firstException) return
    runAction("resolve", async () => {
      await apiPatch(`${state.base}/exceptions/${firstException.id}`, {
        exception_status: "resolved",
        resolution_notes: "Human-recorded compliance exception resolution metadata.",
      })
      setMessage("Compliance exception resolution metadata recorded.")
      await load(selectedEvidenceId)
    })
  }

  function createSnapshot() {
    if (!selectedEvidenceId) return
    runAction("snapshot", async () => {
      await apiPost(`${state.base}/evidence/${selectedEvidenceId}/snapshots`, {
        snapshot_type: "result_review",
      })
      setMessage("Immutable compliance snapshot created.")
      await load(selectedEvidenceId)
    })
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Export Compliance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Compliance Evidence Foundation</h2>
              <p className="mt-1 text-sm text-slate-600">Track evidence, requirements, checks, results, exceptions, and snapshots as compliance metadata only.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Compliance only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[410px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createEvidence}>
                <h3 className="font-semibold text-slate-950">Create compliance evidence</h3>
                <Select label="Governance record" value={form.governance_record_id} onChange={(value) => setForm({ ...form, governance_record_id: value })} options={(state?.governanceRecords || []).map((item) => [item.id, `${item.title || item.id} / ${item.governance_status}`])} />
                <Field label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "evidence"}>{working === "evidence" ? "Creating..." : "Create compliance evidence"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Evidence records</h3>
                <Select label="Compliance evidence" value={selectedEvidenceId} onChange={(value) => load(value).catch((err) => setError(err.message))} options={(state?.evidence || []).map((item) => [item.id, `${item.title || item.id} / ${item.evidence_status}`])} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={() => updateEvidenceStatus("in_review")} disabled={!selectedEvidenceId || working === "status"}>Mark in review</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={() => updateEvidenceStatus("satisfied")} disabled={!selectedEvidenceId || working === "status"}>Mark satisfied</button>
                </div>
              </div>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Compliance metadata</h3>
                <Field label="Requirement" value={form.requirement_name} onChange={(value) => setForm({ ...form, requirement_name: value })} />
                <Field label="Check" value={form.check_name} onChange={(value) => setForm({ ...form, check_name: value })} />
                <Field label="Result" value={form.result_name} onChange={(value) => setForm({ ...form, result_name: value })} />
                <Field label="Exception" value={form.exception_title} onChange={(value) => setForm({ ...form, exception_title: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={addRequirement} disabled={!selectedEvidenceId || working === "requirement"}>Add requirement</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={satisfyRequirement} disabled={!firstRequirement || working === "requirement-status"}>Satisfy requirement</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={addCheck} disabled={!selectedEvidenceId || working === "check"}>Add passed check</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={markCheckFailed} disabled={!firstCheck || working === "check-status"}>Record failed check</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={() => addResult("passed")} disabled={!selectedEvidenceId || working === "result"}>Add passed result</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={() => addResult("failed")} disabled={!selectedEvidenceId || working === "result"}>Add failed result</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={addException} disabled={!selectedEvidenceId || working === "exception"}>Add exception</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={resolveException} disabled={!firstException || working === "resolve"}>Resolve exception</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={createSnapshot} disabled={!selectedEvidenceId || working === "snapshot"}>Create immutable snapshot</button>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <EvidenceSummary evidence={selectedEvidence} />
              <SimpleList title="Requirements" items={state?.detail?.requirements || []} fields={["requirement_type", "requirement_status", "requirement_name", "required"]} />
              <SimpleList title="Checks" items={state?.detail?.checks || []} fields={["check_type", "check_status", "check_name", "performed_at"]} />
              <SimpleList title="Results" items={state?.detail?.results || []} fields={["result_status", "result_name", "evidence_reference_metadata", "evaluated_at"]} />
              <SimpleList title="Exceptions" items={state?.detail?.exceptions || []} fields={["exception_type", "severity", "exception_status", "title"]} />
              <SimpleList title="Snapshots" items={state?.detail?.snapshots || []} fields={["snapshot_type", "immutable", "created_by", "created_at"]} />
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

function Field({ label, value, onChange }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select</option>
        {options.map(([id, labelText]) => <option value={id} key={id}>{labelText}</option>)}
      </select>
    </label>
  )
}

function EvidenceSummary({ evidence }) {
  if (!evidence) return <EmptyState title="No compliance evidence selected" body="Create compliance evidence from an offer decision export governance record." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{evidence.title || evidence.id}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-4">
        <Summary label="Status" value={evidence.evidence_status} />
        <Summary label="Requirements" value={evidence.requirement_count ?? 0} />
        <Summary label="Failed Checks" value={evidence.failed_check_count ?? 0} />
        <Summary label="Snapshots" value={evidence.snapshot_count ?? 0} />
      </div>
    </div>
  )
}

function Summary({ label, value }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 truncate text-slate-800">{formatValue(value)}</p>
    </div>
  )
}

function SimpleList({ title, items, fields }) {
  if (!items.length) return <EmptyState title={`No ${title.toLowerCase()}`} body="No records found." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
        <span className="text-sm text-slate-500">{items.length}</span>
      </div>
      <div className="divide-y divide-slate-100">
        {items.slice(0, 10).map((item) => (
          <div className="grid gap-2 p-4 text-sm md:grid-cols-4" key={item.id}>
            {fields.map((field) => <span className="truncate text-slate-700" key={field}>{formatValue(item[field])}</span>)}
          </div>
        ))}
      </div>
    </div>
  )
}

function formatValue(value) {
  if (Array.isArray(value)) return value.join(", ")
  if (typeof value === "string" && value.includes("T")) return new Date(value).toLocaleString()
  if (typeof value === "boolean") return value ? "Yes" : "No"
  return value || "-"
}
