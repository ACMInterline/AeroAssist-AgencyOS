import { apiGet, apiPost, apiPut } from "./api"

export function fetchGlobalFieldDefinitions(includeInactive = false) {
  return apiGet(`/api/form-profiles/field-definitions?include_inactive=${includeInactive ? "true" : "false"}`)
}

export function bootstrapGlobalFieldDefinitions() {
  return apiPost("/api/form-profiles/field-definitions/bootstrap", {})
}

export function fetchAgencyFormProfiles(agencyId) {
  return apiGet(`/api/agencies/${agencyId}/form-profiles`)
}

export function createAgencyFormProfile(agencyId, payload) {
  return apiPost(`/api/agencies/${agencyId}/form-profiles`, payload)
}

export function updateAgencyFormProfile(agencyId, profileId, payload) {
  return apiPut(`/api/agencies/${agencyId}/form-profiles/${profileId}`, payload)
}

export function fetchEffectiveAgencyFormProfile(agencyId, profileId) {
  return apiGet(`/api/agencies/${agencyId}/form-profiles/${profileId}/effective`)
}

export function updateAgencyFormProfileFields(agencyId, profileId, fields) {
  return apiPut(`/api/agencies/${agencyId}/form-profiles/${profileId}/fields`, { fields })
}

export function fetchPublicEffectiveFormProfile(agencyId, formContext = "public_request") {
  return apiGet(`/api/public/form-profiles/effective?agency_id=${encodeURIComponent(agencyId)}&form_context=${encodeURIComponent(formContext)}`)
}
