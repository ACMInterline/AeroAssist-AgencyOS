const DEMO_EMAIL_KEY = "aeroassist.demoEmail"

export function getDemoEmail() {
  return localStorage.getItem(DEMO_EMAIL_KEY) || "owner@aeroassist.dev"
}

export function setDemoEmail(email) {
  localStorage.setItem(DEMO_EMAIL_KEY, email)
}

export function authHeaders() {
  return {
    "Content-Type": "application/json",
    "X-Demo-User-Email": getDemoEmail(),
  }
}
