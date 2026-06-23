import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const initialForm = {
  name: "",
  slug: "",
  legal_name: "",
  default_currency: "EUR",
  country: "SK",
  timezone: "Europe/Bratislava",
}

function slugify(value) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
}

export default function PlatformAgenciesPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(initialForm)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const summary = await apiGet("/api/platform/summary")
    const agencies = await apiGet("/api/agencies")
    setState({ summary, agencies: agencies.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  function updateField(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
      ...(field === "name" && !current.slug ? { slug: slugify(value) } : {}),
      ...(field === "name" && !current.legal_name ? { legal_name: value } : {}),
    }))
  }

  async function createAgency(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const result = await apiPost("/api/agencies", form)
      setForm(initialForm)
      setMessage("Agency created. Open it to create the first workspace.")
      await load()
      window.location.href = `/platform/agencies/${result.agency.id}`
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Agency Management</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-950">Agencies</h2>
                <p className="mt-2 text-sm text-slate-600">Create your first agency workspace to begin operating AeroAssist.</p>
              </div>
              <StatusBadge status={`${state?.agencies?.length || 0} agencies`} />
            </div>
            {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {state?.agencies?.length ? (
              <div className="mt-6 divide-y divide-slate-100 rounded-md border border-slate-200">
                {state.agencies.map((agency) => (
                  <a className="grid gap-3 p-4 hover:bg-slate-50 md:grid-cols-[1fr_auto]" href={`/platform/agencies/${agency.id}`} key={agency.id}>
                    <div>
                      <p className="font-semibold text-slate-950">{agency.name}</p>
                      <p className="mt-1 text-sm text-slate-600">{agency.legal_name}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
                      <StatusBadge status={agency.status} />
                      <span>{agency.workspace_count || 0} workspaces</span>
                      <span>{agency.staff_membership_count || 0} staff</span>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <div className="mt-6">
                <EmptyState title="No agencies yet" body="Create your first agency workspace to begin operating AeroAssist." />
              </div>
            )}
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="text-sm font-semibold text-slate-950">Create Agency</h3>
            <form className="mt-4 grid gap-4" onSubmit={createAgency}>
              <Input label="Agency name" value={form.name} onChange={(value) => updateField("name", value)} required />
              <Input label="Slug" value={form.slug} onChange={(value) => updateField("slug", slugify(value))} required />
              <Input label="Legal name" value={form.legal_name} onChange={(value) => updateField("legal_name", value)} required />
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Default currency" value={form.default_currency} onChange={(value) => updateField("default_currency", value.toUpperCase())} required />
                <Input label="Country" value={form.country} onChange={(value) => updateField("country", value.toUpperCase())} required />
              </div>
              <Input label="Timezone" value={form.timezone} onChange={(value) => updateField("timezone", value)} required />
              <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Create agency</button>
            </form>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Input({ label, value, onChange, required = false }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" required={required} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}
