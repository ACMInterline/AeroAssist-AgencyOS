import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  audit_review_id: "",
  title: "Offer decision export governance record",
  rule_name: "Governance review rule",
  retention_policy_name: "Decision export retention policy",
  basis_label: "Contract and agency policy basis",
  exception_title: "Governance exception metadata",
}

export default function OfferDecisionExportGovernancePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [selectedRecordId, setSelectedRecordId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextRecordId = selectedRecordId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-export-governance`
    const auditBase = `/api/agencies/${context.agency.id}/offer-decision-export-audit-reviews`
    const [summary, recordsResult, reviewsResult] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/governance-records`),
      apiGet(`${auditBase}/reviews`),
    ])
    const records = recordsResult.items || []
    const chosenRecordId = nextRecordId || records[0]?.id || ""
    const detail = chosenRecordId ? await apiGet(`${base}/governance-records/${chosenRecordId}`) : null
    setSelectedRecordId(chosenRecordId)
    setState({
      ...context,
      base,
      summary,
      records,
      auditReviews: reviewsResult.items || [],
      detail,
    })
    const firstReview = reviewsResult.items?.[0]
    setForm((current) => ({ ...current, audit_review_id: current.audit_review_id || firstReview?.id || "" }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedRecord = state?.detail?.governance_record || state?.records?.find((item) => item.id === selectedRecordId)
  const firstException = state?.detail?.governance_exceptions?.find((item) => item.exception_status === "open")
  const metrics = useMemo(() => [
    ["Records", state?.summary?.governance_record_count],
    ["Rules", state?.summary?.rule_count],
    ["Retention", state?.summary?.retention_policy_count],
    ["Legal Bases", state?.summary?.legal_basis_count],
    ["Archives", state?.summary?.archive_status_count],
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

  function createRecord(event) {
    event.preventDefault()
    runAction("record", async () => {
      const result = await apiPost(`${state.base}/governance-records`, {
        audit_review_id: form.audit_review_id || null,
        title: form.title || null,
        governance_scope: "audit_review",
        policy_summary_json: { source: "agency_governance_page" },
      })
      setMessage("Governance record metadata created.")
      await load(result.governance_record.id)
    })
  }

  function activateRecord() {
    if (!selectedRecordId) return
    runAction("status", async () => {
      await apiPatch(`${state.base}/governance-records/${selectedRecordId}`, {
        governance_status: "active",
        status_reason: "Human governance metadata review recorded.",
      })
      setMessage("Governance status metadata recorded.")
      await load(selectedRecordId)
    })
  }

  function addRule() {
    if (!selectedRecordId) return
    runAction("rule", async () => {
      await apiPost(`${state.base}/governance-records/${selectedRecordId}/rules`, {
        rule_type: "retention",
        rule_status: "active",
        rule_name: form.rule_name,
        rule_text: "Human-reviewed governance metadata rule. No execution is attached.",
      })
      setMessage("Governance rule metadata added.")
      await load(selectedRecordId)
    })
  }

  function addRetentionPolicy() {
    if (!selectedRecordId) return
    runAction("retention", async () => {
      await apiPost(`${state.base}/governance-records/${selectedRecordId}/retention-policies`, {
        policy_name: form.retention_policy_name,
        retention_period_days: 365,
        retention_action: "review",
        review_required: true,
        notes: "Retention policy metadata only.",
      })
      setMessage("Retention policy metadata added.")
      await load(selectedRecordId)
    })
  }

  function addLegalBasis() {
    if (!selectedRecordId) return
    runAction("legal", async () => {
      await apiPost(`${state.base}/governance-records/${selectedRecordId}/legal-bases`, {
        basis_type: "contract",
        basis_label: form.basis_label,
        notes: "Legal basis metadata only.",
        evidence_reference_metadata: "Internal reference only.",
      })
      setMessage("Legal basis metadata added.")
      await load(selectedRecordId)
    })
  }

  function addArchiveStatus() {
    if (!selectedRecordId) return
    runAction("archive", async () => {
      await apiPost(`${state.base}/governance-records/${selectedRecordId}/archive-statuses`, {
        archive_status: "eligible_for_metadata_archive",
        status_reason: "Human archive status metadata recorded.",
        archive_reference_metadata: "No real archive job created.",
      })
      setMessage("Archive status metadata added.")
      await load(selectedRecordId)
    })
  }

  function addException() {
    if (!selectedRecordId) return
    runAction("exception", async () => {
      await apiPost(`${state.base}/governance-records/${selectedRecordId}/governance-exceptions`, {
        exception_type: "policy_override",
        severity: "medium",
        title: form.exception_title,
        description: "Human-entered governance exception metadata only.",
      })
      setMessage("Governance exception metadata added.")
      await load(selectedRecordId)
    })
  }

  function resolveException() {
    if (!firstException) return
    runAction("resolve", async () => {
      await apiPatch(`${state.base}/governance-exceptions/${firstException.id}`, {
        exception_status: "resolved",
        resolution_notes: "Human-recorded governance resolution metadata.",
      })
      setMessage("Governance exception resolution metadata recorded.")
      await load(selectedRecordId)
    })
  }

  function createSnapshot() {
    if (!selectedRecordId) return
    runAction("snapshot", async () => {
      await apiPost(`${state.base}/governance-records/${selectedRecordId}/snapshots`, {
        snapshot_type: "policy_review",
      })
      setMessage("Immutable governance snapshot created.")
      await load(selectedRecordId)
    })
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Export Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Governance Foundation</h2>
              <p className="mt-1 text-sm text-slate-600">Track retention, legal basis, archive status, exceptions, and snapshots as governance metadata only.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Governance only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4 xl:grid-cols-7">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[410px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createRecord}>
                <h3 className="font-semibold text-slate-950">Create governance record</h3>
                <Select label="Audit review" value={form.audit_review_id} onChange={(value) => setForm({ ...form, audit_review_id: value })} options={(state?.auditReviews || []).map((item) => [item.id, `${item.title || item.id} / ${item.review_status}`])} />
                <Field label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "record"}>{working === "record" ? "Creating..." : "Create governance metadata"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Governance records</h3>
                <Select label="Governance record" value={selectedRecordId} onChange={(value) => load(value).catch((err) => setError(err.message))} options={(state?.records || []).map((item) => [item.id, `${item.title || item.id} / ${item.governance_status}`])} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={activateRecord} disabled={!selectedRecordId || working === "status"}>Record active governance status</button>
              </div>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Governance metadata</h3>
                <Field label="Rule name" value={form.rule_name} onChange={(value) => setForm({ ...form, rule_name: value })} />
                <Field label="Retention policy" value={form.retention_policy_name} onChange={(value) => setForm({ ...form, retention_policy_name: value })} />
                <Field label="Legal basis" value={form.basis_label} onChange={(value) => setForm({ ...form, basis_label: value })} />
                <Field label="Exception title" value={form.exception_title} onChange={(value) => setForm({ ...form, exception_title: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={addRule} disabled={!selectedRecordId || working === "rule"}>Add rule</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={addRetentionPolicy} disabled={!selectedRecordId || working === "retention"}>Add retention</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={addLegalBasis} disabled={!selectedRecordId || working === "legal"}>Add legal basis</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={addArchiveStatus} disabled={!selectedRecordId || working === "archive"}>Add archive status</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={addException} disabled={!selectedRecordId || working === "exception"}>Add exception</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={resolveException} disabled={!firstException || working === "resolve"}>Resolve exception</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={createSnapshot} disabled={!selectedRecordId || working === "snapshot"}>Create immutable snapshot</button>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <RecordSummary record={selectedRecord} />
              <SimpleList title="Rules" items={state?.detail?.rules || []} fields={["rule_type", "rule_status", "rule_name", "created_at"]} />
              <SimpleList title="Retention policies" items={state?.detail?.retention_policies || []} fields={["policy_name", "retention_period_days", "retention_action", "review_required"]} />
              <SimpleList title="Legal bases" items={state?.detail?.legal_bases || []} fields={["basis_type", "basis_label", "evidence_reference_metadata", "created_at"]} />
              <SimpleList title="Archive statuses" items={state?.detail?.archive_statuses || []} fields={["archive_status", "status_reason", "reviewed_by", "reviewed_at"]} />
              <SimpleList title="Exceptions" items={state?.detail?.governance_exceptions || []} fields={["exception_type", "severity", "exception_status", "title"]} />
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

function RecordSummary({ record }) {
  if (!record) return <EmptyState title="No governance record selected" body="Create governance metadata from an offer decision export audit review." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{record.title || record.id}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-4">
        <Summary label="Status" value={record.governance_status} />
        <Summary label="Rules" value={record.rule_count ?? 0} />
        <Summary label="Exceptions" value={record.exception_count ?? 0} />
        <Summary label="Snapshots" value={record.snapshot_count ?? 0} />
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
