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
