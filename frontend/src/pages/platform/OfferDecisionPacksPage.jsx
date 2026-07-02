import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const base = "/api/platform/offer-decision-packs"

export default function OfferDecisionPacksPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const [me, summary, packs, evidence, warnings, notes, snapshots] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/packs`),
      apiGet(`${base}/evidence`),
      apiGet(`${base}/warnings`),
      apiGet(`${base}/review-notes`),
      apiGet(`${base}/snapshots`),
    ])
    setState({
      me,
      summary,
      packs: packs.items || [],
      evidence: evidence.items || [],
      warnings: warnings.items || [],
      notes: notes.items || [],
      snapshots: snapshots.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = useMemo(() => [
    ["Decision packs", state?.summary?.decision_pack_count],
    ["Evidence", state?.summary?.option_evidence_count],
    ["Warnings", state?.summary?.warning_count],
    ["Review notes", state?.summary?.review_note_count],
    ["Snapshots", state?.summary?.saved_snapshot_count],
  ], [state])

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Packs</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Decision Pack Governance Diagnostics</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only visibility into offer advisor evidence consumption and human review packs.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Read only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Execution disabled</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <PacksTable packs={state?.packs || []} />
            <SimpleList title="Warnings" items={state?.warnings || []} fields={["agency_id", "warning_level", "airline_code", "message"]} />
            <SimpleList title="Evidence" items={state?.evidence || []} fields={["agency_id", "evidence_type", "airline_code", "source_record_id"]} />
            <SimpleList title="Snapshots" items={state?.snapshots || []} fields={["agency_id", "snapshot_name", "immutable", "created_at"]} />
            <SimpleList title="Review notes" items={state?.notes || []} fields={["agency_id", "airline_code", "note_title", "note_status"]} />
            <SafetyFlags summary={state?.summary || {}} />
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

function PacksTable({ packs }) {
  if (!packs.length) return <EmptyState title="No decision packs" body="No offer decision packs found." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-2">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Recent decision packs</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[960px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {["Agency", "Workspace", "Pack", "Warning", "Complexity", "Evidence", "Unresolved", "Snapshots"].map((header) => <th className="px-3 py-2" key={header}>{header}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {packs.slice(0, 12).map((pack) => (
              <tr key={pack.id}>
                <td className="px-3 py-3">{pack.agency_id}</td>
                <td className="px-3 py-3">{pack.offer_workspace_id}</td>
                <td className="px-3 py-3 font-semibold text-slate-950">{pack.pack_name}</td>
                <td className="px-3 py-3">{pack.warning_level}</td>
                <td className="px-3 py-3">{pack.operational_complexity_score ?? 0}</td>
                <td className="px-3 py-3">{pack.evidence_count ?? 0}</td>
                <td className="px-3 py-3">{pack.unresolved_warning_count ?? 0}</td>
                <td className="px-3 py-3">{pack.saved_snapshot_count ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function SafetyFlags({ summary }) {
  const flags = [
    "human_review_required",
    "auto_recommendation_disabled",
    "offer_price_mutation_disabled",
    "provider_execution_disabled",
    "booking_execution_disabled",
    "ticket_emd_issuance_disabled",
    "payment_invoice_settlement_disabled",
  ]
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Safety flags</h3>
      </div>
      <div className="grid gap-2 p-4 text-sm md:grid-cols-2">
        {flags.map((flag) => (
          <span className="rounded-md bg-slate-50 px-3 py-2 text-slate-700" key={flag}>{flag}: {summary[flag] ? "true" : "false"}</span>
        ))}
      </div>
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
        {items.slice(0, 8).map((item) => (
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
