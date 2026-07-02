import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const base = "/api/platform/offer-decision-exports"

export default function OfferDecisionExportsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const [me, summary, exportsResult, artifacts, auditEvents] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/exports`),
      apiGet(`${base}/artifacts`),
      apiGet(`${base}/audit-events`),
    ])
    setState({
      me,
      summary,
      exports: exportsResult.items || [],
      artifacts: artifacts.items || [],
      auditEvents: auditEvents.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = useMemo(() => [
    ["Exports", state?.summary?.export_count],
    ["Sections", state?.summary?.section_count],
    ["Artifacts", state?.summary?.artifact_count],
    ["Recipient drafts", state?.summary?.recipient_draft_count],
    ["Audit events", state?.summary?.audit_event_count],
  ], [state])

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Exports</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Export Governance Diagnostics</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only visibility into metadata-only review exports, PDF metadata artifacts, and export audit events.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Read only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Sending disabled</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <SimpleList title="Exports" items={state?.exports || []} fields={["agency_id", "export_name", "section_count", "artifact_count"]} />
            <SimpleList title="Artifacts" items={state?.artifacts || []} fields={["agency_id", "artifact_type", "filename", "public_link_created"]} />
            <SimpleList title="Audit events" items={state?.auditEvents || []} fields={["agency_id", "event_type", "description", "created_at"]} />
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

function SafetyFlags({ summary }) {
  const flags = [
    "automatic_sending_disabled",
    "public_links_disabled",
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
