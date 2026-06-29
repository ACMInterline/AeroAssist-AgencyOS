import { useEffect, useMemo, useRef, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"
import {
  archivePlatformReferenceRecord,
  archivePlatformServiceCatalogue,
  applyPlatformReferenceImport,
  commitReferenceEnrichmentImport,
  createPlatformServiceCatalogue,
  createPlatformReferenceRecord,
  dryRunReferenceEnrichmentImport,
  exportPlatformReferenceData,
  fetchPlatformServiceCatalogue,
  fetchReferenceActionRequired,
  fetchReferenceDomainUsage,
  fetchReferenceEnrichmentBatches,
  fetchReferenceEnrichmentPacks,
  fetchReferenceEnrichmentTemplate,
  fetchReferenceEnrichmentTemplates,
  fetchReferenceHealth,
  fetchReferenceImportTemplates,
  fetchPlatformReferenceDomains,
  fetchPlatformReferenceImportBatches,
  fetchPlatformReferenceRecord,
  fetchPlatformReferenceRecords,
  fetchPlatformReferenceSuggestions,
  previewPlatformReferenceImport,
  reviewPlatformReferenceSuggestion,
  savePlatformReferenceDomain,
  updatePlatformServiceCatalogue,
  updatePlatformReferenceRecord,
} from "../../lib/platformReferenceData"

const tabs = [
  ["domains", "Domains"],
  ["records", "Global Records"],
  ["service", "Service Catalogue"],
  ["suggestions", "Agency Suggestions"],
  ["import", "Bulk Import"],
  ["enrichment", "Enrichment Packs"],
  ["export", "Bulk Export"],
  ["health", "Reference Health"],
  ["audit", "Audit / Update History"],
]

const countryDefaults = {
  iso2_code: "",
  iso3_code: "",
  continent: "",
  capital_city: "",
  capital_iata_code: "",
  major_airports: "",
  official_languages: "",
  currency_name: "",
  currency_iso_code: "",
  population_estimate: "",
  population_estimate_year: "",
  national_carrier_name: "",
  national_carrier_iata_code: "",
  major_airline_1_name: "",
  major_airline_1_iata_code: "",
  major_airline_2_name: "",
  major_airline_2_iata_code: "",
  major_airline_3_name: "",
  major_airline_3_iata_code: "",
  travel_notes: "",
  data_quality_status: "draft",
  source_notes: "",
}

const cityDefaults = {
  country_code: "",
}

const defaultRecordFilters = {
  data_quality_status: "",
  continent: "",
  missing_iso3: false,
  missing_capital_iata: false,
  missing_currency: false,
  missing_major_airports: false,
  missing_national_carrier: false,
}

function metadataDefaultsForDomain(domain) {
  if (domain === "countries") return { ...countryDefaults }
  if (domain === "cities") return { ...cityDefaults }
  return {}
}

function emptyRecord(domain = "countries") {
  const metadata = metadataDefaultsForDomain(domain)
  const form = {
    domain,
    code: "",
    label: "",
    description: "",
    aliases: "",
    sort_order: 100,
    is_active: true,
    metadata,
    metadata_json: "{}",
  }
  return { ...form, metadata_json: JSON.stringify(buildMetadataFromRecordForm(domain, form), null, 2) }
}

function emptyServiceForm() {
  return {
    service_key: "",
    label: "",
    description: "",
    category: "other",
    subcategory: "",
    status: "active",
    sort_order: 100,
    ssr_code: "",
    rules_category: "OTHER",
    default_service_type: "",
    emd_applicability: "none",
    request_form_enabled: true,
    exception_engine_enabled: true,
    booking_preview_enabled: true,
    offer_feasibility_enabled: true,
    offer_pricing_enabled: false,
    acceptance_snapshot_enabled: true,
    booking_readiness_enabled: true,
    requires_passenger_scope: false,
    requires_segment_scope: true,
    required_documents_json: "[]",
    required_fields_json: "{}",
    validation_rules_json: "{}",
    internal_handling_notes: "",
  }
}

function serviceToForm(service) {
  return {
    ...emptyServiceForm(),
    ...service,
    service_key: service?.service_key || service?.service_code || "",
    label: service?.label || service?.service_label || "",
    category: service?.category || service?.service_family_code || "other",
    ssr_code: service?.ssr_code || service?.default_ssr_code || "",
    required_documents_json: JSON.stringify(service?.required_documents_json || [], null, 2),
    required_fields_json: JSON.stringify(service?.required_fields_json || {}, null, 2),
    validation_rules_json: JSON.stringify(service?.validation_rules_json || {}, null, 2),
  }
}

function normalizeAliases(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || "").trim()).filter(Boolean)
  }
  return String(value || "")
    .split(/[|,;]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function domainSpecificMetadataKeys(domain) {
  if (domain === "cities") return ["record_type", "iata_city_code", "city_name", "legacy_codes", "country_code"]
  return []
}

function parseAdvancedMetadata(value) {
  try {
    const parsed = JSON.parse(value || "{}")
    if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
      throw new Error("Advanced metadata must be a JSON object.")
    }
    return parsed
  } catch (err) {
    throw new Error(err.message === "Advanced metadata must be a JSON object." ? err.message : "Advanced metadata must be valid JSON.")
  }
}

function extraMetadataFromJson(form) {
  const metadata = parseAdvancedMetadata(form.metadata_json || "{}")
  const canonicalKeys = new Set(domainSpecificMetadataKeys(form.domain))
  return Object.fromEntries(Object.entries(metadata).filter(([key]) => !canonicalKeys.has(key)))
}

function assertCityMetadataDoesNotContradictForm(form, parsedMetadata) {
  const code = String(form.code || "").trim().toUpperCase()
  const label = String(form.label || "").trim()
  const countryCode = String(form.metadata?.country_code || "").trim().toUpperCase()
  const checks = [
    ["iata_city_code", code],
    ["city_name", label],
    ["country_code", countryCode],
  ]
  if (parsedMetadata.record_type && parsedMetadata.record_type !== "city") {
    throw new Error("Advanced metadata record_type must be city for city records.")
  }
  checks.forEach(([key, expected]) => {
    if (parsedMetadata[key] && expected && String(parsedMetadata[key]).trim().toUpperCase() !== expected.toUpperCase()) {
      throw new Error(`Advanced metadata ${key} contradicts the canonical form field.`)
    }
  })
}

function buildMetadataFromRecordForm(domain, form) {
  if (domain === "cities") {
    return compactObject({
      ...extraMetadataFromJson({ ...form, domain }),
      record_type: "city",
      iata_city_code: String(form.code || "").trim().toUpperCase(),
      city_name: String(form.label || "").trim(),
      legacy_codes: normalizeAliases(form.aliases).map((item) => item.toUpperCase()),
      country_code: String(form.metadata?.country_code || "").trim().toUpperCase(),
    })
  }
  if (domain !== "countries") {
    return parseAdvancedMetadata(form.metadata_json || "{}")
  }
  const metadata = compactObject({
    iso2_code: form.metadata.iso2_code.toUpperCase(),
    iso3_code: form.metadata.iso3_code.toUpperCase(),
    continent: form.metadata.continent,
    capital_city: form.metadata.capital_city,
    capital_iata_code: form.metadata.capital_iata_code.toUpperCase(),
    currency_name: form.metadata.currency_name,
    currency_iso_code: form.metadata.currency_iso_code.toUpperCase(),
    population_estimate: form.metadata.population_estimate ? Number(form.metadata.population_estimate) : "",
    population_estimate_year: form.metadata.population_estimate_year ? Number(form.metadata.population_estimate_year) : "",
    travel_notes: form.metadata.travel_notes,
    data_quality_status: form.metadata.data_quality_status || "draft",
    source_notes: form.metadata.source_notes,
  })
  const majorAirports = splitValues(form.metadata.major_airports).map((item) => item.toUpperCase())
  const languages = splitValues(form.metadata.official_languages)
  const majorAirlines = [1, 2, 3]
    .map((index) =>
      compactObject({
        name: form.metadata[`major_airline_${index}_name`],
        iata_code: form.metadata[`major_airline_${index}_iata_code`]?.toUpperCase(),
      })
    )
    .filter((item) => item.name || item.iata_code)
  if (majorAirports.length) metadata.major_airports = majorAirports
  if (languages.length) metadata.official_languages = languages
  if (form.metadata.national_carrier_name || form.metadata.national_carrier_iata_code) {
    metadata.national_carrier = compactObject({
      name: form.metadata.national_carrier_name,
      iata_code: form.metadata.national_carrier_iata_code.toUpperCase(),
    })
  }
  if (majorAirlines.length) metadata.major_airlines = majorAirlines
  return metadata
}

