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

export function fetchServiceCatalogue(includeInactive = false) {
  return apiGet(`/api/reference/service-catalogue?include_inactive=${includeInactive ? "true" : "false"}`)
}

export function searchServiceCatalogue(query, includeInactive = false) {
  return apiGet(`/api/reference/service-catalogue/search?q=${encodeURIComponent(query)}&include_inactive=${includeInactive ? "true" : "false"}`)
}
