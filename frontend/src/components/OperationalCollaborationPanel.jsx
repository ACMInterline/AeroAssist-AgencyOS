import { useEffect, useMemo, useState } from "react"
import Activity from "lucide-react/dist/esm/icons/activity.js"
import FileText from "lucide-react/dist/esm/icons/file-text.js"
import MessageSquare from "lucide-react/dist/esm/icons/message-square.js"
import NotebookPen from "lucide-react/dist/esm/icons/notebook-pen.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import EmptyState from "./EmptyState"
import LoadingState from "./LoadingState"
import StatusBadge from "./StatusBadge"
import Timeline from "./Timeline"
import { useAuthorization } from "../context/AuthorizationContext"
import { apiGet, apiPost } from "../lib/api"

const tabs = [
  { id: "summary", label: "Activity summary", icon: Activity },
  { id: "timeline", label: "Timeline", icon: Activity },
  { id: "communications", label: "Communications", icon: MessageSquare },
  { id: "notes", label: "Internal notes", icon: NotebookPen },
  { id: "documents", label: "Documents", icon: FileText },
]

export default function OperationalCollaborationPanel({
  agencyId,
  entityId,
  entityLabel = "Operational record",
  entityType,
}) {
  const authorization = useAuthorization()
  const [activeTab, setActiveTab] = useState("summary")
  const [activity, setActivity] = useState(null)
  const [error, setError] = useState("")
  const [posting, setPosting] = useState(false)
  const [draft, setDraft] = useState({ plain_text: "", visibility: "agency" })
  const [searchText, setSearchText] = useState("")
  const [searchResult, setSearchResult] = useState(null)
  const canPost = authorization.hasPermission("edit_tasks")

  async function load() {
    if (!agencyId || !entityId || !entityType) return
    setError("")
    try {
      const result = await apiGet(
        `/api/agencies/${agencyId}/operational-collaboration/entities/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/activity`,
      )
      setActivity(result)
    } catch (loadError) {
      setError(loadError.message)
    }
  }

  useEffect(() => {
    setActivity(null)
    load()
  }, [agencyId, entityId, entityType])

  const internalNotes = useMemo(
    () => (activity?.messages || []).filter(
      (message) => message.message_type === "internal_note" && message.visibility === "internal",
    ),
    [activity],
  )

  async function submitMessage(event, forceInternal = false) {
    event.preventDefault()
    const plainText = draft.plain_text.trim()
    if (!plainText || posting) return
    const visibility = forceInternal ? "internal" : draft.visibility
    setPosting(true)
    setError("")
    try {
      const thread = await findOrCreateThread(visibility)
      await apiPost(
        `/api/agencies/${agencyId}/operational-collaboration/threads/${thread.id}/messages`,
        {
          message_type: forceInternal ? "internal_note" : "message",
          plain_text: plainText,
          visibility,
          delivery_status: ["client", "passenger", "supplier"].includes(visibility)
            ? "not_sent"
            : "recorded",
        },
      )
      setDraft((current) => ({ ...current, plain_text: "" }))
      await load()
    } catch (postError) {
      setError(postError.message)
    } finally {
      setPosting(false)
    }
  }

  async function findOrCreateThread(visibility) {
    const existing = (activity?.threads || []).find(
      (thread) => thread.status === "open" && (thread.visibility || []).includes(visibility),
    )
    if (existing) return existing
    const created = await apiPost(
      `/api/agencies/${agencyId}/operational-collaboration/threads`,
      {
        idempotency_key: `entity-thread:${entityType}:${entityId}:ui_${visibility}`,
        subject: `${entityLabel} ${visibility === "internal" ? "internal notes" : "communication"}`,
        entity_references: [{ entity_type: entityType, entity_id: entityId, label: entityLabel }],
        visibility: visibility === "internal" ? ["internal"] : ["internal", visibility],
        metadata: { context_key: `ui_${visibility}`, external_delivery: false },
      },
    )
    return created.thread
  }

  async function searchActivity(event) {
    event.preventDefault()
    const query = searchText.trim()
    if (!query) {
      setSearchResult(null)
      return
    }
    setError("")
    try {
      setSearchResult(await apiGet(
        `/api/agencies/${agencyId}/operational-collaboration/search?q=${encodeURIComponent(query)}&limit=25`,
      ))
    } catch (searchError) {
      setError(searchError.message)
    }
  }

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white" aria-labelledby={`collaboration-${entityType}-${entityId}`}>
      <div className="border-b border-slate-200 px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-950" id={`collaboration-${entityType}-${entityId}`}>
              Activity and communications
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Canonical operational history. Client, passenger, and supplier messages are recorded here; no external provider sends them.
            </p>
          </div>
          <form className="flex w-full max-w-sm gap-2" onSubmit={searchActivity} role="search">
            <label className="sr-only" htmlFor={`activity-search-${entityType}-${entityId}`}>Search Agency activity</label>
            <input
              className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
              id={`activity-search-${entityType}-${entityId}`}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="Search Agency activity"
              value={searchText}
            />
            <button
              aria-label="Search Agency activity"
              className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 text-slate-700 hover:bg-slate-50"
              title="Search Agency activity"
              type="submit"
            >
              <Search aria-hidden="true" className="h-4 w-4" />
            </button>
          </form>
        </div>
        <div className="mt-4 flex gap-1 overflow-x-auto" role="tablist" aria-label="Operational collaboration">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              aria-controls={`collaboration-panel-${id}-${entityType}-${entityId}`}
              aria-selected={activeTab === id}
              className={`inline-flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold ${
                activeTab === id ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
              id={`collaboration-tab-${id}-${entityType}-${entityId}`}
              key={id}
              onClick={() => setActiveTab(id)}
              role="tab"
              type="button"
            >
              <Icon aria-hidden="true" className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      <div
        aria-labelledby={`collaboration-tab-${activeTab}-${entityType}-${entityId}`}
        className="p-5"
        id={`collaboration-panel-${activeTab}-${entityType}-${entityId}`}
        role="tabpanel"
      >
        {error ? <p className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">{error}</p> : null}
        {!activity && !error ? <LoadingState label="Loading operational activity" /> : null}
        {searchResult ? <SearchResults result={searchResult} onClose={() => setSearchResult(null)} /> : null}
        {activity && activeTab === "summary" ? <ActivitySummary activity={activity} /> : null}
        {activity && activeTab === "timeline" ? (
          <Timeline
            emptyBody="Business events, communication evidence, and governed corrections will appear here."
            emptyTitle="No timeline evidence yet"
            items={activity.timeline}
          />
        ) : null}
        {activity && activeTab === "communications" ? (
          <Communications
            activity={activity}
            canPost={canPost}
            draft={draft}
            onDraft={setDraft}
            onSubmit={submitMessage}
            posting={posting}
          />
        ) : null}
        {activity && activeTab === "notes" ? (
          <InternalNotes
            canPost={canPost}
            draft={draft}
            notes={internalNotes}
            onDraft={setDraft}
            onSubmit={(event) => submitMessage(event, true)}
            posting={posting}
          />
        ) : null}
        {activity && activeTab === "documents" ? <Documents items={activity.documents || []} /> : null}
      </div>
    </section>
  )
}

function ActivitySummary({ activity }) {
  const summary = activity.activity_summary || {}
  const items = [
    ["Timeline entries", summary.timeline_count || 0],
    ["Threads", summary.thread_count || 0],
    ["Messages", summary.message_count || 0],
    ["Internal notes", summary.internal_note_count || 0],
    ["Documents", summary.document_count || 0],
  ]
  return (
    <div>
      <dl className="grid gap-px overflow-hidden rounded-md border border-slate-200 bg-slate-200 sm:grid-cols-2 lg:grid-cols-5">
        {items.map(([label, value]) => (
          <div className="bg-white p-4" key={label}>
            <dt className="text-xs font-medium text-slate-500">{label}</dt>
            <dd className="mt-1 text-xl font-semibold text-slate-950">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-4 text-sm text-slate-600">
        Last activity: {formatDate(summary.last_activity_at)}
      </p>
    </div>
  )
}

function Communications({ activity, canPost, draft, onDraft, onSubmit, posting }) {
  const messages = (activity.messages || []).filter((message) => message.message_type !== "internal_note")
  return (
    <div className="space-y-5">
      {canPost ? (
        <form className="space-y-3" onSubmit={onSubmit}>
          <div className="grid gap-3 sm:grid-cols-[180px_minmax(0,1fr)]">
            <label className="text-sm font-medium text-slate-700">
              Visibility
              <select
                className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                onChange={(event) => onDraft((current) => ({ ...current, visibility: event.target.value }))}
                value={draft.visibility}
              >
                <option value="agency">Agency</option>
                <option value="client">Client Portal</option>
                <option value="passenger">Passenger Portal</option>
                <option value="supplier">Supplier record</option>
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700">
              Message
              <textarea
                className="mt-2 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                onChange={(event) => onDraft((current) => ({ ...current, plain_text: event.target.value }))}
                required
                value={draft.plain_text}
              />
            </label>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-slate-500">This records a message. It does not send email, SMS, chat, or an airline/provider message.</p>
            <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={posting} type="submit">
              {posting ? "Recording..." : "Record message"}
            </button>
          </div>
        </form>
      ) : null}
      {!messages.length ? (
        <EmptyState title="No communications yet" body="Messages linked to this operational record will appear here." />
      ) : (
        <ol className="divide-y divide-slate-200 border-y border-slate-200">
          {messages.map((message) => <MessageRow key={message.id} message={message} />)}
        </ol>
      )}
    </div>
  )
}

function InternalNotes({ canPost, draft, notes, onDraft, onSubmit, posting }) {
  return (
    <div className="space-y-5">
      {canPost ? (
        <form className="space-y-3" onSubmit={onSubmit}>
          <label className="block text-sm font-medium text-slate-700">
            Internal note
            <textarea
              className="mt-2 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              onChange={(event) => onDraft((current) => ({ ...current, plain_text: event.target.value }))}
              required
              value={draft.plain_text}
            />
          </label>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs font-medium text-slate-600">Internal notes are never exposed through Client or Passenger Portal projections.</p>
            <button className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={posting} type="submit">
              {posting ? "Recording..." : "Add internal note"}
            </button>
          </div>
        </form>
      ) : null}
      {!notes.length ? (
        <EmptyState title="No internal notes" body="Internal operational notes linked to this record will appear here." />
      ) : (
        <ol className="divide-y divide-slate-200 border-y border-slate-200">
          {notes.map((message) => <MessageRow key={message.id} message={message} />)}
        </ol>
      )}
    </div>
  )
}

function MessageRow({ message }) {
  return (
    <li className="py-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold text-slate-900">{message.sender_display || "Participant"}</p>
        <div className="flex items-center gap-2">
          <StatusBadge status={message.delivery_status || "recorded"} />
          <time className="text-xs text-slate-500" dateTime={message.created_at || ""}>{formatDate(message.created_at)}</time>
        </div>
      </div>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{message.plain_text}</p>
      {message.edited_at ? <p className="mt-2 text-xs text-slate-500">Edited with prior content preserved.</p> : null}
    </li>
  )
}

function Documents({ items }) {
  if (!items.length) {
    return <EmptyState title="No communication documents" body="Immutable document and attachment references linked to these threads will appear here." />
  }
  return (
    <ul className="divide-y divide-slate-200 border-y border-slate-200">
      {items.map((item) => (
        <li className="flex flex-wrap items-center justify-between gap-3 py-4" key={item.id}>
          <div>
            <p className="text-sm font-semibold text-slate-900">{item.title || item.reference_id}</p>
            <p className="mt-1 text-xs text-slate-500">{item.reference_type} · immutable reference · no binary copy</p>
          </div>
          <StatusBadge label={item.visibility} status="default" />
        </li>
      ))}
    </ul>
  )
}

function SearchResults({ result, onClose }) {
  return (
    <div className="mb-5 border-b border-slate-200 pb-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-slate-900">Agency activity search · {result.count || 0} results</p>
        <button className="text-sm font-semibold text-blue-700" onClick={onClose} type="button">Close results</button>
      </div>
      {!result.items?.length ? <p className="mt-3 text-sm text-slate-500">No permitted activity matched.</p> : (
        <ul className="mt-3 space-y-2">
          {result.items.map((item) => (
            <li className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700" key={`${item.result_type}-${item.id}`}>
              <span className="font-semibold">{item.result_type.replaceAll("_", " ")}</span> · {item.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function formatDate(value) {
  if (!value) return "Not recorded"
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString()
}
