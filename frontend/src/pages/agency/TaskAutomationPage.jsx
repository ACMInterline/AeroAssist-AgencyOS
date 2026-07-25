import { useEffect, useMemo, useState } from "react"
import CirclePlay from "lucide-react/dist/esm/icons/circle-play.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import EmptyState from "../../components/EmptyState"
import PageHeader from "../../components/PageHeader"
import ProductTable from "../../components/ProductTable"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import { Field, Metric, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = { trigger_event: "", status: "" }

export default function TaskAutomationPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [draft, setDraft] = useState({ name: "", rule_key: "", trigger_event: "request.created", template_code: "triage_request" })
  const [notice, setNotice] = useState("")
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const response = await apiGet(`/api/agencies/${context.agency.id}/task-automation${queryString(nextFilters)}`)
    setState({ ...context, ...response })
  }

  async function perform(request, success) {
    setError("")
    setNotice("")
    try {
      await request()
      setNotice(success)
      await load(filters)
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  async function createDraft(event) {
    event.preventDefault()
    const triggerEntityType = draft.trigger_event.split(".", 1)[0]
    await perform(
      () => apiPost(`/api/agencies/${state.agency.id}/task-automation/rules`, {
        name: draft.name,
        rule_key: draft.rule_key || draft.name,
        description: "Agency-governed internal work rule.",
        trigger_event_types: [draft.trigger_event],
        trigger_entity_types: [triggerEntityType],
        conditions_json: {},
        actions: [{ action_type: "create_work_item", parameters: { template_code: draft.template_code } }],
        generated_template_code: draft.template_code,
        execution_safety_class: "A",
        dry_run_supported: true,
      }),
      "Draft rule created. It will not execute until an administrator publishes it.",
    )
  }

  async function lifecycle(rule, action) {
    await perform(
      () => apiPost(`/api/agencies/${state.agency.id}/task-automation/rules/${rule.id}/${action}`, {
        reason: `${formatType(action)} requested from Agency automation governance.`,
        expected_version: rule.version,
      }),
      `Rule version ${action === "publish" ? "published" : action === "supersede" ? "superseded its active predecessor" : "deactivated"}.`,
    )
  }

  async function processTimeline() {
    await perform(
      () => apiPost(`/api/agencies/${state.agency.id}/task-automation/process`, { timeline_entry_ids: [], batch_limit: 25, dry_run: false }),
      "The bounded timeline batch was processed. Replays reuse prior execution evidence.",
    )
  }

  async function processReminders() {
    await perform(
      () => apiPost(`/api/agencies/${state.agency.id}/task-automation/process-reminders`, { batch_limit: 50 }),
      "Due work and internal reminder projections were reviewed.",
    )
  }

  async function retryRun(runId) {
    await perform(
      () => apiPost(`/api/agencies/${state.agency.id}/task-automation/runs/${runId}/retry`, { reason: "Manual bounded retry after operator review." }),
      "Retry recorded with separate immutable execution evidence.",
    )
  }

  async function updateDependency(dependencyId, action) {
    await perform(
      () => apiPost(`/api/agencies/${state.agency.id}/task-automation/dependencies/${dependencyId}/${action}`, { reason: `Operator ${action} after dependency review.` }),
      `Dependency ${action} recorded.`,
    )
  }

  useEffect(() => {
    load(filters).catch((requestError) => setError(requestError.message))
  }, [filters.trigger_event, filters.status])

  const membershipRole = state?.agency?.current_membership?.role
  const canGovern = ["agency_owner", "agency_admin"].includes(membershipRole)
  const eventOptions = (state?.event_catalogue || []).map((value) => [value, formatType(value)])
  const templateOptions = (state?.templates || []).map((item) => [item.template_code, item.title_pattern || formatType(item.template_code)])
  const activeRuleCount = (state?.rules || []).filter((rule) => rule.status === "active" && rule.published_at).length
  const metrics = [
    ["Published rules", activeRuleCount],
    ["Open approvals", (state?.approvals || []).filter((item) => ["requested", "assigned"].includes(item.status)).length],
    ["Ready work", state?.ready_tasks?.length || 0],
    ["Blocked work", state?.blocked_tasks?.length || 0],
    ["Execution records", state?.runs?.length || 0],
  ]
  const ruleColumns = useMemo(() => [
    { key: "rule", label: "Rule", render: (rule) => <div><p className="font-semibold text-slate-950">{rule.name}</p><p className="mt-1 text-xs text-slate-500">{rule.rule_key || rule.rule_code}</p></div>, sortValue: (rule) => rule.name },
    { key: "version", label: "Version", render: (rule) => <span>v{rule.version || 1}</span>, sortValue: (rule) => rule.version || 1 },
    { key: "trigger", label: "When", render: (rule) => formatType(rule.trigger_event), sortValue: (rule) => rule.trigger_event },
    { key: "status", label: "Status", render: (rule) => <div><StatusBadge status={rule.status} /><p className="mt-1 text-xs text-slate-500">{rule.published_at ? "Published" : "Not published"}</p></div>, sortValue: (rule) => rule.status },
    { key: "safety", label: "Safety", render: (rule) => <span>Class {rule.execution_safety_class || "A"}</span> },
    { key: "actions", label: "Governance", render: (rule) => <RuleActions canGovern={canGovern} onAction={lifecycle} rule={rule} /> },
  ], [canGovern, state?.agency?.id])
  const runColumns = [
    { key: "run", label: "Execution", render: (run) => <div><p className="font-semibold text-slate-950">{run.run_reference}</p><p className="mt-1 text-xs text-slate-500">{formatType(run.trigger_event)}</p></div>, sortValue: (run) => run.created_at },
    { key: "result", label: "Result", render: (run) => <div><StatusBadge status={run.status} /><p className="mt-1 text-xs text-slate-500">{run.idempotency_result || "created"}</p></div> },
    { key: "rules", label: "Rules and work", render: (run) => <span>{(run.rules_matched || []).length} matched · {(run.tasks_created || []).length} created</span> },
    { key: "safety", label: "Safety", render: (run) => <span>Class {run.execution_safety_class || "A"}</span> },
    { key: "retry", label: "Operator action", render: (run) => <button className="secondary-button" onClick={() => retryRun(run.id)} type="button">Retry safely</button> },
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <PageHeader
            eyebrow="Operations governance"
            title="Automation rules"
            description="Turn canonical timeline events into internal tasks, deadlines, approvals, and reminders. Published rules are deterministic and never perform external or commercial actions."
            actions={<div className="flex flex-wrap gap-2"><button className="secondary-button" onClick={processReminders} type="button"><RefreshCw aria-hidden="true" className="h-4 w-4" />Review reminders</button><button className="primary-button" onClick={processTimeline} type="button"><CirclePlay aria-hidden="true" className="h-4 w-4" />Process next safe batch</button></div>}
          />

          <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
            <p className="inline-flex items-center gap-2 font-semibold"><ShieldCheck aria-hidden="true" className="h-4 w-4" />Human authority remains final</p>
            <p className="mt-1">Class C decisions create approval work only. Provider, airline, ticketing, payment, refund, external message, permission, and tenant actions are prohibited.</p>
          </div>
          {notice ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{notice}</div> : null}
          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">{metrics.map(([label, value]) => <Metric key={label} label={label} value={value} />)}</section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Find rules and execution records</h3>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <SelectField label="Timeline event" value={filters.trigger_event} onChange={(value) => setFilters({ ...filters, trigger_event: value })} options={eventOptions} placeholder="All events" />
              <SelectField label="Execution status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={["processing", "completed", "completed_with_warnings", "skipped", "failed", "manual_review"].map((value) => [value, formatType(value)])} placeholder="All results" />
            </div>
          </section>

          {canGovern ? (
            <form className="rounded-lg border border-slate-200 bg-white p-5" onSubmit={createDraft}>
              <h3 className="font-semibold text-slate-950">Create a draft internal-work rule</h3>
              <p className="mt-1 text-sm text-slate-600">Drafts are inert. Review and publish explicitly before they can match timeline events.</p>
              <div className="mt-4 grid gap-3 lg:grid-cols-4">
                <Field label="Rule name" value={draft.name} onChange={(value) => setDraft({ ...draft, name: value })} />
                <Field label="Stable rule key" value={draft.rule_key} onChange={(value) => setDraft({ ...draft, rule_key: value })} />
                <SelectField label="When this happens" value={draft.trigger_event} onChange={(value) => setDraft({ ...draft, trigger_event: value })} options={eventOptions} />
                <SelectField label="Create this task" value={draft.template_code} onChange={(value) => setDraft({ ...draft, template_code: value })} options={templateOptions} />
              </div>
              <button className="primary-button mt-4" disabled={!draft.name || !draft.trigger_event || !draft.template_code} type="submit">Create draft</button>
            </form>
          ) : null}

          <section>
            <h3 className="mb-3 font-semibold text-slate-950">Rule versions</h3>
            <ProductTable caption="Automation rule versions" columns={ruleColumns} defaultSort={{ key: "rule", direction: "asc" }} emptyBody="Create an Agency draft or review the governed Platform templates available to this Agency." emptyTitle="No automation rules" pageSize={15} rows={state?.rules || []} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,.65fr)]">
            <div>
              <h3 className="mb-3 font-semibold text-slate-950">Immutable execution history</h3>
              <ProductTable caption="Automation execution history" columns={runColumns} defaultSort={{ key: "run", direction: "desc" }} emptyBody="Use the bounded processing action after canonical timeline events exist." emptyTitle="No executions recorded" pageSize={12} rows={state?.runs || []} />
            </div>
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Approvals and dependencies</h3>
              <p className="mt-1 text-sm text-slate-600">Class C work remains blocked until an authorized person records a decision through the canonical approval route.</p>
              <div className="mt-4 space-y-3">
                {(state?.approvals || []).slice(0, 6).map((approval) => <Record key={approval.id} title={approval.title} lines={[`Status: ${formatType(approval.status)}`, `Permission: ${formatType(approval.approval_required_permission)}`, `Source: ${formatType(approval.source_entity_type)}`]} />)}
                {(state?.dependencies || []).slice(0, 6).map((dependency) => <Dependency key={dependency.id} dependency={dependency} onAction={updateDependency} />)}
                {!(state?.approvals || []).length && !(state?.dependencies || []).length ? <EmptyState title="No approvals or dependencies" body="Governed approval and task-order evidence will appear here." /> : null}
              </div>
            </section>
          </section>

          <details className="rounded-lg border border-slate-200 bg-white p-5">
            <summary className="cursor-pointer font-semibold text-slate-950">Advanced catalogue and operational metrics</summary>
            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              <Catalogue title="Timeline events" items={state?.event_catalogue || []} />
              <Catalogue title="Allowed internal actions" items={(state?.action_catalogue || []).map((item) => `${item.action_type} · Class ${item.safety_class}`)} />
              <Catalogue title="Task types" items={(state?.task_type_catalogue || []).map((item) => `${item.task_type} · ${item.required_permission}`)} />
            </div>
          </details>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function RuleActions({ canGovern, onAction, rule }) {
  if (!canGovern || rule.is_default || !rule.agency_id) return <span className="text-xs text-slate-500">Read only</span>
  return (
    <div className="flex flex-wrap gap-2">
      {rule.status === "draft" ? <button className="secondary-button" onClick={() => onAction(rule, "publish")} type="button">Publish</button> : null}
      {rule.status === "draft" ? <button className="secondary-button" onClick={() => onAction(rule, "supersede")} type="button">Supersede</button> : null}
      {rule.status === "active" ? <button className="secondary-button" onClick={() => onAction(rule, "deactivate")} type="button">Deactivate</button> : null}
    </div>
  )
}

function Dependency({ dependency, onAction }) {
  return (
    <Record
      title={dependency.successor_task?.title || "Task dependency"}
      lines={[`${dependency.predecessor_task?.title || "Predecessor"} must finish first`, `Status: ${formatType(dependency.status)}`, `Type: ${formatType(dependency.dependency_type)}`]}
      actions={dependency.status === "pending" ? <><button className="secondary-button" onClick={() => onAction(dependency.id, "satisfy")} type="button">Satisfy</button><button className="secondary-button" onClick={() => onAction(dependency.id, "waive")} type="button">Waive</button></> : null}
    />
  )
}

function Record({ actions, lines, title }) {
  return <div className="rounded-md border border-slate-200 p-3"><p className="font-medium text-slate-950">{title}</p><div className="mt-2 space-y-1 text-xs text-slate-600">{lines.map((line) => <p key={line}>{line}</p>)}</div>{actions ? <div className="mt-3 flex flex-wrap gap-2">{actions}</div> : null}</div>
}

function Catalogue({ items, title }) {
  return <div><p className="text-xs font-semibold uppercase text-slate-500">{title}</p><ul className="mt-2 max-h-64 space-y-1 overflow-auto text-xs text-slate-700">{items.map((item) => <li key={item}>{formatType(item)}</li>)}</ul></div>
}
