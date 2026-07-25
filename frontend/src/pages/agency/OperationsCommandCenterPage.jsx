import { useEffect, useMemo, useState } from "react"
import ConfirmationDialog from "../../components/ConfirmationDialog"
import OperationalAlert from "../../components/OperationalAlert"
import PageHeader from "../../components/PageHeader"
import PilotGuidance from "../../components/PilotGuidance"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkspacePage from "../../components/WorkspacePage"
import OperationsAlerts from "../../components/operations/OperationsAlerts"
import OperationsFilters from "../../components/operations/OperationsFilters"
import OperationsQueues from "../../components/operations/OperationsQueues"
import OperationsTimelineActivity from "../../components/operations/OperationsTimelineActivity"
import OperationsWorkList from "../../components/operations/OperationsWorkList"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const sectionOrder = ["my_work", "alerts", "queues", "timeline", "quick_actions", "recent_activity"]

export default function OperationsCommandCenterPage() {
  const [context, setContext] = useState(null)
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({})
  const [selectedDate, setSelectedDate] = useState("")
  const [error, setError] = useState("")
  const [busyAction, setBusyAction] = useState("")
  const [pendingConfirmation, setPendingConfirmation] = useState(null)

  async function load(nextFilters = filters, nextDate = selectedDate, suppliedContext = context) {
    const activeContext = suppliedContext || await loadCurrentAgency()
    if (activeContext.onboardingRedirect || !activeContext.agency) {
      setContext(activeContext)
      return
    }
    const params = new URLSearchParams()
    Object.entries(nextFilters).forEach(([key, value]) => value && params.set(key, value))
    if (nextDate) params.set("date", nextDate)
    const response = await apiGet(`/api/agencies/${activeContext.agency.id}/operations-command-center?${params}`)
    setContext(activeContext)
    setState(response)
    setFilters(response.filter_metadata?.selected || nextFilters)
    setSelectedDate(response.timeline?.selected_date || nextDate)
    setError("")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function applyFilters(nextFilters) {
    setFilters(nextFilters)
    setState(null)
    await load(nextFilters, selectedDate)
  }

  async function changeDate(date) {
    setSelectedDate(date)
    setState(null)
    await load(filters, date)
  }

  async function runWorkAction(item, action, assigneeId, confirmed = false) {
    if (!action.api_path) return
    if (action.confirmation_required && !confirmed) {
      setPendingConfirmation({ item, action, assigneeId })
      return
    }
    setBusyAction(`${item.id}:${action.key}`)
    try {
      await apiPost(action.api_path, {
        to_user_id: assigneeId || undefined,
        reason: `${action.label} from Operations Command Centre`,
      })
      setPendingConfirmation(null)
      await load(filters, selectedDate)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyAction("")
    }
  }

  const visibleSections = state?.preferences?.visible_sections || sectionOrder
  const orderedSections = useMemo(() => {
    const starting = state?.preferences?.preferred_starting_view || "my_work"
    return [starting, ...sectionOrder].filter((key, index, values) => visibleSections.includes(key) && values.indexOf(key) === index)
  }, [state, visibleSections])

  const name = state?.user_context?.display_name?.split(" ")?.[0] || "there"
  const greeting = new Date().getHours() < 12 ? "Good morning" : new Date().getHours() < 18 ? "Good afternoon" : "Good evening"

  return (
    <AgencyLayout user={context?.me?.user} agency={context?.agency}>
      <ProtectedRoute loading={!state && !error && !context?.onboardingRedirect} error={!state ? error : ""}>
        {!context?.agency ? null : (
          <WorkspacePage as="main" variant="wide" className="space-y-6">
            <PageHeader
              eyebrow="Operations"
              title={`${greeting}, ${name}.`}
              description="Here’s what needs attention and the next action for each item."
              actions={<OperationsFilters metadata={state?.filter_metadata} value={filters} onChange={applyFilters} />}
            />
            <PilotGuidance area="operations" />

            {error ? <OperationalAlert title="The operations view could not be refreshed" tone="error">{error}</OperationalAlert> : null}

            <section aria-label="Today’s operational summary" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
              <DashboardMetric label="Today’s work" value={state?.priorities?.displayed_count || 0} href="/agency/work-queue" detail="Assigned and available" />
              <DashboardMetric label="Action required" value={state?.alerts?.length || 0} href="/agency/work-queue" detail="Warnings and blockers" warning />
              <DashboardMetric label="Deadlines" value={(state?.kpis?.due_soon || 0) + (state?.kpis?.overdue || 0)} href="/agency/deadlines" detail="Due soon or overdue" warning />
              <DashboardMetric label="Bookings needing action" value={(state?.kpis?.accepted_offers_awaiting_booking || 0) + (state?.kpis?.bookings_awaiting_ticketing || 0)} href="/agency/bookings" detail="Booking or ticketing follow-up" />
              <DashboardMetric label="Pending offers" value={state?.kpis?.offers_awaiting_action || queueCount(state?.queues, "offers_awaiting_action")} href="/agency/offers" detail="Preparation or client response" />
              <DashboardMetric label="Pending approvals" value={queueCount(state?.queues, "awaiting_approval")} href="/agency/passenger-services" detail="Passenger service review" />
              <DashboardMetric label="Recent communications" value={state?.recent_activity?.length || 0} href="/agency/communications" detail="Latest recorded activity" />
              <DashboardMetric label="Financial summary" value={state?.kpis?.payment_invoice_blockers || 0} href="/agency/finance" detail="Payment or invoice blockers" warning />
              <DashboardMetric label="Notifications" value={state?.alerts?.length || 0} href="/agency/communications" detail="Items needing follow-up" />
            </section>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
              <div className="space-y-6">
                {orderedSections.map((section) => {
                  if (section === "my_work") return <OperationsWorkList key={section} priorities={state?.priorities} assignees={state?.filter_metadata?.assignees || []} busyAction={busyAction} onAction={runWorkAction} />
                  if (section === "queues") return <OperationsQueues key={section} queues={state?.queues || []} />
                  if (section === "timeline") return <OperationsTimelineActivity key={section} mode="timeline" timeline={state?.timeline} onDateChange={changeDate} />
                  if (section === "recent_activity") return <OperationsTimelineActivity key={section} mode="activity" activities={state?.recent_activity || []} />
                  return null
                })}
              </div>
              <aside className="space-y-6">
                {visibleSections.includes("alerts") ? <OperationsAlerts alerts={state?.alerts || []} /> : null}
                {visibleSections.includes("quick_actions") ? <OperationsAlerts quickActions={state?.quick_actions || []} /> : null}
              </aside>
            </div>
            <ConfirmationDialog
              confirmLabel={pendingConfirmation?.action?.label || "Confirm"}
              message={`Confirm “${pendingConfirmation?.item?.reason || "this action"}”. The update will be added to the work history.`}
              onCancel={() => setPendingConfirmation(null)}
              onConfirm={() => runWorkAction(pendingConfirmation.item, pendingConfirmation.action, pendingConfirmation.assigneeId, true)}
              open={Boolean(pendingConfirmation)}
              title="Confirm this update?"
            />
          </WorkspacePage>
        )}
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function DashboardMetric({ detail, href, label, value, warning = false }) {
  const highlighted = warning && Number(value) > 0
  return (
    <a className={`rounded-lg border bg-white p-4 hover:border-blue-300 ${highlighted ? "border-amber-300" : "border-slate-200"}`} href={href}>
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${highlighted ? "text-amber-800" : "text-slate-950"}`}>{value}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </a>
  )
}

function queueCount(queues = [], key) {
  return queues.find((queue) => queue.key === key)?.count || 0
}
