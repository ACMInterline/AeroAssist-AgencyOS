import { useEffect, useState } from "react"
import Braces from "lucide-react/dist/esm/icons/braces.js"
import FileWarning from "lucide-react/dist/esm/icons/file-warning.js"
import GitBranch from "lucide-react/dist/esm/icons/git-branch.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

export default function JourneyAuthoringDiagnosticsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const [me, dashboard] = await Promise.all([apiGet("/api/auth/me"), apiGet("/api/platform/journey-authoring")])
    setState({ me, dashboard })
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  const summary = state?.dashboard?.summary || {}
  const metrics = [
    ["Authoring sessions", summary.authoring_session_count || 0],
    ["Requires review", summary.requires_review_session_count || 0],
    ["Segment drafts", summary.segment_draft_count || 0],
    ["Unresolved segments", summary.unresolved_segment_count || 0],
    ["Blocking validations", summary.blocking_validation_count || 0],
    ["Applications", summary.application_count || 0],
    ["Parser linked", summary.parser_linked_session_count || 0],
    ["Booking-import linked", summary.booking_import_linked_session_count || 0],
  ]

  return <PlatformLayout user={state?.me?.user}>
    <ProtectedRoute loading={!state && !error} error={error}>
      <div className="space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm font-semibold uppercase text-blue-700">Journey Engine Governance</p><h1 className="mt-2 text-2xl font-semibold text-slate-950">Journey Authoring Diagnostics</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Read-only operational diagnostics for agency authoring sessions, preserved import sources, validations, and explicit applications into canonical Journey records.</p></div><button type="button" title="Refresh diagnostics" onClick={() => load().catch((err) => setError(err.message))} className="icon-button"><RefreshCw className="h-4 w-4" /></button></header>

        <div className="border-y border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900"><strong>Metadata-only diagnostics.</strong> Platform users cannot edit agency itinerary drafts here. The foundation does not search schedules, call providers, scrape, invoke AI, run background work, or publish Journey snapshots.</div>

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{metrics.map(([label, value]) => <div key={label} className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>)}</section>

        <section className="grid gap-6 lg:grid-cols-3"><Diagnostic icon={Braces} title="Import linkage" rows={[["Sources", summary.import_source_count], ["Parser-linked sessions", summary.parser_linked_session_count], ["Booking imports", summary.booking_import_linked_session_count]]} /><Diagnostic icon={FileWarning} title="Review pressure" rows={[["Unresolved segments", summary.unresolved_segment_count], ["Validations", summary.validation_count], ["Corrections", summary.correction_count]]} /><Diagnostic icon={GitBranch} title="Canonical application" rows={[["Confirmed segments", summary.confirmed_segment_count], ["Applications", summary.application_count], ["Average completeness", `${summary.average_completeness || 0}%`]]} /></section>

        <section className="grid gap-6 lg:grid-cols-2"><Breakdown title="Session status" values={summary.status_counts} /><Breakdown title="Source types" values={summary.source_type_counts} /></section>

        <section><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-emerald-700" /><h2 className="text-lg font-semibold text-slate-950">Governance guarantees</h2></div><div className="mt-3 grid gap-2 text-sm text-slate-700 sm:grid-cols-2">{["Raw source content is immutable", "Agent-confirmed fields are not overwritten by enrichment", "Local timestamps require explicit timezone context", "Finalized Journey snapshots cannot be mutated", "Platform diagnostics are read-only", "No automatic client publication"].map((item) => <p key={item} className="border-b border-slate-200 py-2">{item}</p>)}</div></section>
      </div>
    </ProtectedRoute>
  </PlatformLayout>
}

function Diagnostic({ icon: Icon, title, rows }) { return <section><div className="flex items-center gap-2"><Icon className="h-4 w-4 text-blue-700" /><h2 className="font-semibold text-slate-950">{title}</h2></div><dl className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{rows.map(([label, value]) => <div key={label} className="flex justify-between gap-4 py-3"><dt className="text-sm text-slate-600">{label}</dt><dd className="font-semibold text-slate-950">{value || 0}</dd></div>)}</dl></section> }
function Breakdown({ title, values = {} }) { const items = Object.entries(values); return <section><div className="flex justify-between"><h2 className="font-semibold text-slate-950">{title}</h2><span className="text-sm text-slate-500">{items.reduce((sum, [, count]) => sum + count, 0)}</span></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{items.length ? items.map(([label, value]) => <div className="flex justify-between py-3" key={label}><span className="text-sm text-slate-700">{String(label).replaceAll("_", " ")}</span><strong>{value}</strong></div>) : <p className="py-4 text-sm text-slate-500">No metadata recorded.</p>}</div></section> }
