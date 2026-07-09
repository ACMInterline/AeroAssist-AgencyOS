import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  airline: "",
  policy_family: "",
  service_family: "",
  service_code: "",
  status: "",
  support_status: "",
  search: "",
}

const policyFamilies = [
  "PETC",
  "AVIH",
  "SVAN",
  "ESAN",
  "WCHR",
  "WCHS",
  "WCHC",
  "WCOB",
  "MAAS",
  "MEDIF",
  "MEDA",
  "STCR",
  "OXYG",
  "POC",
  "UMNR",
  "YP",
  "EXST",
  "CBBG",
  "sports_equipment",
  "musical_instruments",
  "fragile_valuable",
  "restricted_equipment",
  "documents_compliance",
]

const cardStatuses = ["draft", "in_review", "approved", "retired", "archived"]
const supportStatuses = ["supported", "not_supported", "conditional", "unknown", "request_required"]

export default function VisualPolicyEditorPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/visual-policy-editor${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || response.policy_cards || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.airline, filters.policy_family, filters.service_family, filters.service_code, filters.status, filters.support_status, filters.search])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Cards", summary.visual_policy_editor_card_count ?? items.length],
    ["Families", `${summary.covered_policy_family_count || 0}/${summary.supported_policy_family_count || policyFamilies.length}`],
    ["Service Codes", summary.service_code_count || 0],
    ["Evidence", summary.evidence_link_count || 0],
    ["Warnings", summary.warning_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Visual Policy Editor</h2>
              <p className="mt-1 text-sm text-slate-600">Structured airline service policy cards with no-code sections for review, evidence, governance, and taxonomy links.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Policy Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <SelectField label="Family" value={filters.policy_family} onChange={(value) => setFilters({ ...filters, policy_family: value })} options={policyFamilies.map(optionPair)} placeholder="All families" />
              <Field label="Service Code" value={filters.service_code} onChange={(value) => setFilters({ ...filters, service_code: value })} />
              <Field label="Service Family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={cardStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Support" value={filters.support_status} onChange={(value) => setFilters({ ...filters, support_status: value })} options={supportStatuses.map(optionPair)} placeholder="Any support" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Policy Cards</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <PolicyCardList items={items} showAgency /> : <EmptyState title="No visual policy cards" body="Visual Policy Editor metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function PolicyCardList({ items, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_170px_170px]">
              <div>
                <p className="font-semibold text-slate-950">{item.card_display_name || item.card_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.card_reference || item.id}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Family: {formatType(item.policy_family)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Status: {formatType(item.status)}</p>
                <p className="mt-1">Support: {formatType(item.support_status)}</p>
              </div>
            </div>
          </summary>
          <PolicySections item={item} />
        </details>
      ))}
    </div>
  )
}

function PolicySections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Overview" value={item.overview_section} />
      <RecordCard title="Support Status" value={item.support_status_section} />
      <RecordCard title="Limits" value={item.limits_section} />
      <RecordCard title="Route / Aircraft / Cabin / Date / Weather Restrictions" value={item.restrictions_section} />
      <RecordCard title="Documents" value={item.documents_section} />
      <RecordCard title="Approvals" value={item.approvals_section} />
      <RecordCard title="Warnings" value={item.warnings_section} />
      <RecordCard title="Evidence" value={item.evidence_section} />
      <RecordCard title="Governance" value={item.governance_section} />
      <RecordCard title="Service Parameter Taxonomy" value={item.taxonomy_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
