const DEMO_EMAIL_KEY = "aeroassist.demoEmail"
const DEMO_PORTAL_EMAIL_KEY = "aeroassist.demoPortalEmail"

export function getDemoEmail() {
  return localStorage.getItem(DEMO_EMAIL_KEY) || "owner@aeroassist.dev"
}

export function setDemoEmail(email) {
  localStorage.setItem(DEMO_EMAIL_KEY, email)
}

export function getDemoPortalEmail() {
  return localStorage.getItem(DEMO_PORTAL_EMAIL_KEY) || "anna.client@example.com"
}

export function setDemoPortalEmail(email) {
  localStorage.setItem(DEMO_PORTAL_EMAIL_KEY, email)
}

export function authHeaders() {
  return {
    "Content-Type": "application/json",
    "X-Demo-User-Email": getDemoEmail(),
    "X-Demo-Role": "portal_client",
    "X-Demo-Client-Email": getDemoPortalEmail(),
  }
}
