import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"
import { featureFlagClass, featureFlagLabel } from "../../lib/moduleCatalog"

const base = "/api/platform/feature-flags"

const defaultForm = {
  agency_id: "",
  module_key: "requests",
  feature_key: "",
  display_name: "",
  state: "enabled",
  visibility_note: "",
}

export default function PlatformFeatureFlagsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const [me, summary, flags, reviews, snapshots, agencies] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/flags`),
      apiGet(`${base}/reviews`),
      apiGet(`${base}/snapshots`),
      apiGet("/api/agencies"),
    ])
    const agencyItems = agencies.items || []
    setState({
      me,
      summary,
      flags: flags.items || [],
      reviews: reviews.items || [],
      snapshots: snapshots.items || [],
      agencies: agencyItems,
    })
    setForm((current) => ({ ...current, agency_id: current.agency_id || agencyItems[0]?.id || "" }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

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

  function createFlag(event) {
    event.preventDefault()
    runAction("flag", async () => {
      await apiPost(`${base}/flags`, form)
      setMessage("Feature flag metadata saved.")
      setForm({ ...defaultForm, agency_id: form.agency_id })
      await load()
    })
  }

  function createReview() {
    if (!form.agency_id) return
    runAction("review", async () => {
      await apiPost(`${base}/reviews`, {
        agency_id: form.agency_id,
        notes: "Platform reviewed agency feature visibility metadata. No operational enforcement is performed.",
      })
      setMessage("Review note recorded.")
      await load()
    })
  }

  function createSnapshot() {
    if (!form.agency_id) return
    runAction("snapshot", async () => {
      await apiPost(`${base}/snapshots`, {
        agency_id: form.agency_id,
        immutable_json: {
          metadata_only: true,
          summary: "Manual feature flag visibility snapshot.",
        },
      })
      setMessage("Feature flag snapshot saved.")
      await load()
    })
  }

  const metrics = [
    ["Flags", state?.summary?.flag_count || 0],
    ["Reviews", state?.summary?.review_count || 0],
    ["Snapshots", state?.summary?.snapshot_count || 0],
    ["Agencies", state?.summary?.agency_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">SaaS & Agencies</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Flags</h2>
              <p className="mt-1 text-sm text-slate-600">Feature visibility is informational only. Operational enforcement is not performed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform review</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No enforcement</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Define feature visibility</h3>
              <form className="mt-4 grid gap-3" onSubmit={createFlag}>
                <label className="grid gap-1 text-sm">
                  <span className="font-medium text-slate-700">Agency</span>
                  <select className="rounded-md border border-slate-300 px-3 py-2" value={form.agency_id} onChange={(event) => setForm({ ...form, agency_id: event.target.value })}>
                    {(state?.agencies || []).map((agency) => <option value={agency.id} key={agency.id}>{agency.name}</option>)}
                  </select>
                </label>
                <Field label="Module key" value={form.module_key} onChange={(value) => setForm({ ...form, module_key: value })} />
                <Field label="Feature key" value={form.feature_key} onChange={(value) => setForm({ ...form, feature_key: value })} />
                <Field label="Display name" value={form.display_name} onChange={(value) => setForm({ ...form, display_name: value })} />
                <label className="grid gap-1 text-sm">
                  <span className="font-medium text-slate-700">State</span>
                  <select className="rounded-md border border-slate-300 px-3 py-2" value={form.state} onChange={(event) => setForm({ ...form, state: event.target.value })}>
                    {["enabled", "disabled", "hidden", "beta", "pilot"].map((item) => <option value={item} key={item}>{featureFlagLabel(item)}</option>)}
                  </select>
                </label>
                <label className="grid gap-1 text-sm">
                  <span className="font-medium text-slate-700">Visibility note</span>
                  <textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2" value={form.visibility_note} onChange={(event) => setForm({ ...form, visibility_note: event.target.value })} />
                </label>
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={!form.agency_id || !form.module_key || !form.feature_key || !form.display_name || working === "flag"}>Save feature metadata</button>
              </form>
              <div className="mt-3 flex flex-wrap gap-2">
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createReview} disabled={!form.agency_id || working === "review"}>Add review note</button>
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createSnapshot} disabled={!form.agency_id || working === "snapshot"}>Save snapshot</button>
              </div>
            </section>

            <div className="space-y-4">
              <ListPanel title="Feature flags" items={state?.flags} emptyTitle="No feature flags" render={(item) => <FeatureRow item={item} agencies={state?.agencies || []} />} />
              <section className="grid gap-4 lg:grid-cols-2">
                <ListPanel title="Review notes" items={state?.reviews} emptyTitle="No review notes" render={(item) => <TextRow title={agencyName(state?.agencies, item.agency_id)} body={item.notes} />} />
                <ListPanel title="Snapshots" items={state?.snapshots} emptyTitle="No snapshots" render={(item) => <TextRow title={agencyName(state?.agencies, item.agency_id)} body={item.snapshot_date} />} />
              </section>
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function FeatureRow({ item, agencies }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p className="font-semibold text-slate-950">{item.display_name}</p>
        <p className="mt-1 text-sm text-slate-600">{agencyName(agencies, item.agency_id)} · {item.module_key} · {item.feature_key}</p>
        {item.visibility_note ? <p className="mt-1 text-sm text-slate-500">{item.visibility_note}</p> : null}
      </div>
      <FlagBadge state={item.state} />
    </div>
  )
}

function TextRow({ title, body }) {
  return (
    <div>
      <p className="font-semibold text-slate-950">{title}</p>
      <p className="mt-1 text-sm text-slate-600">{body || "Metadata record"}</p>
    </div>
  )
}

function ListPanel({ title, items, emptyTitle, render }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
      </div>
      {items?.length ? (
        <div className="divide-y divide-slate-100">
          {items.slice(0, 10).map((item) => <div className="p-4" key={item.id}>{render(item)}</div>)}
        </div>
      ) : <EmptyState title={emptyTitle} body="Metadata records will appear here when created." />}
    </section>
  )
}

function Metric({ label: text, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{text}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Field({ label: text, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{text}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function FlagBadge({ state }) {
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${featureFlagClass(state)}`}>{featureFlagLabel(state)}</span>
}

function agencyName(agencies, agencyId) {
  return agencies?.find((agency) => agency.id === agencyId)?.name || agencyId || "Agency"
}
