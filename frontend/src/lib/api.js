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
    throw new Error(data.detail || data.message || "Download failed")
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
    const error = new Error(data.detail || data.message || "Request failed")
    error.status = response.status
    throw error
  }
  return data
}
