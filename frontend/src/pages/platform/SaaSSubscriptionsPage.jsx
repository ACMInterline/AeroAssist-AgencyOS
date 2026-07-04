import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"
import { entitlementLabel, entitlementTone } from "../../lib/moduleCatalog"

const base = "/api/platform/saas-subscriptions"

const defaultPlan = {
  plan_name: "",
  plan_code: "",
  tier: "starter",
  status: "draft",
  description: "",
  included_modules: ["requests", "clients"],
  included_airline_intelligence_domains: [],
  included_data_pack_channels: [],
  visibility_flags: {
    crm: true,
    cms: false,
    client_portal: false,
    offer_builder: false,
    airline_intelligence: false,
  },
}

export default function SaaSSubscriptionsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultPlan)
  const [selectedPlanId, setSelectedPlanId] = useState("")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(openPlanId = selectedPlanId) {
    const [me, summary, plans, entitlements, assignments, readiness, notes, snapshots, agencies, entitlementVisibility] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/plans`),
      apiGet(`${base}/entitlements`),
      apiGet(`${base}/assignments`),
      apiGet(`${base}/readiness`),
      apiGet(`${base}/notes`),
      apiGet(`${base}/snapshots`),
      apiGet("/api/agencies"),
      apiGet(`${base}/entitlement-visibility`).catch(() => ({ items: [] })),
    ])
    const planItems = plans.items || []
    setSelectedPlanId(openPlanId || planItems[0]?.id || "")
    setState({
      me,
      summary,
      plans: planItems,
      entitlements: entitlements.items || [],
      assignments: assignments.items || [],
      readiness: readiness.items || [],
      notes: notes.items || [],
      snapshots: snapshots.items || [],
      agencies: agencies.items || [],
      entitlementVisibility: entitlementVisibility.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedPlan = useMemo(() => state?.plans?.find((plan) => plan.id === selectedPlanId), [state, selectedPlanId])
  const selectedEntitlements = (state?.entitlements || []).filter((item) => item.plan_id === selectedPlanId)
  const selectedAssignments = (state?.assignments || []).filter((item) => item.plan_id === selectedPlanId)
  const metrics = [
    ["Plans", state?.summary?.plan_count || 0],
    ["Entitlements", state?.summary?.entitlement_count || 0],
    ["Assignments", state?.summary?.assignment_count || 0],
    ["Readiness", state?.summary?.readiness_count || 0],
    ["Notes", state?.summary?.note_count || 0],
    ["Snapshots", state?.summary?.snapshot_count || 0],
  ]

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

  function createPlan(event) {
    event.preventDefault()
    runAction("plan", async () => {
      const result = await apiPost(`${base}/plans`, form)
      setMessage("Subscription plan metadata created.")
      setForm(defaultPlan)
      await load(result.plan.id)
    })
  }

  function createSampleEntitlement() {
    if (!selectedPlan) return
    runAction("entitlement", async () => {
      await apiPost(`${base}/entitlements`, {
        plan_id: selectedPlan.id,
        entitlement_scope: "module",
        entitlement_key: "offer_builder",
        label: "Offer builder",
        description: "Metadata-only module entitlement for offer workspace visibility.",
        visibility_flags: { offer_builder: true },
      })
      setMessage("Plan entitlement metadata added.")
      await load(selectedPlan.id)
    })
  }

  function createAssignment() {
    if (!selectedPlan || !state?.agencies?.[0]) return
    runAction("assignment", async () => {
      const result = await apiPost(`${base}/assignments`, {
        agency_id: state.agencies[0].id,
        plan_id: selectedPlan.id,
        assignment_status: "review",
        manual_review_required: true,
        visibility_flags: selectedPlan.visibility_flags || {},
      })
      await apiPost(`${base}/notes`, {
        agency_id: state.agencies[0].id,
        assignment_id: result.assignment.id,
        plan_id: selectedPlan.id,
        note_type: "agency_visible",
        note: "Subscription assignment is visible for manual review. No billing or access enforcement is active.",
        visible_to_agency: true,
      })
      setMessage("Agency assignment metadata created.")
      await load(selectedPlan.id)
    })
  }

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">SaaS & Agencies</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Subscriptions & Entitlements</h2>
              <p className="mt-1 text-sm text-slate-600">Define plan and entitlement metadata for agency visibility. Billing, payments, invoices, and automatic access enforcement are disabled.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No billing</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-950">Agency entitlement review visibility</h3>
                <p className="mt-1 text-sm text-slate-600">Owner-review metadata only. Subscription visibility is informational only and does not automatically enforce access.</p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Read-only guardrail UI</span>
            </div>
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {state?.entitlementVisibility?.length ? state.entitlementVisibility.slice(0, 6).map((item) => (
                <div className="rounded-md border border-slate-200 p-4" key={item.agency_id}>
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-slate-950">{item.agency_name || item.agency_id}</p>
                      <p className="mt-1 text-sm text-slate-600">{label(item.assignment_status)} · access enforcement disabled</p>
                    </div>
                    <Status text={item.manual_review_required ? "review required" : label(item.assignment_status)} ready={!item.manual_review_required && item.assignment_status === "active"} />
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {Object.entries(item.status_counts || {}).filter(([, count]) => count > 0).map(([status, count]) => (
                      <span className={`rounded-full px-2 py-1 text-[11px] font-semibold ring-1 ${entitlementTone(status)}`} key={status}>
                        {count} {entitlementLabel(status)}
                      </span>
                    ))}
                  </div>
                </div>
              )) : <EmptyState title="No agency entitlement visibility" body="Agency visibility summaries appear after subscription metadata exists." />}
            </div>
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 p-4">
                  <h3 className="font-semibold text-slate-950">Plans</h3>
                </div>
                {!state?.plans?.length ? <EmptyState title="No subscription plans" body="Create plan metadata before assigning agencies." /> : (
                  <div className="divide-y divide-slate-100">
                    {state.plans.map((plan) => (
                      <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedPlanId === plan.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(plan.id)} key={plan.id}>
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-semibold text-slate-950">{plan.plan_name}</p>
                            <p className="mt-1 text-sm text-slate-600">{plan.plan_code} · {label(plan.tier)}</p>
                          </div>
                          <Status text={label(plan.status)} ready={plan.status === "active"} />
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4">
                <h3 className="font-semibold text-slate-950">Create plan</h3>
                <form className="mt-4 grid gap-3" onSubmit={createPlan}>
                  <Field label="Plan name" value={form.plan_name} onChange={(value) => setForm({ ...form, plan_name: value })} />
                  <Field label="Plan code" value={form.plan_code} onChange={(value) => setForm({ ...form, plan_code: value })} />
                  <label className="grid gap-1 text-sm">
                    <span className="font-medium text-slate-700">Description</span>
                    <textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
                  </label>
                  <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={!form.plan_name || !form.plan_code || working === "plan"}>Create plan metadata</button>
                </form>
              </section>
            </div>

            <div className="space-y-4">
              {!selectedPlan ? <EmptyState title="Select a plan" body="Entitlements and assignments will appear here." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">{selectedPlan.plan_name}</h3>
                        <p className="mt-1 text-sm text-slate-600">{selectedPlan.description || "Subscription plan metadata."}</p>
                      </div>
                      <Status text={label(selectedPlan.status)} ready={selectedPlan.status === "active"} />
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createSampleEntitlement} disabled={working === "entitlement"}>Add sample entitlement</button>
                      <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createAssignment} disabled={!state?.agencies?.length || working === "assignment"}>Assign first agency for review</button>
                    </div>
                  </section>

                  <section className="grid gap-4 lg:grid-cols-2">
                    <ListPanel title="Plan entitlements" items={selectedEntitlements} emptyTitle="No entitlements" primary={(item) => item.label} secondary={(item) => `${label(item.entitlement_scope)} · ${item.entitlement_key}`} />
                    <ListPanel title="Agency assignments" items={selectedAssignments} emptyTitle="No assignments" primary={(item) => agencyName(state.agencies, item.agency_id)} secondary={(item) => `${label(item.assignment_status)} · access enforcement disabled`} />
                    <ListPanel title="Entitlement readiness" items={state.readiness} emptyTitle="No readiness rows" primary={(item) => item.entitlement_key} secondary={(item) => item.plain_language_summary || label(item.status)} />
                    <ListPanel title="Snapshots" items={state.snapshots} emptyTitle="No snapshots" primary={(item) => label(item.snapshot_type)} secondary={(item) => item.created_at} />
                  </section>
                </>
              )}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
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

function ListPanel({ title, items, emptyTitle, primary, secondary }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
      </div>
      {items?.length ? (
        <div className="divide-y divide-slate-100">
          {items.slice(0, 8).map((item) => (
            <div className="p-4 text-sm" key={item.id}>
              <p className="font-semibold text-slate-950">{primary(item)}</p>
              <p className="mt-1 text-slate-600">{secondary(item)}</p>
            </div>
          ))}
        </div>
      ) : <EmptyState title={emptyTitle} body="Metadata records will appear here when created." />}
    </section>
  )
}

function Status({ text, ready }) {
  const tone = ready ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function agencyName(agencies, agencyId) {
  return agencies?.find((agency) => agency.id === agencyId)?.name || agencyId || "Agency"
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
