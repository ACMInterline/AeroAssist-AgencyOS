import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { loadCurrentAgency } from "../../lib/agency"
import {
  bootstrapGlobalFieldDefinitions,
  createAgencyFormProfile,
  fetchAgencyFormProfiles,
  fetchEffectiveAgencyFormProfile,
  fetchGlobalFieldDefinitions,
  updateAgencyFormProfileFields,
} from "../../lib/formProfiles"

const contexts = [
  ["public_request", "Public Request"],
  ["portal_request", "Portal Request"],
  ["admin_request", "Admin Request"],
  ["offer_client_view", "Offer Client View"],
  ["offer_pdf", "Offer PDF"],
]

const customTypes = ["text", "textarea", "select", "boolean", "number", "date"]

export default function FormProfilesPage() {
  const [state, setState] = useState(null)
  const [profiles, setProfiles] = useState([])
  const [definitions, setDefinitions] = useState([])
  const [selectedProfileId, setSelectedProfileId] = useState("")
  const [effective, setEffective] = useState(null)
  const [drafts, setDrafts] = useState([])
  const [profileForm, setProfileForm] = useState({ profile_key: "custom_public_request", name: "Custom Public Request", form_context: "public_request", is_default: false })
  const [customForm, setCustomForm] = useState({ field_key: "", label: "", field_type: "text", help_text: "", section_key: "agency_custom", display_order: 1000 })
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  const isPlatformOwner = ["platform_owner", "platform_admin"].includes(state?.me?.user?.global_role)
  const selectedProfile = profiles.find((item) => item.id === selectedProfileId)

  async function load(selectedId = selectedProfileId) {
    const context = state || await loadCurrentAgency()
    const [profileResult, definitionResult] = await Promise.all([
      fetchAgencyFormProfiles(context.agency.id),
      fetchGlobalFieldDefinitions().catch(() => ({ items: [] })),
    ])
    const nextProfiles = profileResult.items || []
    const profileId = selectedId || nextProfiles[0]?.id || ""
    setState(context)
    setProfiles(nextProfiles)
    setDefinitions(definitionResult.items || [])
    setSelectedProfileId(profileId)
    if (profileId) {
      await loadEffective(context.agency.id, profileId)
    }
  }

  async function loadEffective(agencyId, profileId) {
    const result = await fetchEffectiveAgencyFormProfile(agencyId, profileId)
    setEffective(result)
    setDrafts((result.fields || []).map(fieldToDraft))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function selectProfile(profileId) {
    setSelectedProfileId(profileId)
    setError("")
    setMessage("")
    await loadEffective(state.agency.id, profileId)
  }

  async function bootstrapFields() {
    setError("")
    setMessage("")
    try {
      const result = await bootstrapGlobalFieldDefinitions()
      setMessage(`Global field bootstrap processed ${result.bootstrap.inserted} inserted and ${result.bootstrap.updated} updated.`)
      await load(selectedProfileId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function createProfile(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const result = await createAgencyFormProfile(state.agency.id, profileForm)
      setMessage("Form profile created.")
      await load(result.profile.id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function saveFields() {
    setError("")
    setMessage("")
    try {
      await updateAgencyFormProfileFields(state.agency.id, selectedProfileId, drafts.map(draftToPayload))
      setMessage("Field settings saved.")
      await loadEffective(state.agency.id, selectedProfileId)
    } catch (err) {
      setError(err.message)
    }
  }

  function patchDraft(fieldKey, patch) {
    setDrafts((current) => current.map((item) => item.field_key === fieldKey ? { ...item, ...patch } : item))
  }

  function addCustomField(event) {
    event.preventDefault()
    const key = customForm.field_key.trim().replaceAll(" ", "_")
    if (!key || !customForm.label.trim()) {
      setError("Custom field key and label are required.")
      return
    }
    const fieldKey = key.startsWith("custom.") ? key : `custom.${key}`
    if (drafts.some((item) => item.field_key === fieldKey)) {
      setError("Custom field key already exists.")
      return
    }
    setDrafts((current) => [...current, {
      field_key: fieldKey,
      custom_field: true,
      enabled: true,
      visible: true,
      required_override: false,
      label_override: customForm.label,
      help_text_override: customForm.help_text,
      display_order: Number(customForm.display_order || 1000),
      section_key: customForm.section_key || "agency_custom",
      custom_field_schema_json: { field_type: customForm.field_type, label: customForm.label, help_text: customForm.help_text },
    }])
    setCustomForm({ field_key: "", label: "", field_type: "text", help_text: "", section_key: "agency_custom", display_order: 1000 })
    setMessage("Custom question staged. Save field settings to persist it.")
  }

  const groupedDrafts = useMemo(() => {
    const groups = []
    drafts.forEach((draft) => {
      const sectionKey = draft.section_key || "general"
      let group = groups.find((item) => item.section_key === sectionKey)
      if (!group) {
        group = { section_key: sectionKey, section_label: draft.section_label || sectionKey.replaceAll("_", " "), fields: [] }
        groups.push(group)
      }
      group.fields.push(draft)
    })
    return groups
  }, [drafts])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Form Profiles</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Configure which approved fields appear in your request and offer forms.</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">AeroAssist owns canonical fields. Agencies can safely adjust visibility, labels, helper text, order, and custom questions without changing SSR, policy, pricing, or compliance meaning.</p>
            {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          </section>

          <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
            <aside className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-950">Profiles</h3>
                  {isPlatformOwner ? <button className="rounded-md bg-slate-950 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={bootstrapFields}>Bootstrap fields</button> : null}
                </div>
                <p className="mt-1 text-xs text-slate-500">{definitions.length} global field definitions loaded</p>
                <div className="mt-3 space-y-2">
                  {profiles.map((profile) => (
                    <button className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedProfileId === profile.id ? "bg-blue-50 font-semibold text-blue-800" : "text-slate-700 hover:bg-slate-50"}`} type="button" onClick={() => selectProfile(profile.id)} key={profile.id}>
                      <span className="block">{profile.name}</span>
                      <span className="text-xs text-slate-500">{profile.form_context.replaceAll("_", " ")} {profile.is_default ? "· default" : ""}</span>
                    </button>
                  ))}
                  {!profiles.length ? <EmptyState title="No profiles" body="Default profiles are created automatically for agencies with access." /> : null}
                </div>
              </section>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-4" onSubmit={createProfile}>
                <h3 className="font-semibold text-slate-950">Create profile</h3>
                <Field label="Profile key" value={profileForm.profile_key} onChange={(value) => setProfileForm({ ...profileForm, profile_key: value })} required />
                <Field label="Name" value={profileForm.name} onChange={(value) => setProfileForm({ ...profileForm, name: value })} required />
                <Select label="Context" value={profileForm.form_context} onChange={(value) => setProfileForm({ ...profileForm, form_context: value })} options={contexts} />
                <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={profileForm.is_default} onChange={(event) => setProfileForm({ ...profileForm, is_default: event.target.checked })} /> Make default for context</label>
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Create profile</button>
              </form>
            </aside>

            <main className="space-y-4">
              {selectedProfile ? (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-xl font-semibold text-slate-950">{selectedProfile.name}</h3>
                        <p className="text-sm text-slate-600">{selectedProfile.form_context.replaceAll("_", " ")} · {effective?.fields?.filter((field) => field.visible).length || 0} visible fields</p>
                      </div>
                      <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="button" onClick={saveFields}>Save field settings</button>
                    </div>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <h3 className="font-semibold text-slate-950">Add custom agency question</h3>
                    <form className="mt-3 grid gap-3 md:grid-cols-5" onSubmit={addCustomField}>
                      <Field label="Key" value={customForm.field_key} onChange={(value) => setCustomForm({ ...customForm, field_key: value })} placeholder="vip_number" />
                      <Field label="Label" value={customForm.label} onChange={(value) => setCustomForm({ ...customForm, label: value })} />
                      <Select label="Type" value={customForm.field_type} onChange={(value) => setCustomForm({ ...customForm, field_type: value })} options={customTypes.map((item) => [item, item])} />
                      <Field label="Section" value={customForm.section_key} onChange={(value) => setCustomForm({ ...customForm, section_key: value })} />
                      <Field label="Order" type="number" value={customForm.display_order} onChange={(value) => setCustomForm({ ...customForm, display_order: value })} />
                      <Field label="Help text" value={customForm.help_text} onChange={(value) => setCustomForm({ ...customForm, help_text: value })} />
                      <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold md:w-fit" type="submit">Stage custom question</button>
                    </form>
                  </section>

                  {groupedDrafts.map((group) => (
                    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white" key={group.section_key}>
                      <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
                        <h4 className="font-semibold capitalize text-slate-950">{group.section_label}</h4>
                      </div>
                      <div className="divide-y divide-slate-100">
                        {group.fields.map((field) => <FieldRow field={field} onPatch={(patch) => patchDraft(field.field_key, patch)} key={field.field_key} />)}
                      </div>
                    </section>
                  ))}
                </>
              ) : <EmptyState title="No profile selected" body="Create or select a form profile to configure fields." />}
            </main>
          </div>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function FieldRow({ field, onPatch }) {
  const safeBadges = [["public", field.public_safe], ["portal", field.portal_safe], ["admin", field.admin_safe]]
  return (
    <div className="grid gap-3 p-4 text-sm lg:grid-cols-[1.2fr_0.9fr_1.3fr]">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-semibold text-slate-950">{field.effective_label || field.label}</p>
          <Status value={field.required_level || "custom"} />
          {field.locked ? <Status value={`locked: ${field.locked_reason}`} tone="amber" /> : null}
          {field.custom_field ? <Status value="custom" tone="blue" /> : null}
        </div>
        <p className="mt-1 font-mono text-xs text-slate-500">{field.canonical_path}</p>
        <div className="mt-2 flex flex-wrap gap-1">{safeBadges.map(([label, ok]) => <Status value={label} tone={ok ? "green" : "slate"} key={label} />)}</div>
      </div>
      <div className="grid gap-2">
        <label className="flex items-center gap-2 text-slate-700"><input type="checkbox" checked={field.visible} disabled={field.locked && field.visible} onChange={(event) => onPatch({ visible: event.target.checked, enabled: event.target.checked })} /> Visible</label>
        <label className="flex items-center gap-2 text-slate-700"><input type="checkbox" checked={field.required_override ?? field.required} disabled={!field.can_be_required_by_agency && !field.custom_field} onChange={(event) => onPatch({ required_override: event.target.checked })} /> Required</label>
        <Field label="Order" type="number" value={field.display_order} onChange={(value) => onPatch({ display_order: value })} />
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        <Field label="Label override" value={field.label_override || ""} disabled={!field.can_label_be_overridden && !field.custom_field} onChange={(value) => onPatch({ label_override: value })} />
        <Field label="Help override" value={field.help_text_override || ""} disabled={!field.can_label_be_overridden && !field.custom_field} onChange={(value) => onPatch({ help_text_override: value })} />
        <Field label="Placeholder" value={field.placeholder_override || ""} onChange={(value) => onPatch({ placeholder_override: value })} />
        <Field label="Section" value={field.section_key || ""} onChange={(value) => onPatch({ section_key: value })} />
      </div>
    </div>
  )
}

function fieldToDraft(field) {
  const setting = field.setting || {}
  return {
    id: setting.id,
    global_field_definition_id: field.custom_field ? null : field.id,
    field_key: field.field_key,
    enabled: field.enabled,
    visible: field.visible,
    required_override: setting.required_override ?? null,
    label_override: setting.label_override || "",
    help_text_override: setting.help_text_override || "",
    placeholder_override: setting.placeholder_override || "",
    display_order: field.display_order,
    section_key: field.section_key,
    section_label: field.section_label,
    custom_field: Boolean(field.custom_field),
    custom_field_schema_json: field.custom_field_schema_json || setting.custom_field_schema_json || null,
    can_be_required_by_agency: field.can_be_required_by_agency,
    can_label_be_overridden: field.can_label_be_overridden,
    required: field.required,
    required_level: field.required_level,
    public_safe: field.public_safe,
    portal_safe: field.portal_safe,
    admin_safe: field.admin_safe,
    canonical_path: field.canonical_path,
    label: field.label,
    effective_label: field.effective_label,
    locked: field.locked,
    locked_reason: field.locked_reason,
  }
}

function draftToPayload(draft) {
  return {
    id: draft.id || undefined,
    global_field_definition_id: draft.global_field_definition_id || undefined,
    field_key: draft.field_key,
    enabled: Boolean(draft.enabled),
    visible: Boolean(draft.visible),
    required_override: draft.required_override,
    label_override: draft.label_override || null,
    help_text_override: draft.help_text_override || null,
    placeholder_override: draft.placeholder_override || null,
    display_order: Number(draft.display_order || 100),
    section_key: draft.section_key || "general",
    custom_field: Boolean(draft.custom_field),
    custom_field_schema_json: draft.custom_field ? draft.custom_field_schema_json || { field_type: "text", label: draft.label_override || draft.field_key } : null,
  }
}

function Status({ value, tone = "slate" }) {
  const tones = { green: "bg-emerald-50 text-emerald-700", amber: "bg-amber-50 text-amber-800", blue: "bg-blue-50 text-blue-700", slate: "bg-slate-100 text-slate-600" }
  return <span className={`rounded-full px-2 py-1 text-[11px] font-semibold ${tones[tone] || tones.slate}`}>{String(value || "").replaceAll("_", " ")}</span>
}

function Field({ label, value, onChange, type = "text", required = false, placeholder = "", disabled = false }) {
  return <label className="block text-xs font-medium text-slate-700">{label}<input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" type={type} value={value || ""} required={required} placeholder={placeholder} disabled={disabled} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, onChange, options }) {
  return <label className="block text-xs font-medium text-slate-700">{label}<select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}</select></label>
}
