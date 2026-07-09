export function MasterRecordList({ items, type, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => {
        const title = type === "client" ? item.client_display_name || item.client_master_reference : item.passenger_display_name || item.passenger_master_reference
        const status = type === "client" ? item.client_status : item.passenger_status
        const reference = type === "client" ? item.client_master_reference : item.passenger_master_reference
        return (
          <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
            <summary className="cursor-pointer list-none">
              <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
                <div>
                  <p className="font-semibold text-slate-950">{title || reference}</p>
                  <p className="mt-1 text-sm text-slate-600">{reference || item.id}</p>
                </div>
                <div className="text-xs text-slate-600">
                  {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                  <p className="mt-1">Status: {formatType(status)}</p>
                </div>
                <div className="text-xs text-slate-600">
                  <p>{type === "client" ? "Linked passengers" : "Reusable history"}: {type === "client" ? (item.link_summary?.linked_passenger_ids || 0) : reusableHistoryCount(item)}</p>
                  <p className="mt-1">Updated: {shortDate(item.updated_at || item.created_at)}</p>
                </div>
              </div>
            </summary>
            <MasterSections item={item} />
          </details>
        )
      })}
    </div>
  )
}

export function MasterSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Client Overview" value={item.client_overview_section} />
      <RecordCard title="Passenger Overview" value={item.passenger_overview_section} />
      <RecordCard title="Service History" value={item.service_history_section} />
      <RecordCard title="Known Operational Profile" value={item.known_operational_profile_section} />
      <RecordCard title="Known Preferences" value={item.known_preferences_section} />
      <RecordCard title="Portal Access" value={item.portal_access_section} />
      <RecordCard title="Relationship Graph" value={item.relationship_graph_section} />
      <RecordCard title="Notes" value={{ internal_notes: item.internal_notes, agent_notes: item.agent_notes, metadata: item.metadata }} />
    </div>
  )
}

export function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

export function RecordCard({ title, value }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <p className="font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap rounded-md bg-white p-3 text-xs leading-5 text-slate-600">{hasContent(value) ? JSON.stringify(value, null, 2) : "No metadata recorded."}</pre>
    </div>
  )
}

export function Field({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

export function SelectField({ label, value, onChange, options, placeholder }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
  )
}

export function queryString(filters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const query = params.toString()
  return query ? `?${query}` : ""
}

export function optionPair(value) {
  return [value, formatType(value)]
}

export function formatType(value) {
  return value ? String(value).replaceAll("_", " ") : "Unset"
}

function reusableHistoryCount(item) {
  const summary = item.history_link_summary || {}
  return Object.values(summary).reduce((total, value) => total + Number(value || 0), 0)
}

function shortDate(value) {
  return value ? String(value).slice(0, 10) : "Unset"
}

function hasContent(value) {
  if (!value) return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === "object") return Object.values(value).some((item) => hasContent(item) || (item !== null && item !== undefined && item !== ""))
  return true
}
