import { useEffect, useMemo, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
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

  async function runWorkAction(item, action, assigneeId) {
    if (!action.api_path) return
    if (action.confirmation_required && !window.confirm(`Complete “${item.reason}”?`)) return
    setBusyAction(`${item.id}:${action.key}`)
    try {
      await apiPost(action.api_path, {
        to_user_id: assigneeId || undefined,
        reason: `${action.label} from Operations Command Centre`,
      })
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
      <ProtectedRoute loading={!state && !error && !context?.onboardingRedirect} error={error}>
        {!context?.agency ? null : (
          <main className="space-y-6">
            <header className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-200 pb-5">
              <div>
                <p className="text-sm font-semibold text-blue-700">Operations</p>
                <h1 className="mt-1 text-2xl font-semibold text-slate-950">{greeting}, {name}.</h1>
                <p className="mt-1 text-sm text-slate-600">Here’s what needs attention.</p>
              </div>
              <OperationsFilters metadata={state?.filter_metadata} value={filters} onChange={applyFilters} />
            </header>

            {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

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
          </main>
        )}
      </ProtectedRoute>
    </AgencyLayout>
  )
}
