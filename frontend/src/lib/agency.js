import { apiGet } from "./api"

export async function loadCurrentAgency() {
  const me = await apiGet("/api/auth/me")
  const agencies = await apiGet("/api/agencies")
  const agency = agencies.items[0]
  if (!agency) {
    return { me, agency: null }
  }
  return { me, agency }
}
