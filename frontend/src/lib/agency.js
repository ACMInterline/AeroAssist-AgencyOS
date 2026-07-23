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

export async function loadCurrentAgency({ suppressOnboardingRedirect = false } = {}) {
  const me = await apiGet("/api/auth/me")
  const agencies = await apiGet("/api/agencies")
  const requestedAgencyId = selectedAgencyIdFromUrl() || window.localStorage.getItem(SELECTED_AGENCY_KEY)
  const agency = agencies.items.find((item) => item.id === requestedAgencyId) || agencies.items[0]
  if (!agency) {
    return { me, agency: null }
  }
  rememberSelectedAgency(agency.id)
  if (!suppressOnboardingRedirect && window.location.pathname.startsWith("/agency") && window.location.pathname !== "/agency/onboarding") {
    const onboarding = await apiGet(`/api/agencies/${agency.id}/onboarding`)
    if (onboarding.required) {
      window.location.replace(`/agency/onboarding?agency_id=${agency.id}`)
      return { me, agency, onboardingRedirect: true }
    }
  }
  try {
    const branding = await apiGet(`/api/agencies/${agency.id}/branding`)
    return { me, agency: { ...agency, branding: branding.branding, computed_theme: branding.computed_theme, design_options: branding.design_options } }
  } catch {
    return { me, agency }
  }
}
