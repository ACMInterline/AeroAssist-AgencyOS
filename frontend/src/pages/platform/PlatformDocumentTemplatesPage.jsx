import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function PlatformDocumentTemplatesPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState(false)

  async function load() {
    const [summary, templates] = await Promise.all([
      apiGet("/api/platform/summary"),
      apiGet("/api/platform/documents/templates"),
    ])
    setState({ summary, templates: templates.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const grouped = useMemo(() => {
    return (state?.templates || []).reduce((acc, template) => {
      const key = template.template_type || template.document_type || "custom"
      acc[key] = acc[key] || []
      acc[key].push(template)
      return acc
    }, {})
  }, [state])

  async function seedDefaults() {
    setWorking(true)
    setError("")
    setMessage("")
    try {
      const result = await apiPost("/api/platform/documents/templates/seed-defaults", {})
      setMessage(`Default templates ready. Created ${result.created_count || 0}; existing ${result.existing_count || 0}.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking(false)
    }
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Documents</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Platform Document Templates</h2>
              <p className="mt-1 text-sm text-slate-600">Default template definitions for internal AgencyOS document previews.</p>
            </div>
            <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={seedDefaults} disabled={working}>
              {working ? "Seeding..." : "Seed defaults"}
            </button>
          </div>

          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}
          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Templates" value={state?.templates?.length || 0} />
            <Metric label="Document types" value={Object.keys(grouped).length} />
            <Metric label="Active" value={(state?.templates || []).filter((item) => item.active !== false).length} />
            <Metric label="Scope" value="platform" />
          </section>

          {state?.templates?.length ? (
            <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <div className="grid grid-cols-[1fr_1fr_1fr_120px] gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <span>Template</span><span>Type</span><span>Key</span><span>Status</span>
              </div>
              <div className="divide-y divide-slate-100">
                {state.templates.map((template) => (
                  <div className="grid grid-cols-[1fr_1fr_1fr_120px] gap-3 px-4 py-4 text-sm text-slate-700" key={template.id}>
                    <span>
                      <span className="block font-semibold text-slate-950">{template.title || template.name}</span>
                      <span className="text-slate-500">{template.description || "No description"}</span>
                    </span>
                    <span>{label(template.template_type || template.document_type)}</span>
                    <span>{template.template_key || "not set"}</span>
                    <span>{template.active === false ? "inactive" : label(template.status || "active")}</span>
                  </div>
                ))}
              </div>
            </section>
          ) : (
            <EmptyState title="No document templates" body="Seed platform defaults to make agency document previews available." />
          )}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Metric({ label: metricLabel, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metricLabel}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function label(value) {
  return String(value || "not set").replaceAll("_", " ")
}
