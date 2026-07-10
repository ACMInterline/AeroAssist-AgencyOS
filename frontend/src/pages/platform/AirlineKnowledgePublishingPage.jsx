import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  airline_code: "",
  service_family: "",
  publication_status: "",
  release_channel: "",
  agency_visibility: "",
  AOIE_ready: "",
  search: "",
}

const publicationStatuses = ["draft", "qa_approved", "approved", "scheduled", "published", "superseded", "rolled_back", "archived"]
const releaseChannels = ["internal_review", "scenario_testing", "agency_preview", "agency_reference", "production_reference"]
const visibilityStatuses = ["platform_only", "selected_agencies", "all_agencies", "hidden", "suspended"]
const boolOptions = [["true", "Ready"], ["false", "Not ready"]]

export default function AirlineKnowledgePublishingPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/airline-knowledge-publishing${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || response.publications || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.airline_code, filters.service_family, filters.publication_status, filters.release_channel, filters.agency_visibility, filters.AOIE_ready, filters.search])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Publications", summary.airline_knowledge_publication_count ?? items.length],
    ["AOIE Ready", summary.aoie_ready_count || 0],
    ["Knowledge Versions", summary.knowledge_version_count || 0],
    ["QA Reviews", summary.qa_review_count || 0],
    ["Supersedes", summary.superseded_publication_link_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Knowledge Publishing</h2>
              <p className="mt-1 text-sm text-slate-600">Controlled publication workflow metadata for approved airline operational knowledge.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No automatic publication</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Publication Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Airline" value={filters.airline_code} onChange={(value) => setFilters({ ...filters, airline_code: value })} />
              <Field label="Service Family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <SelectField label="Status" value={filters.publication_status} onChange={(value) => setFilters({ ...filters, publication_status: value })} options={publicationStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Channel" value={filters.release_channel} onChange={(value) => setFilters({ ...filters, release_channel: value })} options={releaseChannels.map(optionPair)} placeholder="All channels" />
              <SelectField label="Visibility" value={filters.agency_visibility} onChange={(value) => setFilters({ ...filters, agency_visibility: value })} options={visibilityStatuses.map(optionPair)} placeholder="All visibility" />
              <SelectField label="AOIE Ready" value={filters.AOIE_ready} onChange={(value) => setFilters({ ...filters, AOIE_ready: value })} options={boolOptions} placeholder="Any readiness" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Publication Records</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <PublicationList items={items} showAgency /> : <EmptyState title="No publication metadata" body="Approved airline knowledge publication records will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function PublicationList({ items, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.publication_name || item.publication_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.publication_reference || item.id}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Channel: {formatType(item.release_channel)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Status: {formatType(item.publication_status)}</p>
                <p className="mt-1">AOIE: {item.AOIE_ready ? "Ready" : "Not ready"}</p>
              </div>
            </div>
          </summary>
          <PublicationSections item={item} />
        </details>
      ))}
    </div>
  )
}

function PublicationSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Overview" value={item.overview_section} />
      <RecordCard title="Included Knowledge" value={item.included_knowledge_section} />
      <RecordCard title="Readiness" value={item.readiness_section} />
      <RecordCard title="Release Control" value={item.release_control_section} />
      <RecordCard title="Supersession / Rollback" value={item.supersession_section} />
      <RecordCard title="Lifecycle" value={item.lifecycle_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
