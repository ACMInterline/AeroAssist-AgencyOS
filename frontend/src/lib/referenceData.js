import { apiGet, apiPatch, apiPost, apiPut } from "./api"

export function fetchReferenceDomains() {
  return apiGet("/api/reference/domains")
}

export function fetchReferenceDomain(domain, includeInactive = false) {
  return apiGet(`/api/reference/${domain}?include_inactive=${includeInactive ? "true" : "false"}`)
}

export function searchReferenceDomain(domain, query, includeInactive = false) {
  return apiGet(`/api/reference/${domain}/search?q=${encodeURIComponent(query)}&include_inactive=${includeInactive ? "true" : "false"}`)
}

export function createReferenceRecord(domain, payload) {
  return apiPost(`/api/reference/${domain}`, payload)
}

export function updateReferenceRecord(domain, recordId, payload) {
  return apiPut(`/api/reference/${domain}/${recordId}`, payload)
}

export function activateReferenceRecord(domain, recordId) {
  return apiPatch(`/api/reference/${domain}/${recordId}/activate`, {})
}

export function deactivateReferenceRecord(domain, recordId) {
  return apiPatch(`/api/reference/${domain}/${recordId}/deactivate`, {})
}

export function submitReferenceSuggestion(payload) {
  return apiPost("/api/reference/suggestions", payload)
}

export function fetchReferenceSuggestions(params = {}) {
  const search = new URLSearchParams()
  if (params.status) search.set("status", params.status)
  if (params.agency_id) search.set("agency_id", params.agency_id)
  const suffix = search.toString() ? `?${search.toString()}` : ""
  return apiGet(`/api/reference/suggestions${suffix}`)
}

export function approveReferenceSuggestion(suggestionId, payload = {}) {
  return apiPatch(`/api/reference/suggestions/${suggestionId}/approve`, payload)
}

export function rejectReferenceSuggestion(suggestionId, payload = {}) {
  return apiPatch(`/api/reference/suggestions/${suggestionId}/reject`, payload)
}

export function requestReferenceSuggestionInfo(suggestionId, payload = {}) {
  return apiPatch(`/api/reference/suggestions/${suggestionId}/needs-more-information`, payload)
}

export function archiveReferenceSuggestion(suggestionId, payload = {}) {
  return apiPatch(`/api/reference/suggestions/${suggestionId}/archive`, payload)
}

export function createReferenceImportBatch(payload) {
  return apiPost("/api/reference/import-batches", payload)
}

export function fetchReferenceImportBatches() {
  return apiGet("/api/reference/import-batches")
}

export function fetchServiceCatalogue(includeInactive = false) {
  return apiGet(`/api/reference/service-catalogue?include_inactive=${includeInactive ? "true" : "false"}`)
}

export function searchServiceCatalogue(query, includeInactive = false) {
  return apiGet(`/api/reference/service-catalogue/search?q=${encodeURIComponent(query)}&include_inactive=${includeInactive ? "true" : "false"}`)
}
