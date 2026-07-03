import { useEffect, useMemo, useState } from "react"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import FileCheck2 from "lucide-react/dist/esm/icons/file-check-2.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"

const base = "/api/platform/airline-intelligence-agency-consumption"
const versionBase = "/api/platform/airline-intelligence-knowledge-versions"

const defaultProfile = {
  agency_id: "",
  knowledge_version_id: "",
  release_channel_id: "",
  status: "review",
  crm_safe: false,
  cms_safe: false,
  client_portal_safe: false,
  offer_builder_safe: false,
  plain_language_summary: "",
  allowed_usage_notes: "",
  blocked_usage_notes: "",
  internal_owner_notes: "",
  visible_to_agency: false,
}

export default function AirlineIntelligenceAgencyConsumptionPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultProfile)
  const [selectedProfileId, setSelectedProfileId] = useState("")
  const [noteText, setNoteText] = useState("")
  const [visibleNote, setVisibleNote] = useState(true)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(openProfileId = selectedProfileId) {
    const [me, summary, profiles, versions, channels, agencies, notes, snapshots] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/profiles`),
      apiGet(`${versionBase}/versions`),
      apiGet(`${versionBase}/release-channels`),
      apiGet("/api/agencies"),
      apiGet(`${base}/notes`),
      apiGet(`${base}/snapshots`),
    ])
    const profileItems = profiles.items || []
    const nextProfileId = openProfileId || profileItems[0]?.id || ""
    const selectedProfile = profileItems.find((item) => item.id === nextProfileId)
    const [assignments, readiness] = await Promise.all([
      selectedProfile ? apiGet(`${base}/agencies/${selectedProfile.agency_id}/assignments`) : Promise.resolve({ items: [] }),
      selectedProfile ? apiGet(`${base}/agencies/${selectedProfile.agency_id}/usage-readiness?profile_id=${selectedProfile.id}`) : Promise.resolve({ items: [] }),
    ])
    setSelectedProfileId(nextProfileId)
    setState({
      me,
      summary,
      profiles: profileItems,
      versions: versions.items || [],
      channels: channels.items || [],
      agencies: agencies.items || [],
      notes: notes.items || [],
      snapshots: snapshots.items || [],
      assignments: assignments.items || [],
      readiness: readiness.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedProfile = useMemo(() => state?.profiles?.find((profile) => profile.id === selectedProfileId), [state, selectedProfileId])
  const metrics = [
    ["Profiles", state?.summary?.profile_count || 0],
    ["Assignments", state?.summary?.assignment_view_count || 0],
    ["Readiness", state?.summary?.usage_readiness_count || 0],
    ["Notes", state?.summary?.note_count || 0],
    ["Snapshots", state?.summary?.snapshot_count || 0],
    ["Agency visible", state?.summary?.agency_visible_profile_count || 0],
  ]

  async function runAction(name, action) {
    setWorking(name)
    setError("")
    setMessage("")
    try {
      await action()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  function createProfile(event) {
    event.preventDefault()
    runAction("profile", async () => {
      const result = await apiPost(`${base}/profiles`, {
        ...form,
        release_channel_id: form.release_channel_id || null,
        visible_to_agency: form.status === "visible" || form.visible_to_agency,
      })
      setMessage("Agency consumption profile created.")
      setForm(defaultProfile)
      await load(result.profile.id)
    })
  }

  function updateSelected(updates) {
    if (!selectedProfile) return
    runAction("update", async () => {
      const result = await apiPatch(`${base}/profiles/${selectedProfile.id}`, updates)
      setMessage("Agency consumption profile updated.")
      await load(result.profile.id)
    })
  }

  function calculateReadiness() {
    if (!selectedProfile) return
    runAction("readiness", async () => {
      await apiPost(`${base}/agencies/${selectedProfile.agency_id}/usage-readiness`, {
        profile_id: selectedProfile.id,
        knowledge_version_id: selectedProfile.knowledge_version_id,
      })
      setMessage("Usage readiness calculated.")
      await load(selectedProfile.id)
    })
  }

  function createNote(event) {
    event.preventDefault()
    if (!selectedProfile || !noteText.trim()) return
    runAction("note", async () => {
      await apiPost(`${base}/notes`, {
        agency_id: selectedProfile.agency_id,
        knowledge_version_id: selectedProfile.knowledge_version_id,
        release_channel_id: selectedProfile.release_channel_id || null,
        profile_id: selectedProfile.id,
        note_type: visibleNote ? "agency_guidance" : "platform_internal",
        note: noteText,
        visible_to_agency: visibleNote,
      })
      setNoteText("")
      setMessage("Consumption note recorded.")
      await load(selectedProfile.id)
    })
  }

  function createSnapshot() {
    if (!selectedProfile) return
    runAction("snapshot", async () => {
      await apiPost(`${base}/snapshots`, {
        agency_id: selectedProfile.agency_id,
        knowledge_version_id: selectedProfile.knowledge_version_id,
        profile_id: selectedProfile.id,
        snapshot_type: "manual",
        snapshot_json: { plain_language_summary: "Manual agency consumption governance snapshot." },
      })
      setMessage("Immutable consumption snapshot created.")
      await load(selectedProfile.id)
    })
  }

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Agency Consumption</h2>
              <p className="mt-1 text-sm text-slate-600">Govern agency-safe consumption metadata for platform-owned knowledge versions.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={calculateReadiness} disabled={!selectedProfile || working === "readiness"}><RefreshCw className="h-4 w-4" />Readiness</button>
              <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createSnapshot} disabled={!selectedProfile || working === "snapshot"}><FileCheck2 className="h-4 w-4" />Snapshot</button>
              <button className="inline-flex items-center gap-2 aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={() => updateSelected({ status: "visible", visible_to_agency: true })} disabled={!selectedProfile || working === "update"}><CheckCircle2 className="h-4 w-4" />Visible</button>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 p-4">
                  <h3 className="font-semibold text-slate-950">Profiles</h3>
                </div>
                {!state?.profiles?.length ? <EmptyState title="No consumption profiles" body="Create a profile from a governed knowledge version." /> : (
                  <div className="divide-y divide-slate-100">
                    {state.profiles.map((profile) => (
                      <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedProfileId === profile.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(profile.id)} key={profile.id}>
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-semibold text-slate-950">{agencyName(state.agencies, profile.agency_id)}</p>
                            <p className="mt-1 text-sm text-slate-600">{profile.plain_language_summary || "Agency consumption profile"}</p>
                          </div>
                          <Status text={label(profile.status)} ready={profile.status === "visible"} />
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4">
                <h3 className="font-semibold text-slate-950">Create profile</h3>
                <form className="mt-4 grid gap-3" onSubmit={createProfile}>
                  <Select label="Agency" value={form.agency_id} onChange={(value) => setForm({ ...form, agency_id: value })} options={state?.agencies || []} optionLabel={(item) => item.name} />
                  <Select label="Knowledge version" value={form.knowledge_version_id} onChange={(value) => setForm({ ...form, knowledge_version_id: value })} options={state?.versions || []} optionLabel={(item) => `${item.version_code} · ${item.title}`} />
                  <Select label="Release channel" value={form.release_channel_id} onChange={(value) => setForm({ ...form, release_channel_id: value })} options={state?.channels || []} optionLabel={(item) => item.name} allowBlank />
                  <label className="grid gap-1 text-sm">
                    <span className="font-medium text-slate-700">Summary</span>
                    <textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2" value={form.plain_language_summary} onChange={(event) => setForm({ ...form, plain_language_summary: event.target.value })} />
                  </label>
                  <div className="grid gap-2 text-sm">
                    {[
                      ["crm_safe", "CRM"],
                      ["cms_safe", "Agency website"],
                      ["client_portal_safe", "Client portal"],
                      ["offer_builder_safe", "Offer builder"],
                    ].map(([field, text]) => (
                      <label className="flex items-center gap-2" key={field}>
                        <input type="checkbox" checked={form[field]} onChange={(event) => setForm({ ...form, [field]: event.target.checked })} />
                        <span>{text}</span>
                      </label>
                    ))}
                  </div>
                  <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={!form.agency_id || !form.knowledge_version_id || working === "profile"}>Create consumption profile</button>
                </form>
              </section>
            </div>

            <div className="space-y-4">
              {!selectedProfile ? <EmptyState title="Select a profile" body="Agency consumption details will appear here." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">{agencyName(state.agencies, selectedProfile.agency_id)}</h3>
                        <p className="mt-1 text-sm text-slate-600">{selectedProfile.plain_language_summary || "Agency consumption profile"}</p>
                      </div>
                      <Status text={label(selectedProfile.status)} ready={selectedProfile.status === "visible"} />
                    </div>
                    <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
                      <Flag label="CRM" enabled={selectedProfile.crm_safe} />
                      <Flag label="Agency website" enabled={selectedProfile.cms_safe} />
                      <Flag label="Client portal" enabled={selectedProfile.client_portal_safe} />
                      <Flag label="Offer builder" enabled={selectedProfile.offer_builder_safe} />
                    </div>
                    {selectedProfile.internal_owner_notes ? <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-600">{selectedProfile.internal_owner_notes}</p> : null}
                  </section>

                  <section className="grid gap-4 lg:grid-cols-2">
                    <Panel title="Usage readiness" items={state.readiness} render={(item) => (
                      <div className="p-4" key={item.id}>
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-semibold text-slate-950">{label(item.usage_area)}</p>
                          <Status text={label(item.status)} ready={item.status === "ready"} />
                        </div>
                        <p className="mt-1 text-sm text-slate-600">{item.plain_language_summary}</p>
                      </div>
                    )} emptyTitle="No readiness yet" />
                    <Panel title="Assignments" items={state.assignments} render={(item) => (
                      <div className="p-4" key={item.id}>
                        <p className="font-semibold text-slate-950">{label(item.status)}</p>
                        <p className="mt-1 text-sm text-slate-600">{item.plain_language_summary || "Agency-visible assignment metadata."}</p>
                      </div>
                    )} emptyTitle="No assignments" />
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white p-4">
                    <h3 className="font-semibold text-slate-950">Add note</h3>
                    <form className="mt-3 grid gap-3" onSubmit={createNote}>
                      <textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2 text-sm" value={noteText} onChange={(event) => setNoteText(event.target.value)} />
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={visibleNote} onChange={(event) => setVisibleNote(event.target.checked)} />
                        <span>Visible to agency</span>
                      </label>
                      <button className="w-fit rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={!noteText.trim() || working === "note"}>Record note</button>
                    </form>
                  </section>
                </>
              )}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Select({ label: text, value, onChange, options, optionLabel, allowBlank = false }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{text}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        {allowBlank ? <option value="">None</option> : <option value="">Select</option>}
        {options.map((item) => <option value={item.id} key={item.id}>{optionLabel(item)}</option>)}
      </select>
    </label>
  )
}

function Panel({ title, items, render, emptyTitle }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
      </div>
      {items?.length ? <div className="divide-y divide-slate-100">{items.map(render)}</div> : <EmptyState title={emptyTitle} body="Run metadata review to populate this panel." />}
    </section>
  )
}

function Metric({ label: text, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{text}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Flag({ label: text, enabled }) {
  return <span className={`rounded-md px-3 py-2 ${enabled ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-500"}`}>{text}: {enabled ? "Safe" : "Off"}</span>
}

function Status({ text, ready }) {
  const tone = ready ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function agencyName(agencies, agencyId) {
  return agencies?.find((agency) => agency.id === agencyId)?.name || agencyId || "Agency"
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
