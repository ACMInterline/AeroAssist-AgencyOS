const AUTH_SESSION_KEY = "aeroassist.authSession"
const AUTH_CONTEXT_KEY = "aeroassist.authContext"
const DEMO_EMAIL_KEY = "aeroassist.demoEmail"
const DEMO_PORTAL_EMAIL_KEY = "aeroassist.demoPortalEmail"
const isProduction = import.meta.env.PROD || import.meta.env.VITE_APP_ENV === "production"

export function getAuthSession() {
  const raw = localStorage.getItem(AUTH_SESSION_KEY)
  return raw ? JSON.parse(raw) : null
}

export function setAuthSession(session, auth) {
  localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(session))
  localStorage.setItem(AUTH_CONTEXT_KEY, JSON.stringify(auth))
}

export function getAuthContext() {
  const raw = localStorage.getItem(AUTH_CONTEXT_KEY)
  return raw ? JSON.parse(raw) : null
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_SESSION_KEY)
  localStorage.removeItem(AUTH_CONTEXT_KEY)
}

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
  const headers = {
    "Content-Type": "application/json",
  }
  if (!isProduction) {
    headers["X-Demo-User-Email"] = getDemoEmail()
    headers["X-Demo-Role"] = "portal_client"
    headers["X-Demo-Client-Email"] = getDemoPortalEmail()
  }
  const session = getAuthSession()
  if (session?.access_token) {
    headers.Authorization = `${session.token_type || "bearer"} ${session.access_token}`
  }
  return headers
}