function mergeMetadataIntoRecordForm(domain, record) {
  const metadata = record?.metadata_json || {}
  if (domain === "cities") {
    return {
      ...metadataDefaultsForDomain(domain),
      country_code: metadata.country_code || "",
    }
  }
  if (domain !== "countries") return metadata
  const nationalCarrier = metadata.national_carrier || {}
  const majorAirlines = metadata.major_airlines || []
  return {
    ...countryDefaults,
    ...metadata,
    major_airports: (metadata.major_airports || []).join(", "),
    official_languages: (metadata.official_languages || []).join(", "),
    national_carrier_name: nationalCarrier.name || "",
    national_carrier_iata_code: nationalCarrier.iata_code || "",
    major_airline_1_name: majorAirlines[0]?.name || "",
    major_airline_1_iata_code: majorAirlines[0]?.iata_code || "",
    major_airline_2_name: majorAirlines[1]?.name || "",
    major_airline_2_iata_code: majorAirlines[1]?.iata_code || "",
    major_airline_3_name: majorAirlines[2]?.name || "",
    major_airline_3_iata_code: majorAirlines[2]?.iata_code || "",
  }
}

function splitValues(value) {
  return String(value || "")
    .split(/[|,;]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3)
}

function compactObject(value) {
  return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== undefined && item !== null && item !== ""))
}

function recordToForm(record) {
  const domain = record?.domain || "countries"
  const form = {
    domain: record?.domain || "countries",
    code: record?.code || record?.key || "",
    label: record?.label || "",
    description: record?.description || "",
    aliases: (record?.aliases || []).join(", "),
    sort_order: record?.sort_order || 100,
    is_active: record?.is_active !== false,
    metadata: mergeMetadataIntoRecordForm(domain, record),
    metadata_json: JSON.stringify(record?.metadata_json || {}, null, 2),
  }
  return { ...form, metadata_json: JSON.stringify(buildMetadataFromRecordForm(domain, form), null, 2) }
}

function metadataFromForm(form) {
  return buildMetadataFromRecordForm(form.domain, form)
}

function recordPayload(form) {
  return {
    domain: form.domain,
    code: form.domain === "cities" ? form.code.toUpperCase().trim() : form.code,
    label: form.label,
    description: form.description || null,
    aliases: normalizeAliases(form.aliases),
    sort_order: Number(form.sort_order || 100),
    is_active: form.is_active,
    metadata_json: metadataFromForm(form),
  }
}

function Field({ label, children }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      {children}
    </label>
  )
}

function TextInput(props) {
  return <input {...props} className={`rounded-md border border-slate-300 px-3 py-2 text-sm ${props.className || ""}`} />
}

