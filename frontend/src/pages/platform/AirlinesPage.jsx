import { useEffect, useState } from "react"
import AirlineStatusBadge from "../../components/AirlineStatusBadge"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function AirlinesPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ airline_code: "", airline_name: "", country: "", website_url: "" })
  const [search, setSearch] = useState("")
  const [error, setError] = useState("")

  async function load(query = search) {
    const [summary, airlines] = await Promise.all([
      apiGet("/api/platform/summary"),
      apiGet(`/api/platform/airlines${query ? `?search=${encodeURIComponent(query)}` : ""}`),
    ])
    setState({ summary, airlines: airlines.items })
  }

  useEffect(() => {
    load("").catch((err) => setError(err.message))
  }, [])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function createAirline(event) {
    event.preventDefault()
    await apiPost("/api/platform/airlines", { ...form, status: "active" })
    setForm({ airline_code: "", airline_name: "", country: "", website_url: "" })
    await load("")
  }

  async function runSearch(event) {
    event.preventDefault()
    await load(search)
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airlines / Knowledge</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Global Airline Intelligence</h2>
              <p className="mt-1 text-sm text-slate-600">Platform-owned records published to agencies as decision support.</p>
            </div>
            <form className="flex gap-2" onSubmit={runSearch}>
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search airlines" value={search} onChange={(event) => setSearch(event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Search</button>
            </form>
          </div>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Create Airline</h3>
            <form className="mt-4 grid gap-3 md:grid-cols-[100px_1fr_140px_1fr_auto]" onSubmit={createAirline}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Code" value={form.airline_code} onChange={(event) => setField("airline_code", event.target.value.toUpperCase())} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline name" value={form.airline_name} onChange={(event) => setField("airline_name", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Country" value={form.country} onChange={(event) => setField("country", event.target.value)} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Website URL" value={form.website_url} onChange={(event) => setField("website_url", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create</button>
            </form>
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Airlines</h3>
            {!state.airlines.length ? <EmptyState title="No airlines found" body="Create a platform-owned airline profile to start adding knowledge." /> : (
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {state.airlines.map((airline) => (
                  <a className="grid gap-2 p-4 text-sm hover:bg-slate-50 md:grid-cols-[100px_1fr_160px_120px]" href={`/platform/airlines/${airline.id}`} key={airline.id}>
                    <span className="font-semibold text-slate-950">{airline.airline_code}</span>
                    <span className="text-slate-700">{airline.airline_name}</span>
                    <span className="text-slate-600">{airline.country}</span>
                    <AirlineStatusBadge status={airline.status} />
                  </a>
                ))}
              </div>
            )}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
