import { apiGet } from "./api"

const SELECTED_AGENCY_KEY = "aeroassist.selectedAgencyId"

export function selectedAgencyIdFromUrl() {
  return new URLSearchParams(window.location.search).get("agency_id")
}

export function rememberSelectedAgency(agencyId) {
  if (agencyId) {
    window.localStorage.setItem(SELECTED_AGENCY_KEY, agencyId)
  }
}

export async function loadCurrentAgency() {
  const me = await apiGet("/api/auth/me")
  const agencies = await apiGet("/api/agencies")
  const requestedAgencyId = selectedAgencyIdFromUrl() || window.localStorage.getItem(SELECTED_AGENCY_KEY)
  const agency = agencies.items.find((item) => item.id === requestedAgencyId) || agencies.items[0]
  if (!agency) {
    return { me, agency: null }
  }
  rememberSelectedAgency(agency.id)
  return { me, agency }
}
