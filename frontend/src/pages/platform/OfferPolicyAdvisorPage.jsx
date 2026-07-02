import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const base = "/api/platform/offer-policy-advisor"

export default function OfferPolicyAdvisorPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const [me, summary, contexts, rows, warnings, notes, snapshots] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/contexts`),
      apiGet(`${base}/airline-rows`),
      apiGet(`${base}/warnings`),
      apiGet(`${base}/decision-notes`),
      apiGet(`${base}/saved-snapshots`),
    ])
    setState({
      me,
      summary,
      contexts: contexts.items || [],
      rows: rows.items || [],
      warnings: warnings.items || [],
      notes: notes.items || [],
      snapshots: snapshots.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = useMemo(() => [
    ["Contexts", state?.summary?.context_count],
    ["Airline rows", state?.summary?.airline_row_count],
    ["Warnings", state?.summary?.warning_count],
    ["Decision notes", state?.summary?.decision_note_count],
    ["Snapshots", state?.summary?.saved_snapshot_count],
  ], [state])

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Policy Advisor</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Offer Advisor Governance Diagnostics</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only visibility into offer-linked policy advisor contexts, warnings, notes, and saved snapshots.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Operational execution disabled</span>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <SimpleList title="Advisor contexts" items={state?.contexts || []} fields={["agency_id", "context_name", "context_status", "offer_workspace_id"]} />
            <SimpleList title="Warnings" items={state?.warnings || []} fields={["warning_level", "airline_code", "source", "message"]} />
            <AirlineRows rows={state?.rows || []} />
            <SimpleList title="Saved snapshots" items={state?.snapshots || []} fields={["agency_id", "snapshot_name", "advisor_result_id", "created_at"]} />
            <SimpleList title="Decision notes" items={state?.notes || []} fields={["agency_id", "airline_code", "note_title", "note_status"]} />
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

function AirlineRows({ rows }) {
  if (!rows.length) return <EmptyState title="No airline rows" body="No offer-linked advisor rows found." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-2">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Offer-linked airline rows</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[980px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {["Agency", "Workspace", "Airline", "Taxonomy", "Warning", "Complexity", "Quote result", "Advisor result"].map((header) => <th className="px-3 py-2" key={header}>{header}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.slice(0, 12).map((row) => (
              <tr key={row.id}>
                <td className="px-3 py-3">{row.agency_id}</td>
                <td className="px-3 py-3">{row.offer_workspace_id}</td>
                <td className="px-3 py-3 font-semibold text-slate-950">{row.airline_code}</td>
                <td className="px-3 py-3">{[row.domain_code, row.family_code, row.variant_code].filter(Boolean).join(" / ")}</td>
                <td className="px-3 py-3">{row.warning_level}</td>
                <td className="px-3 py-3">{row.operational_complexity_score ?? 0}</td>
                <td className="px-3 py-3">{row.quote_result_id || "-"}</td>
                <td className="px-3 py-3">{row.advisor_result_id || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
