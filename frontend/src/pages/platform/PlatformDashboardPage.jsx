import { useEffect, useMemo, useState } from "react"
import Activity from "lucide-react/dist/esm/icons/activity.js"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import Building2 from "lucide-react/dist/esm/icons/building-2.js"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import CircleAlert from "lucide-react/dist/esm/icons/circle-alert.js"
import MessageSquareText from "lucide-react/dist/esm/icons/message-square-text.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import WorkspacePage from "../../components/WorkspacePage"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"
import { productLabel } from "../../lib/productLanguage"

export default function PlatformDashboardPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const summary = await apiGet("/api/platform/summary")
    const [knowledge, pilot, feedback, readiness] = await Promise.all([
      optionalGet("/api/platform/airline-intelligence-readiness/summary"),
      optionalGet("/api/platform/commercial-pilot-readiness"),
      optionalGet("/api/platform/pilot-feedback?status=submitted"),
      optionalGet("/api/readiness"),
    ])
    setState({ summary, knowledge, pilot, feedback, readiness })
    setError("")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const attention = useMemo(() => buildAttentionItems(state), [state])
  const overview = state?.summary?.product_overview || {}
  const knowledgeSummary = state?.knowledge?.summary || {}
  const pilot = state?.pilot || {}
  const readiness = state?.readiness || {}
  const feedbackCount = state?.feedback?.items?.length || 0

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <WorkspacePage as="main" variant="wide" className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Platform" }, { label: "Overview" }]}
            eyebrow="Today"
            title="Platform overview"
            description="Agency operations, airline knowledge, pilot readiness, and system health in one practical view."
            status={<StatusBadge label={attention.length ? `${attention.length} need attention` : "No urgent issues"} status={attention.length ? "warning" : "ready"} />}
            actions={<button className="icon-button" type="button" onClick={() => load().catch((err) => setError(err.message))} title="Refresh overview" aria-label="Refresh overview"><RefreshCw className="h-4 w-4" /></button>}
          />

          <section aria-labelledby="attention-heading">
            <div className="flex items-center gap-2">
              <CircleAlert className="h-5 w-5 text-amber-600" aria-hidden="true" />
              <h2 className="text-base font-semibold text-slate-950" id="attention-heading">Attention required</h2>
            </div>
            {attention.length ? (
              <div className="mt-3 divide-y divide-slate-200 border-y border-slate-200 bg-white">
                {attention.map((item) => (
                  <a className="flex items-start justify-between gap-4 px-4 py-4 hover:bg-slate-50" href={item.href} key={item.title}>
                    <div><p className="text-sm font-semibold text-slate-950">{item.title}</p><p className="mt-1 text-sm text-slate-600">{item.body}</p></div>
                    <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
                  </a>
                ))}
              </div>
            ) : (
              <div className="mt-3 flex items-center gap-3 border-y border-emerald-200 bg-emerald-50 px-4 py-4 text-sm text-emerald-800">
                <CheckCircle2 className="h-5 w-5 shrink-0" aria-hidden="true" />
                No urgent onboarding, pilot, knowledge, feedback, or system-health issues are currently visible.
              </div>
            )}
          </section>

          <section className="grid gap-4 xl:grid-cols-4">
            <OverviewCard icon={Building2} title="Agencies" href="/platform/agencies" status={overview.onboarding_attention_count ? "warning" : "ready"}>
              <Metric label="Total agencies" value={overview.agency_count ?? state?.summary?.counts?.agencies ?? 0} />
              <Metric label="Onboarding attention" value={overview.onboarding_attention_count ?? 0} />
              <Metric label="Open requests" value={overview.open_operational_request_count ?? 0} />
            </OverviewCard>
            <OverviewCard icon={Plane} title="Knowledge readiness" href="/platform/airline-intelligence-readiness" status={knowledgeSummary.blocked_gate_count ? "blocked" : knowledgeSummary.release_ready_count ? "ready" : "warning"}>
              <Metric label="Average readiness" value={formatScore(knowledgeSummary.average_readiness_score)} />
              <Metric label="Release ready" value={knowledgeSummary.release_ready_count ?? 0} />
              <Metric label="Blocked gates" value={knowledgeSummary.blocked_gate_count ?? 0} />
            </OverviewCard>
            <OverviewCard icon={ShieldCheck} title="Pilot status" href="/platform/commercial-pilot-readiness" status={pilot.status || "not_verified"}>
              <Metric label="Current status" value={productLabel(pilot.status || "not verified")} />
              <Metric label="Blocking checks" value={pilot.blocker_count ?? "—"} />
              <Metric label="New feedback" value={feedbackCount} />
            </OverviewCard>
            <OverviewCard icon={Activity} title="System health" href="/platform/pilot-operations" status={readiness.ok ? "ready" : "blocked"}>
              <Metric label="API readiness" value={readiness.ok ? "Ready" : "Needs attention"} />
              <Metric label="Configuration" value={productLabel(readiness.diagnostics?.configuration || "unknown")} />
              <Metric label="Smoke inventory" value={inventoryLabel(readiness.inventory)} />
            </OverviewCard>
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.6fr)]">
            <div>
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-700" aria-hidden="true" />
                <h2 className="text-base font-semibold text-slate-950">Recent activity</h2>
              </div>
              {(overview.recent_activity || []).length ? (
                <div className="mt-3 divide-y divide-slate-200 border-y border-slate-200 bg-white">
                  {overview.recent_activity.map((item, index) => (
                    <div className="px-4 py-3" key={`${item.event_type}-${item.created_at}-${index}`}>
                      <p className="text-sm font-semibold text-slate-900">{item.summary || productLabel(item.event_type)}</p>
                      <p className="mt-1 text-xs text-slate-500">{formatDateTime(item.created_at)}</p>
                    </div>
                  ))}
                </div>
              ) : <p className="mt-3 border-y border-slate-200 bg-white px-4 py-5 text-sm text-slate-600">Recent platform activity will appear here as governed actions are recorded.</p>}
            </div>

            <div>
              <div className="flex items-center gap-2">
                <MessageSquareText className="h-5 w-5 text-blue-700" aria-hidden="true" />
                <h2 className="text-base font-semibold text-slate-950">Quick actions</h2>
              </div>
              <div className="mt-3 grid gap-2">
                <QuickAction href="/platform/agencies" label="Review agency onboarding" />
                <QuickAction href="/platform/airline-service-coverage" label="Review knowledge gaps" />
                <QuickAction href="/platform/pilot-feedback" label="Review pilot feedback" />
                <QuickAction href="/platform/pilot-operations" label="Open health and release evidence" />
              </div>
            </div>
          </section>
        </WorkspacePage>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

