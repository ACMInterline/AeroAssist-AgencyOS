import { apiGet, apiPost, apiPut } from "./api"

function withQuery(path, params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value))
    }
  })
  const suffix = search.toString() ? `?${search.toString()}` : ""
  return `${path}${suffix}`
}

export function fetchPlatformReferenceDomains() {
  return apiGet("/api/platform/reference/domains")
}

export function savePlatformReferenceDomain(domain, payload) {
  return apiPut(`/api/platform/reference/domains/${encodeURIComponent(domain)}`, payload)
}

export function fetchPlatformReferenceRecords(params = {}) {
  return apiGet(withQuery("/api/platform/reference/records", params))
}

export function fetchPlatformReferenceRecord(recordId) {
  return apiGet(`/api/platform/reference/records/${recordId}`)
}

export function createPlatformReferenceRecord(payload) {
  return apiPost("/api/platform/reference/records", payload)
}

export function updatePlatformReferenceRecord(recordId, payload) {
  return apiPut(`/api/platform/reference/records/${recordId}`, payload)
}

export function archivePlatformReferenceRecord(recordId) {
  return apiPost(`/api/platform/reference/records/${recordId}/archive`, {})
}

export function fetchPlatformReferenceSuggestions(params = {}) {
  return apiGet(withQuery("/api/platform/reference/suggestions", params))
}

export function reviewPlatformReferenceSuggestion(suggestionId, action, payload = {}) {
  return apiPost(`/api/platform/reference/suggestions/${suggestionId}/${action}`, payload)
}

export function importPlatformReferenceCsv(payload) {
  return apiPost("/api/platform/reference/import", payload)
}

export function fetchPlatformReferenceImportBatches() {
  return apiGet("/api/platform/reference/import-batches")
}

export function exportPlatformReferenceData(params = {}) {
  return apiGet(withQuery("/api/platform/reference/export", params))
}

export function fetchReferenceEnrichmentTemplates() {
  return apiGet("/api/platform/reference/enrichment/templates")
}

export function fetchReferenceEnrichmentTemplate(templateName) {
  return apiGet(`/api/platform/reference/enrichment/template/${encodeURIComponent(templateName)}`)
}

export function dryRunReferenceEnrichmentImport(payload) {
  return apiPost("/api/platform/reference/enrichment/dry-run", payload)
}

export function commitReferenceEnrichmentImport(payload) {
  return apiPost("/api/platform/reference/enrichment/import", payload)
}

export function fetchReferenceEnrichmentBatches() {
  return apiGet("/api/platform/reference/enrichment/batches")
}
