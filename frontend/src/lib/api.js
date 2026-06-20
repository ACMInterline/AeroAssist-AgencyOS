import { authHeaders } from "./auth"

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

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

async function readResponse(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || data.message || "Request failed")
  }
  return data
}