export default function PlatformReferenceDataPage({ recordId }) {
  const [activeTab, setActiveTab] = useState(recordId ? "health" : "domains")
  const [summary, setSummary] = useState(null)
  const [referenceReadiness, setReferenceReadiness] = useState(null)
  const [domains, setDomains] = useState([])
  const [domainUsage, setDomainUsage] = useState([])
  const [referenceHealth, setReferenceHealth] = useState(null)
  const [actionRequired, setActionRequired] = useState([])
  const [records, setRecords] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [imports, setImports] = useState([])
  const [importTemplates, setImportTemplates] = useState([])
  const [importResult, setImportResult] = useState(null)
  const [enrichmentTemplates, setEnrichmentTemplates] = useState([])
  const [enrichmentPacks, setEnrichmentPacks] = useState([])
  const [enrichmentBatches, setEnrichmentBatches] = useState([])
  const [serviceCatalogue, setServiceCatalogue] = useState([])
  const [serviceForm, setServiceForm] = useState(emptyServiceForm())
  const [editingServiceId, setEditingServiceId] = useState(null)
  const [auditEvents, setAuditEvents] = useState([])
  const [selectedDomain, setSelectedDomain] = useState("countries")
  const [selectedRecord, setSelectedRecord] = useState(null)
  const [recordForm, setRecordForm] = useState(emptyRecord("countries"))
  const [domainForm, setDomainForm] = useState({ domain: "countries", label: "Countries", description: "", category: "geography", is_active: true, sort_order: 10 })
  const [filters, setFilters] = useState(defaultRecordFilters)
  const [importCsv, setImportCsv] = useState("domain,code,label,iso2_code,iso3_code,continent,capital_city,capital_iata_code,major_airports,official_languages,currency_name,currency_iso_code,national_carrier_name,national_carrier_iata_code,data_quality_status\ncountries,CA,Canada,CA,CAN,North America,Ottawa,YOW,\"YYZ,YVR,YUL\",English|French,Canadian dollar,CAD,Air Canada,AC,draft")
  const [importMode, setImportMode] = useState("upsert")
  const [enrichmentForm, setEnrichmentForm] = useState({ template_name: "countries_enriched", domain: "countries", update_mode: "update_missing_only", csv_text: "", source_label: "Manual platform import pack", notes: "" })
  const [enrichmentReport, setEnrichmentReport] = useState(null)
  const [enrichmentDryRunOk, setEnrichmentDryRunOk] = useState(false)
  const [exportOptions, setExportOptions] = useState({ export_type: "domain", domain: "countries", format: "csv" })
  const [exportResult, setExportResult] = useState(null)
  const [notice, setNotice] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [recordNotice, setRecordNotice] = useState("")
  const [recordError, setRecordError] = useState("")
  const [recordsLoading, setRecordsLoading] = useState(false)
  const [savingRecord, setSavingRecord] = useState(false)
  const recordLoadRequestRef = useRef(0)
  const selectedDomainRef = useRef(selectedDomain)

  const domainOptions = useMemo(() => domains.map((domain) => domain.domain), [domains])
  const selectedDomainMeta = useMemo(() => domains.find((domain) => domain.domain === selectedDomain), [domains, selectedDomain])
  const domainUsageByKey = useMemo(() => Object.fromEntries(domainUsage.map((item) => [item.domain_key, item])), [domainUsage])
  const actionCountByDomain = useMemo(() => {
    const counts = {}
    actionRequired.forEach((item) => {
      counts[item.domain] = (counts[item.domain] || 0) + 1
    })
    return counts
  }, [actionRequired])
  const selectedImportTemplate = useMemo(() => importTemplates.find((template) => template.domain_key === selectedDomain), [importTemplates, selectedDomain])
  const selectedDomainLabel = selectedDomainMeta?.label || selectedDomain.replaceAll("_", " ")
  const selectedDomainHasCountrySchema = selectedDomain === "countries"
  const recordCodeColumnLabel = {
    cities: "IATA City Code",
    airports: "IATA Airport Code",
    airlines: "Airline Code",
  }[selectedDomain] || "Code"
  const synchronizedMetadataJson = useMemo(() => {
    try {
      return JSON.stringify(buildMetadataFromRecordForm(recordForm.domain, recordForm), null, 2)
    } catch {
      return recordForm.metadata_json
    }
  }, [recordForm])
  const visibleAuditEvents = useMemo(
    () => auditEvents.filter((event) => String(event.event_type || "").includes("reference")).slice(-40).reverse(),
    [auditEvents]
  )

  useEffect(() => {
    selectedDomainRef.current = selectedDomain
  }, [selectedDomain])

  async function loadRecords(domain = selectedDomain, nextFilters = filters) {
    const requestId = recordLoadRequestRef.current + 1
    recordLoadRequestRef.current = requestId
    setRecordsLoading(true)
    setRecords([])
    setRecordError("")
    try {
      const result = await fetchPlatformReferenceRecords({ domain, include_inactive: true, ...nextFilters })
      if (recordLoadRequestRef.current !== requestId || selectedDomainRef.current !== domain) return
      setRecords((result.items || []).filter((record) => record.domain === domain))
    } catch (err) {
      if (recordLoadRequestRef.current !== requestId || selectedDomainRef.current !== domain) return
      setRecords([])
      setRecordError(err.message)
    } finally {
      if (recordLoadRequestRef.current === requestId && selectedDomainRef.current === domain) {
        setRecordsLoading(false)
      }
    }
  }

  async function loadAll() {
    setLoading(true)
    const [
      summaryResult,
      readinessResult,
      domainsResult,
      domainUsageResult,
      healthResult,
      actionResult,
      suggestionsResult,
      importsResult,
      importTemplatesResult,
      enrichmentTemplatesResult,
      enrichmentPacksResult,
      enrichmentBatchesResult,
      serviceResult,
      auditResult,
    ] = await Promise.all([
      apiGet("/api/platform/summary"),
      apiGet("/api/readiness"),
      fetchPlatformReferenceDomains(),
      fetchReferenceDomainUsage(),
      fetchReferenceHealth(),
      fetchReferenceActionRequired(),
      fetchPlatformReferenceSuggestions(),
      fetchPlatformReferenceImportBatches(),
      fetchReferenceImportTemplates(),
      fetchReferenceEnrichmentTemplates(),
      fetchReferenceEnrichmentPacks(),
      fetchReferenceEnrichmentBatches(),
      fetchPlatformServiceCatalogue({ include_archived: true }),
      apiGet("/api/platform/audit-events"),
    ])
    setSummary(summaryResult)
    setReferenceReadiness(readinessResult.platform_reference_console || {})
    setDomains(domainsResult.items || [])
    setDomainUsage(domainUsageResult.items || [])
    setReferenceHealth(healthResult || {})
    setActionRequired(actionResult.items || [])
    setSuggestions(suggestionsResult.items || [])
    setImports(importsResult.items || [])
    setImportTemplates(importTemplatesResult.items || [])
    setEnrichmentTemplates(enrichmentTemplatesResult.items || [])
    setEnrichmentPacks(enrichmentPacksResult.items || [])
    setEnrichmentBatches(enrichmentBatchesResult.items || [])
    setServiceCatalogue(serviceResult.items || [])
    setAuditEvents(auditResult.items || [])
    await loadRecords(selectedDomain)
    if (recordId) {
      const card = await fetchPlatformReferenceRecord(recordId)
      selectedDomainRef.current = card.record.domain
      setSelectedDomain(card.record.domain)
      populateDomainMetadataForm(card.record.domain)
      setSelectedRecord(card.record)
      setRecordForm(recordToForm(card.record))
      await loadRecords(card.record.domain)
    }
    setLoading(false)
  }

  useEffect(() => {
    loadAll().catch((err) => {
      setError(err.message)
      setLoading(false)
    })
  }, [recordId])

  function populateDomainMetadataForm(domain) {
    const selected = domains.find((item) => item.domain === domain)
    setDomainForm({
      domain,
      label: selected?.label || "",
      description: selected?.description || "",
      category: selected?.category || "reference",
      is_active: selected?.is_active !== false,
      sort_order: selected?.sort_order || 100,
    })
  }

  async function changeDomain(domain, options = {}) {
    const nextFilters = domain === "countries" ? filters : defaultRecordFilters
    selectedDomainRef.current = domain
    setSelectedDomain(domain)
    setRecords([])
    setRecordForm(emptyRecord(domain))
    setSelectedRecord(null)
    setRecordNotice("")
    setRecordError("")
    setNotice("")
    populateDomainMetadataForm(domain)
    if (domain !== "countries") setFilters(defaultRecordFilters)
    await loadRecords(domain, nextFilters)
    if (options.openRecords) {
      setActiveTab("records")
      setNotice(`Showing ${domains.find((item) => item.domain === domain)?.label || domain.replaceAll("_", " ")} records.`)
    }
  }

  function editDomainMetadata(domain) {
    selectedDomainRef.current = domain
    setSelectedDomain(domain)
    populateDomainMetadataForm(domain)
    setNotice("")
    setRecordNotice("")
    setRecordError("")
  }

  async function selectTab(tab) {
    setActiveTab(tab)
    if (tab === "records") {
      setRecordNotice("")
      setRecordError("")
      await loadRecords(selectedDomain)
    }
  }

  function setRecordField(name, value) {
    setRecordForm((current) => ({ ...current, [name]: value }))
  }

  function setMetadataField(name, value) {
    setRecordForm((current) => ({ ...current, metadata: { ...current.metadata, [name]: value } }))
  }

  async function saveDomain(event) {
    event.preventDefault()
    await savePlatformReferenceDomain(domainForm.domain, {
      label: domainForm.label,
      description: domainForm.description || null,
      category: domainForm.category || "reference",
      is_active: domainForm.is_active,
      sort_order: Number(domainForm.sort_order || 100),
    })
    setNotice("Domain metadata saved.")
    const result = await fetchPlatformReferenceDomains()
    setDomains(result.items || [])
  }

  async function saveRecord(event) {
    event.preventDefault()
    setSavingRecord(true)
    setRecordNotice("")
    setRecordError("")
    try {
      if (selectedRecord && selectedRecord.domain !== selectedDomain) {
        throw new Error("Selected record no longer belongs to the active domain. Reload the domain and try again.")
      }
      const payload = { ...recordPayload({ ...recordForm, domain: selectedDomain, metadata_json: synchronizedMetadataJson }), domain: selectedDomain }
      const updatePayload = payload
      const result = selectedRecord
        ? await updatePlatformReferenceRecord(selectedRecord.id, updatePayload)
        : await createPlatformReferenceRecord(payload)
      setSelectedRecord(result.record)
      setRecordForm(recordToForm(result.record))
      setRecordNotice("Global reference record saved.")
      await loadRecords(selectedDomain, selectedDomain === "countries" ? filters : defaultRecordFilters)
    } catch (err) {
      setRecordError(err.message)
    } finally {
      setSavingRecord(false)
    }
  }

  async function archiveRecord(record) {
    await archivePlatformReferenceRecord(record.id)
    setNotice("Reference record archived.")
    await loadRecords(record.domain)
  }

  async function runSuggestionAction(suggestion, action) {
    await reviewPlatformReferenceSuggestion(suggestion.id, action, { reviewer_note: `Platform console ${action}.` })
    setNotice(`Suggestion ${action.replace("-", " ")} complete.`)
    const result = await fetchPlatformReferenceSuggestions()
    setSuggestions(result.items || [])
    await loadRecords(selectedDomain)
  }

  async function runImport(event) {
    event.preventDefault()
    const result = await previewPlatformReferenceImport({ domain: selectedDomain, filename: `${selectedDomain}.csv`, csv_text: importCsv, mode: importMode })
    setImportResult(result.preview || result)
    setNotice("Import preview completed.")
  }

  async function applyImport() {
    const result = await applyPlatformReferenceImport({ domain: selectedDomain, filename: `${selectedDomain}.csv`, csv_text: importCsv, mode: importMode })
    setImportResult(result.preview || result)
    setImports((current) => [result.batch, ...current].filter(Boolean))
    const [actionResult, serviceResult] = await Promise.all([
      fetchReferenceActionRequired(),
      fetchPlatformServiceCatalogue({ include_archived: true }),
    ])
    setActionRequired(actionResult.items || [])
    setServiceCatalogue(serviceResult.items || [])
    await loadRecords(selectedDomain)
    setNotice("Import applied.")
  }

  function loadImportTemplateCsv() {
    const columns = [...(selectedImportTemplate?.required_columns || []), ...(selectedImportTemplate?.optional_columns || [])]
    setImportCsv(`${columns.join(",")}\n`)
    setImportResult(null)
  }

  function servicePayloadFromForm() {
    return {
      ...serviceForm,
      service_key: serviceForm.service_key.trim().toUpperCase(),
      label: serviceForm.label.trim(),
      category: serviceForm.category.trim(),
      sort_order: Number(serviceForm.sort_order || 100),
      required_documents_json: JSON.parse(serviceForm.required_documents_json || "[]"),
      required_fields_json: JSON.parse(serviceForm.required_fields_json || "{}"),
      validation_rules_json: JSON.parse(serviceForm.validation_rules_json || "{}"),
    }
  }

  async function saveService(event) {
    event.preventDefault()
    const payload = servicePayloadFromForm()
    if (editingServiceId) {
      await updatePlatformServiceCatalogue(editingServiceId, payload)
      setNotice("Service catalogue record updated.")
    } else {
      await createPlatformServiceCatalogue(payload)
      setNotice("Service catalogue record created.")
    }
    const result = await fetchPlatformServiceCatalogue({ include_archived: true })
    setServiceCatalogue(result.items || [])
    setEditingServiceId(null)
    setServiceForm(emptyServiceForm())
  }

  async function archiveService(service) {
    await archivePlatformServiceCatalogue(service.id)
    setNotice("Service catalogue record archived.")
    const result = await fetchPlatformServiceCatalogue({ include_archived: true })
    setServiceCatalogue(result.items || [])
  }

  function editService(service) {
    setEditingServiceId(service.id)
    setServiceForm(serviceToForm(service))
  }

  async function loadEnrichmentTemplate(templateName) {
    const result = await fetchReferenceEnrichmentTemplate(templateName)
    setEnrichmentForm((current) => ({
      ...current,
      template_name: templateName,
      domain: result.template.domain,
      csv_text: result.csv_text,
    }))
    setEnrichmentReport(null)
    setEnrichmentDryRunOk(false)
  }

  async function runEnrichmentDryRun(event) {
    event.preventDefault()
    const result = await dryRunReferenceEnrichmentImport({
      domain: enrichmentForm.domain,
      csv_text: enrichmentForm.csv_text,
      update_mode: enrichmentForm.update_mode,
      dry_run: true,
      source_label: enrichmentForm.source_label,
      notes: enrichmentForm.notes,
    })
    setEnrichmentReport(result.report)
    setEnrichmentDryRunOk((result.report?.failed || 0) === 0)
    const batches = await fetchReferenceEnrichmentBatches()
    setEnrichmentBatches(batches.items || [])
    setNotice("Enrichment dry run completed.")
  }

  async function commitEnrichmentImport() {
    const result = await commitReferenceEnrichmentImport({
      domain: enrichmentForm.domain,
      csv_text: enrichmentForm.csv_text,
      update_mode: enrichmentForm.update_mode,
      dry_run: false,
      source_label: enrichmentForm.source_label,
      notes: enrichmentForm.notes,
    })
    setEnrichmentReport(result.report)
    setEnrichmentDryRunOk(false)
    const [batches, recordsResult, readinessResult] = await Promise.all([
      fetchReferenceEnrichmentBatches(),
      fetchPlatformReferenceRecords({ domain: enrichmentForm.domain, include_inactive: true }),
      apiGet("/api/readiness"),
    ])
    setEnrichmentBatches(batches.items || [])
    if (enrichmentForm.domain === selectedDomain) {
      setRecords((recordsResult.items || []).filter((record) => record.domain === selectedDomain))
    }
    setReferenceReadiness(readinessResult.platform_reference_console || {})
    setNotice("Enrichment import committed.")
  }

  async function runExport(event) {
    event.preventDefault()
    const result = await exportPlatformReferenceData(exportOptions)
    setExportResult(result)
    setNotice("Export generated.")
  }

  function editRecord(record) {
    if (record.domain !== selectedDomain) {
      setRecordError("This record belongs to a different domain. Reload the selected domain before editing.")
      return
    }
    setRecordNotice("")
    setRecordError("")
    setSelectedRecord(record)
    setRecordForm(recordToForm(record))
    setActiveTab("records")
  }

  return (
    <PlatformLayout user={summary?.current_user}>
      <ProtectedRoute loading={loading} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Platform Reference Data</p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Reference Data Management Console</h2>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">Platform owners manage global records, enriched countries, imports, exports, and agency suggestion review. Agency workspaces remain consume-and-suggest only.</p>
            </div>
            <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-white" href="/agency/reference">Agency reference view</a>
          </div>
          {notice ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div> : null}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Reference Enrichment Quality</h3>
            <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["Countries", referenceReadiness?.enriched_country_record_count, referenceReadiness?.country_record_count],
                ["Airports enriched", referenceReadiness?.enriched_airport_record_count],
                ["Airlines enriched", referenceReadiness?.enriched_airline_record_count],
                ["Currencies enriched", referenceReadiness?.enriched_currency_record_count],
                ["Languages enriched", referenceReadiness?.enriched_language_record_count],
                ["Countries with airports", referenceReadiness?.countries_with_major_airports_count],
                ["Countries with carrier", referenceReadiness?.countries_with_national_carrier_count],
                ["Missing country links", (referenceReadiness?.airports_missing_country_link_count || 0) + (referenceReadiness?.airlines_missing_country_link_count || 0)],
              ].map(([label, value, total]) => (
                <div className="rounded-md bg-slate-50 p-3" key={label}>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
                  <dd className="mt-1 text-2xl font-semibold text-slate-950">{value || 0}{total !== undefined ? <span className="text-sm font-normal text-slate-500"> / {total || 0}</span> : null}</dd>
                </div>
              ))}
            </dl>
          </section>

          <div className="flex flex-wrap gap-2">
            {tabs.map(([key, label]) => (
              <button className={`rounded-full px-3 py-2 text-sm font-semibold ${activeTab === key ? "bg-blue-600 text-white" : "bg-white text-slate-700 hover:bg-slate-50"}`} key={key} type="button" onClick={() => selectTab(key)}>
                {label}
              </button>
            ))}
          </div>

          {activeTab === "domains" ? (
            <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Domains</h3>
                <div className="mt-4 grid gap-3">
                  {domains.map((domain) => (
                    <article className={`rounded-lg border p-4 ${selectedDomain === domain.domain ? "border-blue-300 bg-blue-50/40" : "border-slate-200 bg-white"}`} key={domain.domain}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{domain.label}</p>
                          <p className="text-xs uppercase tracking-wide text-slate-500">{domain.domain} · {domain.category}</p>
                        </div>
                        <StatusBadge status={domain.is_active ? "active" : "inactive"} />
                      </div>
                      <dl className="mt-3 grid grid-cols-4 gap-2 text-xs text-slate-600">
                        <div><dt>Active</dt><dd className="font-semibold text-slate-950">{domain.active_record_count}</dd></div>
                        <div><dt>Inactive</dt><dd className="font-semibold text-slate-950">{domain.inactive_record_count}</dd></div>
                        <div><dt>Suggestions</dt><dd className="font-semibold text-slate-950">{domain.pending_suggestion_count}</dd></div>
                        <div><dt>Actions</dt><dd className="font-semibold text-slate-950">{actionCountByDomain[domain.domain] || 0}</dd></div>
                      </dl>
                      {domainUsageByKey[domain.domain] ? (
                        <div className="mt-3 rounded-md bg-slate-50 p-3 text-xs text-slate-600">
                          <p className="font-medium text-slate-800">{domainUsageByKey[domain.domain].description}</p>
                          <p className="mt-2"><span className="font-semibold">Managed by:</span> {domainUsageByKey[domain.domain].owner_scope} · <span className="font-semibold">Agency:</span> {domainUsageByKey[domain.domain].agency_behavior}</p>
                          <p className="mt-1"><span className="font-semibold">Consumers:</span> {(domainUsageByKey[domain.domain].primary_consumers || []).slice(0, 4).join(", ") || "n/a"}</p>
                          <p className="mt-1"><span className="font-semibold">Workflows:</span> {(domainUsageByKey[domain.domain].used_in_workflows || []).slice(0, 5).join(", ") || "n/a"}</p>
                          <p className="mt-1"><span className="font-semibold">Import:</span> {domainUsageByKey[domain.domain].bulk_import_supported ? domainUsageByKey[domain.domain].import_template_type : "not supported"} · <span className="font-semibold">Enrichment:</span> {domainUsageByKey[domain.domain].enrichment_supported ? "supported" : "not supported"} · <span className="font-semibold">Risk:</span> {domainUsageByKey[domain.domain].missing_data_risk_level}</p>
                        </div>
                      ) : null}
                      <div className="mt-4 flex flex-wrap gap-2">
                        <button className="rounded-md bg-blue-600 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={() => changeDomain(domain.domain, { openRecords: true })}>Open records</button>
                        <button className="rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700" type="button" onClick={() => editDomainMetadata(domain.domain)}>Edit metadata</button>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Create / Edit Domain Metadata</h3>
                <form className="mt-4 grid gap-3" onSubmit={saveDomain}>
                  <Field label="Domain code"><TextInput required value={domainForm.domain} onChange={(event) => setDomainForm((current) => ({ ...current, domain: event.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_") }))} /></Field>
                  <Field label="Label"><TextInput required value={domainForm.label} onChange={(event) => setDomainForm((current) => ({ ...current, label: event.target.value }))} /></Field>
                  <Field label="Description"><textarea className="rounded-md border border-slate-300 px-3 py-2 text-sm" rows={3} value={domainForm.description} onChange={(event) => setDomainForm((current) => ({ ...current, description: event.target.value }))} /></Field>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <Field label="Category"><TextInput value={domainForm.category} onChange={(event) => setDomainForm((current) => ({ ...current, category: event.target.value }))} /></Field>
                    <Field label="Sort order"><TextInput type="number" value={domainForm.sort_order} onChange={(event) => setDomainForm((current) => ({ ...current, sort_order: event.target.value }))} /></Field>
                    <label className="mt-7 flex items-center gap-2 text-sm text-slate-700"><input checked={domainForm.is_active} type="checkbox" onChange={(event) => setDomainForm((current) => ({ ...current, is_active: event.target.checked }))} /> Active</label>
                  </div>
                  <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">Save domain metadata</button>
                </form>
              </section>
            </div>
          ) : null}

          {activeTab === "records" ? (
            <div className="space-y-6">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-wrap items-end gap-3">
                  <Field label="Domain">
                    <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={selectedDomain} onChange={(event) => changeDomain(event.target.value, { openRecords: true })}>
                      {domainOptions.map((domain) => <option key={domain} value={domain}>{domain}</option>)}
                    </select>
                  </Field>
                  {selectedDomainHasCountrySchema ? (
                    <>
                      <Field label="Quality"><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.data_quality_status} onChange={(event) => setFilters((current) => ({ ...current, data_quality_status: event.target.value }))}><option value="">Any</option><option value="draft">Draft</option><option value="verified">Verified</option><option value="needs_review">Needs review</option><option value="deprecated">Deprecated</option></select></Field>
                      <Field label="Continent"><TextInput value={filters.continent} onChange={(event) => setFilters((current) => ({ ...current, continent: event.target.value }))} /></Field>
                      {["missing_iso3", "missing_capital_iata", "missing_currency", "missing_major_airports", "missing_national_carrier"].map((key) => (
                        <label className="mb-2 flex items-center gap-2 text-sm text-slate-700" key={key}><input checked={filters[key]} type="checkbox" onChange={(event) => setFilters((current) => ({ ...current, [key]: event.target.checked }))} /> {key.replaceAll("_", " ")}</label>
                      ))}
                    </>
                  ) : null}
                  <button className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60" type="button" disabled={recordsLoading} onClick={() => loadRecords(selectedDomain)}>Apply filters</button>
                  <button className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" type="button" onClick={() => { setSelectedRecord(null); setRecordForm(emptyRecord(selectedDomain)); setRecordNotice(""); setRecordError("") }}>New record</button>
                </div>
              </section>

              {recordNotice ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{recordNotice}</div> : null}
              {recordError ? <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{recordError}</div> : null}

              <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <section className="rounded-lg border border-slate-200 bg-white p-5" aria-busy={recordsLoading}>
                  <h3 className="font-semibold text-slate-950">Global Records: {selectedDomainLabel}</h3>
                  {recordsLoading ? (
                    <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">Loading {selectedDomainLabel} records...</div>
                  ) : !records.length ? <EmptyState title="No records found" body="Create or import global records for this platform-owned domain." /> : (
                    <div className="mt-4 overflow-x-auto rounded-md border border-slate-200">
                      <table className="min-w-full divide-y divide-slate-200 text-sm">
                        {selectedDomainHasCountrySchema ? (
                          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-3 py-2">{recordCodeColumnLabel}</th><th className="px-3 py-2">Label</th><th className="px-3 py-2">ISO3</th><th className="px-3 py-2">Capital IATA</th><th className="px-3 py-2">Currency</th><th className="px-3 py-2">Quality</th><th className="px-3 py-2">Actions</th></tr></thead>
                        ) : (
                          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-3 py-2">{recordCodeColumnLabel}</th><th className="px-3 py-2">Label</th><th className="px-3 py-2">Aliases</th><th className="px-3 py-2">Description</th><th className="px-3 py-2">Status / Governance</th><th className="px-3 py-2">Actions</th></tr></thead>
                        )}
                        <tbody className="divide-y divide-slate-100">
                          {records.map((record) => (
                            <tr key={record.id}>
                              <td className="px-3 py-2 font-semibold text-slate-950">{record.code}</td>
                              <td className="px-3 py-2 text-slate-700">{record.label}</td>
                              {selectedDomainHasCountrySchema ? (
                                <>
                                  <td className="px-3 py-2 text-slate-600">{record.metadata_json?.iso3_code || "-"}</td>
                                  <td className="px-3 py-2 text-slate-600">{record.metadata_json?.capital_iata_code || "-"}</td>
                                  <td className="px-3 py-2 text-slate-600">{record.metadata_json?.currency_iso_code || "-"}</td>
                                </>
                              ) : (
                                <>
                                  <td className="px-3 py-2 text-slate-600">{(record.aliases || []).join(", ") || "-"}</td>
                                  <td className="px-3 py-2 text-slate-600">{record.description || "-"}</td>
                                </>
                              )}
                              <td className="px-3 py-2"><StatusBadge status={record.metadata_json?.data_quality_status || (record.is_active ? "active" : "inactive")} /></td>
                              <td className="px-3 py-2">
                                <div className="flex gap-2">
                                  <button className="text-blue-700 hover:underline" type="button" onClick={() => editRecord(record)}>Edit</button>
                                  <a className="text-slate-700 hover:underline" href={`/platform/reference/records/${record.id}`}>Card</a>
                                  <button className="text-rose-700 hover:underline" type="button" onClick={() => archiveRecord(record)}>Archive</button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>

                <section className="rounded-lg border border-slate-200 bg-white p-5">
                  <h3 className="font-semibold text-slate-950">{selectedRecord ? "Edit Record" : "Create Record"}</h3>
                  <form className="mt-4 grid gap-3" onSubmit={saveRecord}>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Field label={recordCodeColumnLabel}>
                        <TextInput
                          required
                          maxLength={recordForm.domain === "cities" ? 3 : undefined}
                          value={recordForm.code}
                          onChange={(event) => setRecordField("code", recordForm.domain === "cities" ? event.target.value.toUpperCase() : event.target.value)}
                        />
                      </Field>
                      <Field label={recordForm.domain === "cities" ? "City name" : "Label"}><TextInput required value={recordForm.label} onChange={(event) => setRecordField("label", event.target.value)} /></Field>
                      <Field label={recordForm.domain === "cities" ? "Legacy aliases" : "Aliases"}><TextInput value={recordForm.aliases} onChange={(event) => setRecordField("aliases", event.target.value)} /></Field>
                      <Field label="Sort order"><TextInput type="number" value={recordForm.sort_order} onChange={(event) => setRecordField("sort_order", event.target.value)} /></Field>
                    </div>
                    <Field label="Description"><textarea className="rounded-md border border-slate-300 px-3 py-2 text-sm" rows={2} value={recordForm.description} onChange={(event) => setRecordField("description", event.target.value)} /></Field>
                    <label className="flex items-center gap-2 text-sm text-slate-700"><input checked={recordForm.is_active} type="checkbox" onChange={(event) => setRecordField("is_active", event.target.checked)} /> Active</label>

                    {recordForm.domain === "cities" ? (
                      <div className="grid gap-3 rounded-lg bg-slate-50 p-4 sm:grid-cols-2">
                        <Field label="Country code"><TextInput maxLength={2} value={recordForm.metadata.country_code || ""} onChange={(event) => setMetadataField("country_code", event.target.value.toUpperCase())} /></Field>
                      </div>
                    ) : recordForm.domain === "countries" ? (
                      <div className="grid gap-3 rounded-lg bg-slate-50 p-4 sm:grid-cols-2">
                        <Field label="ISO2"><TextInput maxLength={2} value={recordForm.metadata.iso2_code} onChange={(event) => setMetadataField("iso2_code", event.target.value.toUpperCase())} /></Field>
                        <Field label="ISO3"><TextInput maxLength={3} value={recordForm.metadata.iso3_code} onChange={(event) => setMetadataField("iso3_code", event.target.value.toUpperCase())} /></Field>
                        <Field label="Continent"><TextInput value={recordForm.metadata.continent} onChange={(event) => setMetadataField("continent", event.target.value)} /></Field>
                        <Field label="Capital city"><TextInput value={recordForm.metadata.capital_city} onChange={(event) => setMetadataField("capital_city", event.target.value)} /></Field>
                        <Field label="Capital IATA"><TextInput maxLength={3} value={recordForm.metadata.capital_iata_code} onChange={(event) => setMetadataField("capital_iata_code", event.target.value.toUpperCase())} /></Field>
                        <Field label="Major airports"><TextInput placeholder="SOF, VAR, BOJ" value={recordForm.metadata.major_airports} onChange={(event) => setMetadataField("major_airports", event.target.value.toUpperCase())} /></Field>
                        <Field label="Official languages"><TextInput value={recordForm.metadata.official_languages} onChange={(event) => setMetadataField("official_languages", event.target.value)} /></Field>
                        <Field label="Currency name"><TextInput value={recordForm.metadata.currency_name} onChange={(event) => setMetadataField("currency_name", event.target.value)} /></Field>
                        <Field label="Currency ISO"><TextInput maxLength={3} value={recordForm.metadata.currency_iso_code} onChange={(event) => setMetadataField("currency_iso_code", event.target.value.toUpperCase())} /></Field>
                        <Field label="Population estimate"><TextInput type="number" value={recordForm.metadata.population_estimate} onChange={(event) => setMetadataField("population_estimate", event.target.value)} /></Field>
                        <Field label="Population year"><TextInput type="number" value={recordForm.metadata.population_estimate_year} onChange={(event) => setMetadataField("population_estimate_year", event.target.value)} /></Field>
                        <Field label="National carrier"><TextInput value={recordForm.metadata.national_carrier_name} onChange={(event) => setMetadataField("national_carrier_name", event.target.value)} /></Field>
                        <Field label="National carrier IATA"><TextInput maxLength={2} value={recordForm.metadata.national_carrier_iata_code} onChange={(event) => setMetadataField("national_carrier_iata_code", event.target.value.toUpperCase())} /></Field>
                        {[1, 2, 3].map((index) => (
                          <div className="grid gap-3 sm:col-span-2 sm:grid-cols-[1fr_120px]" key={index}>
                            <Field label={`Major airline ${index}`}><TextInput value={recordForm.metadata[`major_airline_${index}_name`]} onChange={(event) => setMetadataField(`major_airline_${index}_name`, event.target.value)} /></Field>
                            <Field label="IATA"><TextInput maxLength={2} value={recordForm.metadata[`major_airline_${index}_iata_code`]} onChange={(event) => setMetadataField(`major_airline_${index}_iata_code`, event.target.value.toUpperCase())} /></Field>
                          </div>
                        ))}
                        <Field label="Quality status"><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={recordForm.metadata.data_quality_status} onChange={(event) => setMetadataField("data_quality_status", event.target.value)}><option value="draft">Draft</option><option value="verified">Verified</option><option value="needs_review">Needs review</option><option value="deprecated">Deprecated</option></select></Field>
                        <Field label="Source notes"><TextInput value={recordForm.metadata.source_notes} onChange={(event) => setMetadataField("source_notes", event.target.value)} /></Field>
                        <Field label="Travel notes"><textarea className="rounded-md border border-slate-300 px-3 py-2 text-sm" rows={2} value={recordForm.metadata.travel_notes} onChange={(event) => setMetadataField("travel_notes", event.target.value)} /></Field>
                      </div>
                    ) : null}
                    {recordForm.domain === "cities" ? (
                      <Field label="Synchronized advanced metadata JSON">
                        <textarea readOnly className="rounded-md border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-700" rows={8} value={synchronizedMetadataJson} />
                      </Field>
                    ) : recordForm.domain !== "countries" ? (
                      <Field label="Synchronized advanced metadata JSON">
                        <textarea className="rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" rows={8} value={recordForm.metadata_json} onChange={(event) => setRecordField("metadata_json", event.target.value)} />
                      </Field>
                    ) : (
                      <Field label="Synchronized advanced metadata JSON">
                        <textarea readOnly className="rounded-md border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-700" rows={8} value={synchronizedMetadataJson} />
                      </Field>
                    )}
                    <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60" type="submit" disabled={savingRecord}>{savingRecord ? "Saving..." : "Save global record"}</button>
                  </form>
                </section>
              </div>
            </div>
          ) : null}

          {activeTab === "service" ? (
            <div className="grid gap-6 xl:grid-cols-[1fr_420px]">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-slate-950">Service Catalogue Management</h3>
                    <p className="mt-1 text-sm text-slate-600">Platform-owned service records drive request choices, rules/services, SSR/OSI previews, offers, acceptance snapshots, booking readiness, documents, and future EMD readiness.</p>
                  </div>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700" type="button" onClick={() => { setEditingServiceId(null); setServiceForm(emptyServiceForm()) }}>New service</button>
                </div>
                <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                  {serviceCatalogue.map((service) => (
                    <div className="grid gap-3 p-4 lg:grid-cols-[1fr_auto]" key={service.id}>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold text-slate-950">{service.service_key || service.service_code} · {service.label || service.service_label}</p>
                          <StatusBadge status={service.status || (service.is_active ? "active" : "archived")} />
                        </div>
                        <p className="mt-1 text-sm text-slate-600">{service.category || service.service_family_code} · SSR {service.ssr_code || service.default_ssr_code || "manual"} · rules {service.rules_category || "OTHER"} · EMD {service.emd_applicability || "none"}</p>
                        <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                          <span className="rounded-md bg-slate-50 p-2">Request: {service.request_form_enabled ? "enabled" : "hidden"} · {service.requires_segment_scope ? "segment scoped" : "trip scoped"}</span>
                          <span className="rounded-md bg-slate-50 p-2">Rules/SSR: {service.exception_engine_enabled ? "engine" : "manual"} · {service.booking_preview_enabled ? "preview" : "no preview"}</span>
                          <span className="rounded-md bg-slate-50 p-2">Offer/readiness: {service.offer_feasibility_enabled ? "feasibility" : "manual"} · {service.booking_readiness_enabled ? "readiness" : "excluded"}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 lg:justify-end">
                        <button className="rounded-md bg-blue-600 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={() => editService(service)}>Edit</button>
                        <button className="rounded-md border border-rose-300 px-3 py-2 text-xs font-semibold text-rose-700" type="button" onClick={() => archiveService(service)}>Archive</button>
                      </div>
                    </div>
                  ))}
                  {!serviceCatalogue.length ? <div className="p-5"><EmptyState title="No service catalogue records" body="Create operational service records for request, rules, offer, and readiness workflows." /></div> : null}
                </div>
              </section>
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">{editingServiceId ? "Edit Service" : "Create Service"}</h3>
                <form className="mt-4 grid gap-3" onSubmit={saveService}>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Field label="Service key"><TextInput required value={serviceForm.service_key} onChange={(event) => setServiceForm((current) => ({ ...current, service_key: event.target.value.toUpperCase() }))} /></Field>
                    <Field label="Label"><TextInput required value={serviceForm.label} onChange={(event) => setServiceForm((current) => ({ ...current, label: event.target.value }))} /></Field>
                    <Field label="Category"><TextInput required value={serviceForm.category} onChange={(event) => setServiceForm((current) => ({ ...current, category: event.target.value }))} /></Field>
                    <Field label="Subcategory"><TextInput value={serviceForm.subcategory || ""} onChange={(event) => setServiceForm((current) => ({ ...current, subcategory: event.target.value }))} /></Field>
                    <Field label="Status"><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={serviceForm.status} onChange={(event) => setServiceForm((current) => ({ ...current, status: event.target.value }))}><option value="draft">Draft</option><option value="active">Active</option><option value="deprecated">Deprecated</option><option value="archived">Archived</option></select></Field>
                    <Field label="Sort order"><TextInput type="number" value={serviceForm.sort_order} onChange={(event) => setServiceForm((current) => ({ ...current, sort_order: event.target.value }))} /></Field>
                  </div>
                  <Field label="Description"><textarea className="rounded-md border border-slate-300 px-3 py-2 text-sm" rows={2} value={serviceForm.description || ""} onChange={(event) => setServiceForm((current) => ({ ...current, description: event.target.value }))} /></Field>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Field label="SSR code"><TextInput value={serviceForm.ssr_code || ""} onChange={(event) => setServiceForm((current) => ({ ...current, ssr_code: event.target.value.toUpperCase() }))} /></Field>
                    <Field label="Rules category"><TextInput value={serviceForm.rules_category || ""} onChange={(event) => setServiceForm((current) => ({ ...current, rules_category: event.target.value.toUpperCase() }))} /></Field>
                    <Field label="Default service type"><TextInput value={serviceForm.default_service_type || ""} onChange={(event) => setServiceForm((current) => ({ ...current, default_service_type: event.target.value.toUpperCase() }))} /></Field>
                    <Field label="EMD applicability"><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={serviceForm.emd_applicability} onChange={(event) => setServiceForm((current) => ({ ...current, emd_applicability: event.target.value }))}><option value="none">None</option><option value="optional">Optional</option><option value="required">Required</option><option value="conditional">Conditional</option></select></Field>
                  </div>
                  <div className="grid gap-2 rounded-md bg-slate-50 p-3 text-sm text-slate-700">
                    {[
                      ["request_form_enabled", "Request form"],
                      ["exception_engine_enabled", "Rules/services"],
                      ["booking_preview_enabled", "SSR/OSI preview"],
                      ["offer_feasibility_enabled", "Offer feasibility"],
                      ["offer_pricing_enabled", "Offer pricing"],
                      ["acceptance_snapshot_enabled", "Acceptance snapshot"],
                      ["booking_readiness_enabled", "Booking readiness"],
                      ["requires_passenger_scope", "Passenger scope"],
                      ["requires_segment_scope", "Segment scope"],
                    ].map(([key, label]) => <label className="flex items-center gap-2" key={key}><input checked={Boolean(serviceForm[key])} type="checkbox" onChange={(event) => setServiceForm((current) => ({ ...current, [key]: event.target.checked }))} /> {label}</label>)}
                  </div>
                  <Field label="Required documents JSON"><textarea className="rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" rows={4} value={serviceForm.required_documents_json} onChange={(event) => setServiceForm((current) => ({ ...current, required_documents_json: event.target.value }))} /></Field>
                  <Field label="Required fields JSON"><textarea className="rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" rows={4} value={serviceForm.required_fields_json} onChange={(event) => setServiceForm((current) => ({ ...current, required_fields_json: event.target.value }))} /></Field>
                  <Field label="Validation rules JSON"><textarea className="rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" rows={4} value={serviceForm.validation_rules_json} onChange={(event) => setServiceForm((current) => ({ ...current, validation_rules_json: event.target.value }))} /></Field>
                  <Field label="Internal handling notes"><textarea className="rounded-md border border-slate-300 px-3 py-2 text-sm" rows={2} value={serviceForm.internal_handling_notes || ""} onChange={(event) => setServiceForm((current) => ({ ...current, internal_handling_notes: event.target.value }))} /></Field>
                  <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">{editingServiceId ? "Save service" : "Create service"}</button>
                </form>
              </section>
            </div>
          ) : null}

          {activeTab === "suggestions" ? (
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Agency Suggestion Review Queue</h3>
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {suggestions.map((suggestion) => (
                  <div className="grid gap-3 p-4 lg:grid-cols-[1fr_auto]" key={suggestion.id}>
                    <div>
                      <p className="font-semibold text-slate-950">{suggestion.domain}:{suggestion.suggested_code || "new"} · {suggestion.suggested_label}</p>
                      <p className="text-sm text-slate-600">{suggestion.agency_name || suggestion.submitting_agency_id} · {suggestion.suggestion_type} · {suggestion.evidence_note || "No evidence note"}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <StatusBadge status={suggestion.status} />
                      <button className="rounded-md bg-emerald-600 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={() => runSuggestionAction(suggestion, "approve")}>Approve</button>
                      <button className="rounded-md bg-amber-500 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={() => runSuggestionAction(suggestion, "request-info")}>Request info</button>
                      <button className="rounded-md bg-rose-600 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={() => runSuggestionAction(suggestion, "reject")}>Reject</button>
                      <button className="rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700" type="button" onClick={() => runSuggestionAction(suggestion, "archive")}>Archive</button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {activeTab === "import" ? (
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Domain-Aware Bulk Import</h3>
              <p className="mt-1 text-sm text-slate-600">Imports use per-domain templates with required columns, validation rules, duplicate handling, preview, and explicit apply.</p>
              <div className="mt-4 rounded-md bg-slate-50 p-4 text-sm text-slate-700">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-slate-950">{selectedImportTemplate?.label || selectedDomainLabel}</p>
                    <p className="mt-1">Required: {(selectedImportTemplate?.required_columns || []).join(", ") || "No template"}</p>
                    <p className="mt-1">Optional: {(selectedImportTemplate?.optional_columns || []).join(", ") || "n/a"}</p>
                    <p className="mt-1">Duplicate handling: {selectedImportTemplate?.duplicate_handling || "n/a"} · Code normalization: {selectedImportTemplate?.code_normalization || "n/a"}</p>
                  </div>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700" type="button" onClick={loadImportTemplateCsv}>Load header</button>
                </div>
              </div>
              <form className="mt-4 grid gap-3" onSubmit={runImport}>
                <div className="flex flex-wrap items-end gap-3">
                  <Field label="Domain">
                    <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={selectedDomain} onChange={(event) => changeDomain(event.target.value)}>
                      {importTemplates.map((template) => <option key={template.domain_key} value={template.domain_key}>{template.label}</option>)}
                    </select>
                  </Field>
                  <Field label="Mode">
                    <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={importMode} onChange={(event) => setImportMode(event.target.value)}>
                      <option value="upsert">Upsert</option>
                      <option value="create_only">Create only</option>
                      <option value="update_existing">Update existing</option>
                    </select>
                  </Field>
                </div>
                <textarea className="min-h-56 rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" value={importCsv} onChange={(event) => setImportCsv(event.target.value)} />
                <div className="flex flex-wrap gap-2">
                  <button className="w-fit rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">Preview import</button>
                  <button className="w-fit rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white" type="button" onClick={applyImport}>Apply import</button>
                </div>
              </form>
              {importResult ? (
                <div className="mt-5 grid gap-4 lg:grid-cols-[240px_1fr]">
                  <div className="rounded-lg bg-slate-50 p-4">
                    <h4 className="font-semibold text-slate-950">Import Summary</h4>
                    <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                      {["created", "updated", "skipped", "errors"].map((key) => <div key={key}><dt className="text-xs uppercase tracking-wide text-slate-500">{key}</dt><dd className="text-2xl font-semibold text-slate-950">{importResult.summary?.[key] || 0}</dd></div>)}
                    </dl>
                  </div>
                  <div className="max-h-72 overflow-auto rounded-md border border-slate-200">
                    <table className="min-w-full divide-y divide-slate-200 text-sm">
                      <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-3 py-2">Row</th><th className="px-3 py-2">Code</th><th className="px-3 py-2">Label</th><th className="px-3 py-2">Action</th><th className="px-3 py-2">Errors</th></tr></thead>
                      <tbody className="divide-y divide-slate-100">
                        {(importResult.rows || []).map((row) => <tr key={`${row.row_number}-${row.code}`}><td className="px-3 py-2">{row.row_number}</td><td className="px-3 py-2 font-semibold">{row.code}</td><td className="px-3 py-2">{row.label}</td><td className="px-3 py-2">{row.action}</td><td className="px-3 py-2 text-slate-600">{(row.errors || []).join(" · ") || "-"}</td></tr>)}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : null}
              <div className="mt-5 grid gap-2 text-sm">
                {imports.slice(0, 8).map((batch) => <div className="rounded-md bg-slate-50 p-3" key={batch.id}>{batch.domain} · {batch.status} · valid {batch.valid_rows} · invalid {batch.invalid_rows} · inserted {batch.inserted_count} · updated {batch.updated_count}</div>)}
              </div>
            </section>
          ) : null}

          {activeTab === "enrichment" ? (
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-slate-950">Enrichment Packs</h3>
                  <p className="mt-1 text-sm text-slate-600">Enrichment Packs update selected reference domains with operational metadata used by workflows such as requests, offers, rules, offer acceptance, booking readiness, and documents.</p>
                </div>
                <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700" href="/agency/reference">Agency view stays read/suggest</a>
              </div>
              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                {enrichmentPacks.map((pack) => (
                  <article className="rounded-lg border border-slate-200 p-4" key={pack.id || pack.pack_key}>
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold text-slate-950">{pack.label}</p>
                        <p className="text-xs uppercase tracking-wide text-slate-500">{pack.pack_key} · {pack.target_domain}</p>
                      </div>
                      <StatusBadge status={pack.status} />
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{pack.description}</p>
                    <p className="mt-2 text-xs text-slate-500">Fields: {(pack.fields_added_or_updated || []).join(", ") || "n/a"}</p>
                    <p className="mt-1 text-xs text-slate-500">Workflow impact: {(pack.workflow_impact || []).join(", ") || "reference governance"}</p>
                  </article>
                ))}
              </div>
              <form className="mt-4 grid gap-4" onSubmit={runEnrichmentDryRun}>
                <div className="grid gap-3 lg:grid-cols-[220px_220px_1fr_auto]">
                  <Field label="Pack type">
                    <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={enrichmentForm.template_name} onChange={(event) => {
                      const selected = enrichmentTemplates.find((item) => item.template_name === event.target.value)
                      setEnrichmentForm((current) => ({ ...current, template_name: event.target.value, domain: selected?.domain || current.domain }))
                      setEnrichmentDryRunOk(false)
                    }}>
                      {enrichmentTemplates.map((template) => <option key={template.template_name} value={template.template_name}>{template.label}</option>)}
                    </select>
                  </Field>
                  <Field label="Update mode">
                    <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={enrichmentForm.update_mode} onChange={(event) => { setEnrichmentForm((current) => ({ ...current, update_mode: event.target.value })); setEnrichmentDryRunOk(false) }}>
                      <option value="insert_only">Insert only</option>
                      <option value="update_missing_only">Update missing only</option>
                      <option value="update_all_non_verified">Update all non-verified</option>
                      <option value="force_update">Force update</option>
                    </select>
                  </Field>
                  <Field label="Source label"><TextInput value={enrichmentForm.source_label} onChange={(event) => setEnrichmentForm((current) => ({ ...current, source_label: event.target.value }))} /></Field>
                  <button className="mt-6 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700" type="button" onClick={() => loadEnrichmentTemplate(enrichmentForm.template_name)}>Load template</button>
                </div>
                <Field label="Notes"><TextInput value={enrichmentForm.notes} onChange={(event) => setEnrichmentForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
                <textarea className="min-h-72 rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" placeholder="Load a template or paste enrichment CSV text here." value={enrichmentForm.csv_text} onChange={(event) => { setEnrichmentForm((current) => ({ ...current, csv_text: event.target.value })); setEnrichmentDryRunOk(false) }} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">Dry run</button>
                  <button className={`rounded-md px-4 py-2 text-sm font-semibold ${enrichmentDryRunOk ? "bg-emerald-600 text-white" : "cursor-not-allowed bg-slate-200 text-slate-500"}`} disabled={!enrichmentDryRunOk} type="button" onClick={commitEnrichmentImport}>Commit import</button>
                </div>
              </form>
              {enrichmentReport ? (
                <div className="mt-5 grid gap-4 lg:grid-cols-[280px_1fr]">
                  <div className="rounded-lg bg-slate-50 p-4">
                    <h4 className="font-semibold text-slate-950">Report</h4>
                    <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                      {["inserted", "updated", "skipped", "failed"].map((key) => <div key={key}><dt className="text-xs uppercase tracking-wide text-slate-500">{key}</dt><dd className="text-2xl font-semibold text-slate-950">{enrichmentReport[key] || 0}</dd></div>)}
                    </dl>
                    <p className="mt-3 text-xs text-slate-500">Mode: {enrichmentReport.update_mode} · {enrichmentReport.dry_run ? "dry run" : "committed"}</p>
                  </div>
                  <div className="space-y-3">
                    {enrichmentReport.warnings?.length ? <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"><strong>Warnings:</strong> {enrichmentReport.warnings.join(" · ")}</div> : null}
                    {enrichmentReport.missing_links?.length ? <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800"><strong>Missing links:</strong> {enrichmentReport.missing_links.join(", ")}</div> : null}
                    <div className="max-h-80 overflow-auto rounded-md border border-slate-200">
                      <table className="min-w-full divide-y divide-slate-200 text-sm">
                        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-3 py-2">Row</th><th className="px-3 py-2">Code</th><th className="px-3 py-2">Action</th><th className="px-3 py-2">Issues</th></tr></thead>
                        <tbody className="divide-y divide-slate-100">
                          {(enrichmentReport.rows || []).map((row) => <tr key={`${row.row_number}-${row.code}`}><td className="px-3 py-2">{row.row_number}</td><td className="px-3 py-2 font-semibold">{row.code}</td><td className="px-3 py-2">{row.action}</td><td className="px-3 py-2 text-slate-600">{[...(row.errors || []), ...(row.warnings || [])].join(" · ") || "—"}</td></tr>)}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : null}
              <div className="mt-5">
                <h4 className="font-semibold text-slate-950">Enrichment Batch History</h4>
                <div className="mt-3 grid gap-2 text-sm">
                  {enrichmentBatches.slice(0, 8).map((batch) => {
                    const report = batch.error_report_json?.enrichment || {}
                    return <div className="rounded-md bg-slate-50 p-3" key={batch.id}>{batch.domain} · {batch.status} · {report.update_mode || "n/a"} · inserted {report.inserted || 0} · updated {report.updated || 0} · failed {report.failed || 0}</div>
                  })}
                </div>
              </div>
            </section>
          ) : null}

          {activeTab === "export" ? (
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Bulk Export</h3>
              <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={runExport}>
                <Field label="Export type"><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={exportOptions.export_type} onChange={(event) => setExportOptions((current) => ({ ...current, export_type: event.target.value }))}><option value="domain">Domain records</option><option value="service_catalogue">Service catalogue</option><option value="suggestions">Suggestions</option><option value="import_batches">Import batches</option></select></Field>
                <Field label="Domain"><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={exportOptions.domain} onChange={(event) => setExportOptions((current) => ({ ...current, domain: event.target.value }))}>{domainOptions.map((domain) => <option key={domain} value={domain}>{domain}</option>)}</select></Field>
                <Field label="Format"><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={exportOptions.format} onChange={(event) => setExportOptions((current) => ({ ...current, format: event.target.value }))}><option value="csv">CSV</option><option value="json">JSON</option></select></Field>
                <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">Generate export</button>
              </form>
              {exportResult ? <textarea readOnly className="mt-4 min-h-72 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" value={exportResult.content || ""} /> : null}
            </section>
          ) : null}

          {activeTab === "health" ? (
            <div className="space-y-6">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-slate-950">Reference Health & Action Required</h3>
                    <p className="mt-1 text-sm text-slate-600">Records appear here only when explicit health logic identifies missing metadata, active workflow use, review needs, pinned status, recent changes, or high-risk operational domains.</p>
                  </div>
                  <StatusBadge status={referenceHealth?.important_records_replaced ? "important records replaced" : "health"} />
                </div>
                <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {(referenceHealth?.sections || []).map((section) => (
                    <div className="rounded-md bg-slate-50 p-3" key={section.key}>
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{section.label || section.key.replaceAll("_", " ")}</dt>
                      <dd className="mt-1 text-2xl font-semibold text-slate-950">{(section.items || []).length}</dd>
                    </div>
                  ))}
                </dl>
              </section>
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Action Required</h3>
                <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                  {actionRequired.map((item) => (
                    <div className="grid gap-3 p-4 lg:grid-cols-[1fr_auto]" key={`${item.domain}-${item.record_id}-${item.reason}`}>
                      <div>
                        <p className="font-semibold text-slate-950">{item.domain}:{item.code || item.record_id} · {item.label}</p>
                        <p className="mt-1 text-sm text-slate-600">{item.reason}</p>
                        <p className="mt-1 text-xs text-slate-500">Impact: {item.consumer_impact}</p>
                        <p className="mt-1 text-xs text-slate-500">Recommended action: {item.recommended_action}</p>
                      </div>
                      <StatusBadge status={item.severity} />
                    </div>
                  ))}
                  {!actionRequired.length ? <div className="p-5"><EmptyState title="No action-required records" body="Reference health did not find missing metadata, review, pinned, recent, or active-workflow issues." /></div> : null}
                </div>
              </section>
            </div>
          ) : null}

          {activeTab === "audit" ? (
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Audit / Update History</h3>
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {visibleAuditEvents.map((event) => <div className="p-4 text-sm" key={event.id}><p className="font-semibold text-slate-950">{event.event_type}</p><p className="text-slate-600">{event.summary}</p><p className="text-xs text-slate-400">{event.created_at}</p></div>)}
              </div>
            </section>
          ) : null}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
