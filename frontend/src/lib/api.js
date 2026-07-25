import { authHeaders } from "./auth"

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD || import.meta.env.VITE_APP_ENV === "production" ? "" : "http://localhost:8000")

export async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(),
  })
  return readResponse(response)
}

export async function apiPost(path, body = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  })
  return readResponse(response)
}

export async function apiDeleteSession() {
  const response = await fetch(`${API_BASE}/api/auth/logout`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
  return readResponse(response)
}

export async function apiDelete(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: authHeaders(),
  })
  return readResponse(response)
}

export async function apiPut(path, body = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(body),
  })
  return readResponse(response)
}

export async function apiPatch(path, body = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify(body),
  })
  return readResponse(response)
}

export async function apiDownload(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw responseError(response, data)
  }
  const blob = await response.blob()
  const disposition = response.headers.get("Content-Disposition") || ""
  const match = disposition.match(/filename="?([^";]+)"?/)
  const filename = match?.[1] || "download"
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

async function readResponse(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw responseError(response, data)
  }
  return data
}

function responseError(response, data) {
  const correlationId = response.headers.get("X-Correlation-ID") || response.headers.get("X-Request-ID") || ""
  const message = safeErrorMessage(data, response.status)
  const error = new Error(correlationId ? `${message} Reference: ${correlationId}.` : message)
  error.status = response.status
  error.code = data?.error?.code || data?.code || statusCode(response.status)
  error.correlationId = correlationId
  return error
}

const DEFAULT_STATUS_MESSAGES = {
  400: "Check the information and try again.",
  401: "Sign in again to continue.",
  403: "You do not have access to complete this action.",
  404: "The requested record could not be found.",
  409: "This record changed or the action conflicts with its current status. Refresh and review it before trying again.",
  422: "Check the highlighted information and try again.",
  429: "Too many attempts were made. Wait a moment before trying again.",
  500: "AeroAssist could not complete the request. Your existing work has not been changed.",
  502: "A required service is temporarily unavailable. Try again shortly.",
  503: "AeroAssist is temporarily unavailable. Try again shortly.",
}

const UNSAFE_ERROR_PATTERN = /(traceback|pymongo|mongodb|mongoerror|duplicate key|e11000|objectid|collection[:\s]|\/users\/|\/var\/|\/opt\/|\/app\/backend)/i

function statusCode(status) {
  if (status === 401) return "authentication_required"
  if (status === 403) return "authorization_denied"
  if (status === 404) return "not_found"
  if (status === 409) return "conflict"
  if (status === 422) return "validation_error"
  if (status === 429) return "throttled"
  return status >= 500 ? "unexpected_error" : "request_failed"
}

function safeErrorMessage(data, status) {
  const detail = data?.detail
  let message = data?.error?.message || data?.message || ""
  if (!message && typeof detail === "string") message = detail
  if (!message && detail && !Array.isArray(detail) && typeof detail === "object") {
    message = detail.message || ""
  }
  if (!message && Array.isArray(detail)) {
    const fields = detail
      .map((item) => Array.isArray(item?.loc) ? item.loc.filter((part) => !["body", "query", "path"].includes(part)).join(".") : "")
      .filter(Boolean)
    message = fields.length
      ? `Check ${[...new Set(fields)].slice(0, 3).join(", ")} and try again.`
      : DEFAULT_STATUS_MESSAGES[422]
  }
  const fallback = DEFAULT_STATUS_MESSAGES[status] || DEFAULT_STATUS_MESSAGES[500]
  const normalized = String(message || fallback).trim()
  return !normalized || UNSAFE_ERROR_PATTERN.test(normalized) ? fallback : normalized
}