async function optionalGet(path) {
  try {
    return await apiGet(path)
  } catch {
    return null
  }
}

function buildAttentionItems(state) {
  if (!state) return []
  const items = []
  const overview = state.summary?.product_overview || {}
  const knowledge = state.knowledge?.summary || {}
  if (overview.onboarding_attention_count) {
    items.push({ title: "Agency onboarding needs attention", body: `${overview.onboarding_attention_count} agency workspace${overview.onboarding_attention_count === 1 ? "" : "s"} have not completed setup.`, href: "/platform/agencies" })
  }
  if (knowledge.blocked_gate_count) {
    items.push({ title: "Airline knowledge has blocked release gates", body: `${knowledge.blocked_gate_count} knowledge gate${knowledge.blocked_gate_count === 1 ? "" : "s"} require review.`, href: "/platform/airline-intelligence-readiness" })
  }
  if ((state.pilot?.blocker_count || 0) > 0 || state.pilot?.status === "blocked") {
    items.push({ title: "Commercial Pilot is blocked", body: `${state.pilot?.blocker_count || 0} blocking check${state.pilot?.blocker_count === 1 ? "" : "s"} remain.`, href: "/platform/commercial-pilot-readiness" })
  }
  const feedbackCount = state.feedback?.items?.length || 0
  if (feedbackCount) {
    items.push({ title: "New pilot feedback", body: `${feedbackCount} submission${feedbackCount === 1 ? "" : "s"} await review.`, href: "/platform/pilot-feedback" })
  }
  if (state.readiness && !state.readiness.ok) {
    items.push({ title: "System readiness needs attention", body: "Configuration or database readiness is not currently passing.", href: "/platform/pilot-operations" })
  }
  return items
}

function OverviewCard({ children, href, icon: Icon, status, title }) {
  return (
    <article className="border-t-2 border-blue-700 bg-white px-4 py-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2"><Icon className="h-5 w-5 text-blue-700" aria-hidden="true" /><h2 className="text-sm font-semibold text-slate-950">{title}</h2></div>
        <StatusBadge status={status} />
      </div>
      <dl className="mt-4 grid gap-2">{children}</dl>
      <a className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-blue-700" href={href}>Open <ArrowRight className="h-4 w-4" aria-hidden="true" /></a>
    </article>
  )
}

function Metric({ label, value }) {
  return <div className="flex items-baseline justify-between gap-3 border-b border-slate-100 py-1.5"><dt className="text-xs text-slate-500">{label}</dt><dd className="text-sm font-semibold text-slate-900">{value}</dd></div>
}

function QuickAction({ href, label }) {
  return <a className="flex items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800 hover:bg-slate-50" href={href}>{label}<ArrowRight className="h-4 w-4 text-slate-400" aria-hidden="true" /></a>
}

function formatScore(value) {
  return value === undefined || value === null ? "Not assessed" : `${value}/100`
}

function inventoryLabel(inventory) {
  if (!inventory) return "Unavailable"
  return `${inventory.inventoried_smoke_scripts || 0}/${inventory.total_smoke_scripts || 0}`
}

function formatDateTime(value) {
  if (!value) return "Time unavailable"
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? String(value) : date.toLocaleString()
}
