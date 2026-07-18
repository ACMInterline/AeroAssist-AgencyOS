import { useEffect, useMemo, useState } from "react"
import AlertTriangle from "lucide-react/dist/esm/icons/alert-triangle.js"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import Database from "lucide-react/dist/esm/icons/database.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import Users from "lucide-react/dist/esm/icons/users.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const statusClasses = {
  PASS: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  WARNING: "bg-amber-50 text-amber-800 ring-amber-200",
  BLOCKED: "bg-red-50 text-red-700 ring-red-200",
  APPROVED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  APPROVED_WITH_CONDITIONS: "bg-amber-50 text-amber-800 ring-amber-200",
  NOT_SIGNED_OFF: "bg-slate-100 text-slate-700 ring-slate-200",
}

export default function PilotOperationsReadinessPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [agencyId, setAgencyId] = useState("")
  const [actionReason, setActionReason] = useState("")
  const [datasetReference, setDatasetReference] = useState("PILOT_TEST_")
  const [datasetCount, setDatasetCount] = useState(5)

  async function load() {
    const [me, agencies, dashboard, diagnostics] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet("/api/platform/pilot-operations"),
      apiGet("/api/platform/pilot-operations/production-diagnostics"),
    ])
    setState({ me, agencies: agencies.items || [], dashboard, diagnostics })
    if (!agencyId && agencies.items?.length) setAgencyId(agencies.items[0].id)
    setError("")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const isOwner = state?.me?.user?.global_role === "platform_owner"
  const overview = state?.dashboard?.overview || {}
  const enrollments = state?.dashboard?.pilot_agencies || []
  const activeEnrollment = useMemo(
    () => enrollments.find((item) => item.agency_id === agencyId && ["enabled", "activated"].includes(item.enrollment_status)),
    [enrollments, agencyId],
  )

  async function mutate(path, payload) {
    setBusy(true)
    setError("")
    try {
      await apiPost(path, payload)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function changeEnrollment(item, action) {
    if (!actionReason.trim()) {
      setError("Enter an action reason before changing pilot status.")
      return
    }
    mutate(`/api/platform/pilot-operations/pilot-agencies/${item.id}/${action}`, { reason: actionReason.trim() })
  }

  const overviewCards = [
    ["Deployment phase", overview.deployment_phase || "Unknown"],
    ["Health", overview.health || "WARNING"],
    ["Readiness", overview.readiness || "WARNING"],
    ["Backups", overview.backup_status || "WARNING"],
    ["Smoke", overview.smoke_status || "WARNING"],
    ["CI", overview.ci_status || "WARNING"],
    ["Pilot approval", overview.pilot_approval_state || "NOT_SIGNED_OFF"],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-7">
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase text-blue-700">Release Operations</p>
              <h1 className="mt-2 text-2xl font-semibold text-slate-950">Pilot Operations & Release Readiness</h1>
              <p className="mt-1 max-w-4xl text-sm text-slate-600">Human-governed pilot evidence, release assessment, agency enrollment, isolated synthetic datasets, health history, and protected diagnostics. This console does not approve releases, migrate production, call providers, process payments, or execute ticketing.</p>
            </div>
            <button className="icon-button" type="button" title="Refresh pilot readiness" onClick={() => load().catch((err) => setError(err.message))}><RefreshCw className="h-4 w-4" /></button>
          </header>

          {error ? <div className="border-y border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {overviewCards.map(([label, value]) => <OverviewCard key={label} label={label} value={value} />)}
          </section>

          <section>
            <SectionHeading icon={ShieldCheck} title="Release assessment" detail="PASS, WARNING, and BLOCKED are deterministic recommendations. Human sign-off remains separate." />
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {(state?.dashboard?.assessment_groups || []).map((group) => (
                <div className="rounded-md border border-slate-200 bg-white p-4" key={group.category}>
                  <div className="flex items-start justify-between gap-3"><h3 className="font-semibold capitalize text-slate-950">{group.category.replaceAll("_", " ")}</h3><StatusBadge status={group.status} /></div>
                  <div className="mt-3 space-y-2 text-xs text-slate-600">{group.items.map((item) => <div className="flex items-start justify-between gap-2 border-t border-slate-100 pt-2" key={item.key}><span>{item.key.replaceAll("_", " ")}</span><StatusBadge status={item.display_status} compact /></div>)}</div>
                </div>
              ))}
            </div>
          </section>

          <section>
            <SectionHeading icon={Database} title="Operational evidence registry" detail="Immutable operator evidence and sign-offs. Conflicting or superseding evidence is retained." />
            <DataTable headers={["Type", "Title", "Status", "Reference", "Occurred"]} rows={(state?.dashboard?.evidence || []).map((item) => [format(item.evidence_type), item.title, <StatusBadge status={item.status} />, item.reference, dateTime(item.occurred_at)])} empty="No operational evidence recorded." />
          </section>

          <section>
            <SectionHeading icon={Users} title="Pilot agency management" detail="Platform Owner controls enrollment. Invitation records do not send email or alter agency entitlements." />
            {isOwner ? (
              <div className="mt-3 grid gap-3 border-y border-slate-200 bg-white py-4 md:grid-cols-[1fr_2fr_auto]">
                <label className="text-sm font-medium text-slate-700">Agency<select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={agencyId} onChange={(event) => setAgencyId(event.target.value)}>{(state?.agencies || []).map((agency) => <option value={agency.id} key={agency.id}>{agency.name}</option>)}</select></label>
                <label className="text-sm font-medium text-slate-700">Action reason<input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={actionReason} onChange={(event) => setActionReason(event.target.value)} placeholder="Required for audit history" /></label>
                <button className="self-end rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300" type="button" disabled={busy || !agencyId || !actionReason.trim()} onClick={() => mutate("/api/platform/pilot-operations/pilot-agencies/invitations", { agency_id: agencyId, reason: actionReason.trim() })}>Invite</button>
              </div>
            ) : null}
            <div className="mt-3 space-y-2">{enrollments.length ? enrollments.map((item) => <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-3 py-3" key={item.id}><div><p className="font-semibold text-slate-950">{item.agency_name}</p><p className="text-xs text-slate-500">{format(item.enrollment_status)} · invited {dateTime(item.invited_at)}</p></div>{isOwner ? <div className="flex gap-2"><ActionButton label="Enable" disabled={busy || !actionReason.trim()} onClick={() => changeEnrollment(item, "enable")} /><ActionButton label="Activate" disabled={busy || !actionReason.trim()} onClick={() => changeEnrollment(item, "activate")} /><ActionButton label="Disable" disabled={busy || !actionReason.trim()} onClick={() => changeEnrollment(item, "disable")} /></div> : null}</div>) : <EmptyLine text="No pilot agencies enrolled." />}</div>
          </section>

          <section>
            <SectionHeading icon={Database} title="Synthetic data manager" detail="Creates isolated, prefixed metadata fixtures only. Removal clears fixture contents and preserves audit history." />
            {isOwner ? <div className="mt-3 grid gap-3 border-y border-slate-200 bg-white py-4 md:grid-cols-[1fr_120px_auto]"><label className="text-sm font-medium text-slate-700">Dataset reference<input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={datasetReference} onChange={(event) => setDatasetReference(event.target.value)} /></label><label className="text-sm font-medium text-slate-700">Records<input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" type="number" min="1" max="50" value={datasetCount} onChange={(event) => setDatasetCount(Number(event.target.value))} /></label><button className="self-end rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300" type="button" disabled={busy || !activeEnrollment || !datasetReference.startsWith("PILOT_TEST_")} onClick={() => mutate("/api/platform/pilot-operations/synthetic-datasets", { agency_id: agencyId, dataset_reference: datasetReference, dataset_type: "operational_readiness", record_count: datasetCount, notes: actionReason })}>Create dataset</button></div> : null}
            <DataTable headers={["Reference", "Agency", "Status", "Records", "Created", "Action"]} rows={(state?.dashboard?.synthetic_datasets || []).map((item) => [item.dataset_reference, item.agency_id, format(item.dataset_status), item.record_count, dateTime(item.created_at), isOwner ? <ActionButton label="Remove" disabled={busy || !actionReason.trim()} onClick={() => mutate(`/api/platform/pilot-operations/synthetic-datasets/${item.id}/remove`, { reason: actionReason.trim() })} /> : "Read only"])} empty="No active synthetic pilot datasets." />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <div><SectionHeading icon={CheckCircle2} title="Health timeline" detail="Newest recorded deployment, health, readiness, smoke, backup, restore, incident, and pilot events." /><div className="mt-3 space-y-2">{(state?.dashboard?.health_timeline || []).length ? state.dashboard.health_timeline.slice(0, 12).map((item) => <div className="border-l-2 border-blue-300 bg-white px-4 py-3" key={item.id}><div className="flex justify-between gap-3"><p className="font-semibold text-slate-950">{item.title}</p><StatusBadge status={item.status} compact /></div><p className="mt-1 text-sm text-slate-600">{item.summary}</p><p className="mt-2 text-xs text-slate-500">{format(item.event_type)} · {dateTime(item.occurred_at)}</p></div>) : <EmptyLine text="No health timeline events." />}</div></div>
            <div><SectionHeading icon={AlertTriangle} title="Protected diagnostics" detail="Bounded process telemetry, query summaries, and audit metadata. Raw logs and sensitive values are not exposed." /><Diagnostics value={state?.diagnostics || {}} /></div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function OverviewCard({ label, value }) {
  const normalized = String(value)
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><div className="mt-2">{statusClasses[normalized] ? <StatusBadge status={normalized} /> : <p className="break-words text-sm font-semibold text-slate-950">{normalized}</p>}</div></div>
}

function StatusBadge({ status, compact = false }) {
  const value = String(status || "WARNING").toUpperCase()
  return <span className={`inline-flex rounded-full font-semibold ring-1 ${compact ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs"} ${statusClasses[value] || "bg-slate-100 text-slate-700 ring-slate-200"}`}>{value.replaceAll("_", " ")}</span>
}

function SectionHeading({ icon: Icon, title, detail }) {
  return <div className="flex items-start gap-3"><Icon className="mt-0.5 h-5 w-5 shrink-0 text-blue-700" /><div><h2 className="text-lg font-semibold text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-600">{detail}</p></div></div>
}

function DataTable({ headers, rows, empty }) {
  if (!rows.length) return <div className="mt-3 border-y border-slate-200 bg-white px-4 py-6 text-sm text-slate-500">{empty}</div>
  return <div className="mt-3 overflow-x-auto border-y border-slate-200 bg-white"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-xs uppercase text-slate-500"><tr>{headers.map((header) => <th className="px-3 py-3" key={header}>{header}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{rows.map((row, index) => <tr key={index}>{row.map((value, column) => <td className="max-w-xs px-3 py-3 align-top" key={column}>{value}</td>)}</tr>)}</tbody></table></div>
}

function Diagnostics({ value }) {
  const telemetry = value.telemetry_summary || {}
  const requests = value.request_statistics || {}
  return <div className="mt-3 grid gap-3 sm:grid-cols-2"><Diagnostic label="Process telemetry" value={{ process_local: telemetry.process_local, durable: telemetry.durable, reset_on_restart: telemetry.reset_on_restart, uptime_seconds: telemetry.uptime_seconds }} /><Diagnostic label="Request statistics" value={requests} /><Diagnostic label="Slow queries" value={value.slow_query_summary || {}} /><Diagnostic label="Bounded audit log" value={{ records: value.bounded_logs?.length || 0, raw_logs_exposed: value.raw_logs_exposed, sensitive_values_exposed: value.sensitive_values_exposed }} /></div>
}

function Diagnostic({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="font-semibold text-slate-950">{label}</p><pre className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap break-words text-xs text-slate-600">{JSON.stringify(value, null, 2)}</pre></div>
}

function ActionButton({ label, disabled, onClick }) {
  return <button className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:text-slate-300" type="button" disabled={disabled} onClick={onClick}>{label}</button>
}

function EmptyLine({ text }) {
  return <div className="border-y border-slate-200 bg-white px-4 py-6 text-sm text-slate-500">{text}</div>
}

function format(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function dateTime(value) {
  return value ? new Date(value).toLocaleString() : "Not recorded"
}
