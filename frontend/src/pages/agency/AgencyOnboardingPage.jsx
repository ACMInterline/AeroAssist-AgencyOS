import { useEffect, useMemo, useState } from "react"
import { Building2, Check, ChevronLeft, ChevronRight, Clock3, Gem, Image, Mail, Plane, Settings2, Users } from "lucide-react"
import ProtectedRoute from "../../components/ProtectedRoute"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const stepIcons = [Building2, Clock3, Image, Settings2, Plane, Check]
const defaultHours = [
  ["monday", true], ["tuesday", true], ["wednesday", true], ["thursday", true], ["friday", true],
  ["saturday", false], ["sunday", false],
].map(([day, enabled]) => ({ day, enabled, open_time: enabled ? "09:00" : null, close_time: enabled ? "17:30" : null }))

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1] || "")
    reader.onerror = () => reject(new Error("Logo could not be read."))
    reader.readAsDataURL(file)
  })
}

function Field({ label, value, onChange, type = "text", required = false, placeholder = "" }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2.5 text-sm text-slate-950 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" type={type} value={value || ""} onChange={(event) => onChange(event.target.value)} required={required} placeholder={placeholder} />
    </label>
  )
}

export default function AgencyOnboardingPage() {
  const [context, setContext] = useState(null)
  const [state, setState] = useState(null)
  const [stepIndex, setStepIndex] = useState(0)
  const [profile, setProfile] = useState({})
  const [hours, setHours] = useState(defaultHours)
  const [email, setEmail] = useState({ configuration_status: "not_configured", sender_name: "", sender_email: "", reply_to_email: "" })
  const [preferences, setPreferences] = useState({ landing_page: "/agency", compact_mode: false, dashboard_widgets: ["open_requests", "upcoming_departures", "deadlines", "work_queue"], in_app_notifications: true, email_notifications: false, assignment_notifications: true, deadline_notifications: true, service_notifications: true })
  const [demoProfiles, setDemoProfiles] = useState([])
  const [selectedDemoProfile, setSelectedDemoProfile] = useState("small_agency")
  const [generationProgress, setGenerationProgress] = useState(0)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const agencyContext = await loadCurrentAgency({ suppressOnboardingRedirect: true })
    if (!agencyContext.agency) throw new Error("No agency is available for onboarding.")
    const onboarding = await apiGet(`/api/agencies/${agencyContext.agency.id}/onboarding`)
    const demoProfileState = await apiGet(`/api/agencies/${agencyContext.agency.id}/onboarding/demo-workspace/profiles`)
    setContext(agencyContext)
    setState(onboarding)
    setDemoProfiles(demoProfileState.profiles || [])
    setSelectedDemoProfile(demoProfileState.selected_profile || "small_agency")
    const agency = onboarding.agency
    setProfile({ name: agency.name || "", legal_name: agency.legal_name || "", contact_name: agency.contact_name || "", contact_email: agency.contact_email || "", contact_phone: agency.contact_phone || "", address_line_1: agency.address_line_1 || "", address_line_2: agency.address_line_2 || "", city: agency.city || "", region: agency.region || "", postal_code: agency.postal_code || "", country: agency.country || "", timezone: agency.timezone || "UTC", default_currency: agency.default_currency || "EUR" })
    setHours(agency.working_hours?.length ? agency.working_hours : defaultHours)
    if (onboarding.email_settings) setEmail({ configuration_status: onboarding.email_settings.configuration_status || "not_configured", sender_name: onboarding.email_settings.sender_name || agency.name, sender_email: onboarding.email_settings.sender_email || agency.contact_email || "", reply_to_email: onboarding.email_settings.reply_to_email || "" })
    else setEmail((current) => ({ ...current, sender_name: agency.name, sender_email: agency.contact_email || "" }))
    if (onboarding.dashboard_preferences || onboarding.notification_preferences) setPreferences((current) => ({ ...current, ...onboarding.dashboard_preferences, ...onboarding.notification_preferences }))
    const persistedStep = onboarding.profile?.current_step
    const persistedIndex = onboarding.steps?.findIndex((item) => item.key === persistedStep)
    if (persistedIndex >= 0) setStepIndex(persistedIndex)
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  const steps = state?.steps || []
  const activeStep = steps[stepIndex]?.key || "agency_profile"
  const progress = state?.progress_percent || 0
  const logoUrl = context?.agency?.branding?.logo_url || context?.agency?.branding?.logo_data_url
  const completedCount = useMemo(() => steps.filter((item) => item.complete).length, [steps])

  async function action(callback, success) {
    setBusy(true); setError(""); setMessage("")
    try {
      const result = await callback()
      setState(result)
      setMessage(success)
      return result
    } catch (err) {
      setError(err.message)
      return null
    } finally { setBusy(false) }
  }

  async function saveProfile(nextIndex) {
    const result = await action(() => apiPut(`/api/agencies/${state.agency.id}/onboarding/profile`, { ...profile, working_hours: hours, current_step: steps[nextIndex]?.key || activeStep }), "Agency details saved.")
    if (result) setStepIndex(nextIndex)
  }

  async function saveCommunications(nextIndex) {
    const statusResult = await action(() => apiPut(`/api/agencies/${state.agency.id}/onboarding/email-status`, email), "Communication status saved.")
    if (!statusResult) return
    const result = await action(() => apiPut(`/api/agencies/${state.agency.id}/onboarding/preferences`, preferences), "Preferences saved.")
    if (result) setStepIndex(nextIndex)
  }

  async function uploadLogo(event) {
    const file = event.target.files?.[0]
    if (!file) return
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 2 * 1024 * 1024) {
      setError("Use a PNG, JPEG, or WEBP logo no larger than 2 MB.")
      return
    }
    const dataBase64 = await fileToBase64(file)
    await action(async () => {
      await apiPost(`/api/agencies/${state.agency.id}/branding/logo`, { filename: file.name, content_type: file.type, data_base64: dataBase64 })
      const result = await apiPost(`/api/agencies/${state.agency.id}/onboarding/logo/confirm`)
      await load()
      return result
    }, "Logo uploaded and confirmed.")
  }

  async function seedDemo() {
    setGenerationProgress(5)
    const progressTimer = window.setInterval(() => setGenerationProgress((current) => Math.min(current + 7, 88)), 350)
    const result = await action(
      () => apiPost(`/api/agencies/${state.agency.id}/onboarding/demo-workspace`, { demo_profile: selectedDemoProfile }),
      "Complete synthetic pilot workspace created.",
    )
    window.clearInterval(progressTimer)
    if (result) {
      setGenerationProgress(100)
      setStepIndex(5)
    } else setGenerationProgress(0)
  }

  async function finish() {
    const result = await action(() => apiPost(`/api/agencies/${state.agency.id}/onboarding/complete`), "Onboarding complete.")
    if (result) window.location.href = `/agency?agency_id=${state.agency.id}`
  }

  function renderStep() {
    if (activeStep === "agency_profile") return (
      <form className="grid gap-5" onSubmit={(event) => { event.preventDefault(); saveProfile(1) }}>
        <div><h2 className="text-xl font-semibold text-slate-950">Agency profile</h2><p className="mt-1 text-sm text-slate-600">Set the identity clients and operational documents will use.</p></div>
        <div className="grid gap-4 sm:grid-cols-2"><Field label="Agency name" value={profile.name} onChange={(value) => setProfile({ ...profile, name: value })} required /><Field label="Legal name" value={profile.legal_name} onChange={(value) => setProfile({ ...profile, legal_name: value })} required /></div>
        <div className="grid gap-4 sm:grid-cols-3"><Field label="Contact name" value={profile.contact_name} onChange={(value) => setProfile({ ...profile, contact_name: value })} required /><Field label="Contact email" type="email" value={profile.contact_email} onChange={(value) => setProfile({ ...profile, contact_email: value })} required /><Field label="Contact phone" type="tel" value={profile.contact_phone} onChange={(value) => setProfile({ ...profile, contact_phone: value })} required /></div>
        <div className="grid gap-4 sm:grid-cols-2"><Field label="Address line 1" value={profile.address_line_1} onChange={(value) => setProfile({ ...profile, address_line_1: value })} required /><Field label="Address line 2" value={profile.address_line_2} onChange={(value) => setProfile({ ...profile, address_line_2: value })} /></div>
        <div className="grid gap-4 sm:grid-cols-4"><Field label="City" value={profile.city} onChange={(value) => setProfile({ ...profile, city: value })} required /><Field label="Region" value={profile.region} onChange={(value) => setProfile({ ...profile, region: value })} /><Field label="Postcode" value={profile.postal_code} onChange={(value) => setProfile({ ...profile, postal_code: value })} /><Field label="Country code" value={profile.country} onChange={(value) => setProfile({ ...profile, country: value.toUpperCase() })} required /></div>
        <div className="grid gap-4 sm:grid-cols-2"><Field label="IANA time zone" value={profile.timezone} onChange={(value) => setProfile({ ...profile, timezone: value })} required placeholder="Europe/Sofia" /><Field label="Currency" value={profile.default_currency} onChange={(value) => setProfile({ ...profile, default_currency: value.toUpperCase() })} required placeholder="EUR" /></div>
        <Footer busy={busy} next="Save and continue" />
      </form>
    )
    if (activeStep === "working_hours") return (
      <form className="space-y-5" onSubmit={(event) => { event.preventDefault(); saveProfile(2) }}>
        <div><h2 className="text-xl font-semibold text-slate-950">Working hours</h2><p className="mt-1 text-sm text-slate-600">These hours provide the default operational context for deadlines and dashboards.</p></div>
        <div className="divide-y divide-slate-100 rounded-md border border-slate-200">{hours.map((item, index) => <div className="grid items-center gap-3 p-3 sm:grid-cols-[140px_90px_1fr_1fr]" key={item.day}><span className="text-sm font-semibold capitalize text-slate-800">{item.day}</span><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={item.enabled} onChange={(event) => setHours(hours.map((entry, idx) => idx === index ? { ...entry, enabled: event.target.checked, open_time: event.target.checked ? entry.open_time || "09:00" : null, close_time: event.target.checked ? entry.close_time || "17:30" : null } : entry))} /> Open</label><input aria-label={`${item.day} opening time`} className="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" type="time" disabled={!item.enabled} value={item.open_time || ""} onChange={(event) => setHours(hours.map((entry, idx) => idx === index ? { ...entry, open_time: event.target.value } : entry))} /><input aria-label={`${item.day} closing time`} className="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" type="time" disabled={!item.enabled} value={item.close_time || ""} onChange={(event) => setHours(hours.map((entry, idx) => idx === index ? { ...entry, close_time: event.target.value } : entry))} /></div>)}</div>
        <Footer busy={busy} back={() => setStepIndex(0)} next="Save and continue" />
      </form>
    )
    if (activeStep === "branding") return (
      <div className="space-y-5"><div><h2 className="text-xl font-semibold text-slate-950">Branding</h2><p className="mt-1 text-sm text-slate-600">Add a logo now or keep the generated AeroAssist default and update it later.</p></div><div className="flex min-h-48 items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 p-8">{logoUrl ? <img className="max-h-32 max-w-full object-contain" src={logoUrl} alt="Agency logo preview" /> : <div className="text-center"><Image className="mx-auto h-9 w-9 text-slate-400" /><p className="mt-3 text-sm text-slate-600">No agency logo uploaded</p></div>}</div><div className="flex flex-wrap gap-3"><label className="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">Upload logo<input className="sr-only" type="file" accept="image/png,image/jpeg,image/webp" onChange={uploadLogo} /></label><button className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" type="button" disabled={busy} onClick={async () => { const result = await action(() => apiPost(`/api/agencies/${state.agency.id}/onboarding/logo/skip`), "Default branding selected."); if (result) setStepIndex(3) }}>Use default branding</button></div><p className="text-xs text-slate-500">PNG, JPEG, or WEBP. Maximum 2 MB.</p><Footer busy={busy} back={() => setStepIndex(1)} next="Continue" onNext={() => state.profile.logo_status === "uploaded" || state.profile.logo_status === "skipped" ? setStepIndex(3) : setError("Upload a logo or choose the default branding.")} /></div>
    )
    if (activeStep === "communications_preferences") return (
      <form className="space-y-5" onSubmit={(event) => { event.preventDefault(); saveCommunications(4) }}><div><h2 className="text-xl font-semibold text-slate-950">Communications and workspace</h2><p className="mt-1 text-sm text-slate-600">Record configuration readiness and choose quiet operational defaults. No message is sent.</p></div><div className="grid gap-4 sm:grid-cols-2"><label className="block text-sm font-medium text-slate-700">Email configuration status<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2.5 text-sm" value={email.configuration_status} onChange={(event) => setEmail({ ...email, configuration_status: event.target.value })}>{["not_configured", "configuration_pending", "configured_unverified", "verified", "not_required"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label><Field label="Sender name" value={email.sender_name} onChange={(value) => setEmail({ ...email, sender_name: value })} required /><Field label="Sender email" type="email" value={email.sender_email} onChange={(value) => setEmail({ ...email, sender_email: value })} required /><Field label="Reply-to email" type="email" value={email.reply_to_email} onChange={(value) => setEmail({ ...email, reply_to_email: value })} /></div><div className="grid gap-3 rounded-md border border-slate-200 p-4 sm:grid-cols-2">{[["in_app_notifications", "In-app notifications"], ["email_notifications", "Email notifications"], ["assignment_notifications", "Assignments"], ["deadline_notifications", "Deadlines"], ["service_notifications", "Passenger services"], ["compact_mode", "Compact dashboard"]].map(([key, label]) => <label className="flex items-center gap-3 text-sm text-slate-700" key={key}><input type="checkbox" checked={Boolean(preferences[key])} onChange={(event) => setPreferences({ ...preferences, [key]: event.target.checked })} />{label}</label>)}</div><div className="rounded-md border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900"><Mail className="mr-2 inline h-4 w-4" />Email remains disabled until separately configured and verified.</div><Footer busy={busy} back={() => setStepIndex(2)} next="Save and continue" /></form>
    )
    if (activeStep === "demo_workspace") return (
      <div className="space-y-6">
        <div><h2 className="text-xl font-semibold text-slate-950">Complete pilot workspace</h2><p className="mt-1 text-sm text-slate-600">Choose the operating profile your team wants to evaluate. Every record is synthetic, canonical, and linked across the workflow.</p></div>
        <div className="grid gap-3 sm:grid-cols-2">
          {demoProfiles.map((item, index) => {
            const Icon = index === 3 ? Gem : index === 0 ? Building2 : Users
            const selected = selectedDemoProfile === item.key
            return <button className={`min-h-36 rounded-md border p-4 text-left transition ${selected ? "border-blue-500 bg-blue-50 ring-2 ring-blue-100" : "border-slate-200 bg-white hover:border-slate-300"}`} type="button" key={item.key} disabled={state.profile.demo_workspace_seeded || busy} onClick={() => setSelectedDemoProfile(item.key)}><span className="flex items-center justify-between gap-3"><span className="flex items-center gap-2 font-semibold text-slate-950"><Icon className="h-4 w-4 text-blue-700" />{item.label}</span><span className={`h-4 w-4 rounded-full border-4 ${selected ? "border-blue-600 bg-white" : "border-slate-300 bg-white"}`} /></span><span className="mt-3 block text-sm leading-5 text-slate-600">{item.description}</span><span className="mt-3 block text-xs font-semibold text-slate-500">About {item.estimated_record_count} records · {item.scenario_count} scenarios</span></button>
          })}
        </div>
        {demoProfiles.find((item) => item.key === selectedDemoProfile) ? <div className="grid gap-5 border-y border-slate-200 py-5 lg:grid-cols-2"><Summary title="Operational areas" items={demoProfiles.find((item) => item.key === selectedDemoProfile).generated_operational_areas} /><Summary title="Scenario preview" items={demoProfiles.find((item) => item.key === selectedDemoProfile).scenario_preview} /></div> : null}
        <Summary title="Safety boundaries" items={["No provider or airline communication", "No PNR creation or ticket issuance", "No payment execution", "Stable IDs make safe reruns idempotent"]} />
        {generationProgress > 0 ? <div aria-live="polite"><div className="flex justify-between text-sm font-medium text-slate-700"><span>{generationProgress === 100 ? "Pilot workspace ready" : "Generating linked operational records"}</span><span>{generationProgress}%</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-blue-600 transition-all" style={{ width: `${generationProgress}%` }} /></div></div> : null}
        <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white disabled:bg-slate-400" type="button" disabled={busy} onClick={seedDemo}><Plane className="h-4 w-4" />{state.profile.demo_workspace_seeded ? "Refresh selected workspace safely" : "Create demo workspace"}</button>
        <Footer busy={busy} back={() => setStepIndex(3)} next="Review setup" onNext={() => state.profile.demo_workspace_seeded ? setStepIndex(5) : setError("Create the demo workspace before review.")} />
      </div>
    )
    return (
      <div className="space-y-5"><div><h2 className="text-xl font-semibold text-slate-950">Ready for operations</h2><p className="mt-1 text-sm text-slate-600">Review the setup. Completing onboarding activates the agency workspace; it does not enable providers, payments, or ticketing.</p></div><div className="divide-y divide-slate-100 rounded-md border border-slate-200">{steps.slice(0, 5).map((item) => <div className="flex items-center justify-between p-4" key={item.key}><span className="text-sm font-medium text-slate-800">{item.label}</span><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${item.complete ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{item.complete ? "Complete" : "Needs attention"}</span></div>)}</div>{state.profile?.demo_generation_summary?.record_count ? <div className="border-y border-slate-200 py-5"><div className="grid gap-4 sm:grid-cols-3"><div><p className="text-xs font-semibold uppercase text-slate-500">Profile</p><p className="mt-1 text-sm font-semibold text-slate-950">{state.profile.demo_generation_summary.profile_label}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Linked records</p><p className="mt-1 text-sm font-semibold text-slate-950">{state.profile.demo_generation_summary.record_count}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Scenarios</p><p className="mt-1 text-sm font-semibold text-slate-950">{state.profile.demo_generation_summary.scenario_count}</p></div></div><p className="mt-4 text-sm text-slate-600">The Operations Command Centre, booking, offers, passenger services, documents, finance, and after-sales views now have linked synthetic examples.</p></div> : null}<Footer busy={busy} back={() => setStepIndex(4)} next="Complete onboarding" onNext={finish} /></div>
    )
  }

  if (state?.legacy_exempt || (state && !state.required && state.profile?.onboarding_status === "completed")) {
    window.location.replace(`/agency?agency_id=${state.agency.id}`)
    return null
  }

  return (
    <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
      <main className="min-h-screen bg-slate-100 px-4 py-6 sm:px-6 lg:py-10">
        <div className="mx-auto max-w-6xl overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <header className="border-b border-slate-200 px-5 py-4 sm:px-7"><div className="flex flex-wrap items-center justify-between gap-4"><div><p className="text-sm font-semibold text-blue-700">AeroAssist setup</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">{state?.agency?.name}</h1></div><div className="min-w-48"><div className="flex justify-between text-xs font-medium text-slate-600"><span>{completedCount} of {steps.length} complete</span><span>{progress}%</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-blue-600 transition-all" style={{ width: `${progress}%` }} /></div></div></div></header>
          <div className="grid lg:grid-cols-[250px_1fr]"><nav className="border-b border-slate-200 bg-slate-50 p-4 lg:border-b-0 lg:border-r"><ol className="grid gap-1 sm:grid-cols-3 lg:grid-cols-1">{steps.map((item, index) => { const Icon = stepIcons[index]; return <li key={item.key}><button className={`flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm font-medium ${index === stepIndex ? "bg-blue-100 text-blue-900" : "text-slate-700 hover:bg-slate-100"}`} type="button" onClick={() => setStepIndex(index)}><span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${item.complete ? "bg-emerald-100 text-emerald-700" : "bg-white text-slate-500"}`}>{item.complete ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}</span>{item.label}</button></li> })}</ol></nav><section className="min-w-0 p-5 sm:p-7 lg:p-9">{message ? <p className="mb-5 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}{error ? <p className="mb-5 rounded-md bg-red-50 p-3 text-sm text-red-800">{error}</p> : null}{renderStep()}<p className="mt-8 border-t border-slate-100 pt-4 text-xs text-slate-500">Progress is saved after each step. You can close this page and resume later. <a className="font-semibold text-blue-700 hover:underline" href="/agency/pilot-feedback?affected_area=onboarding#pilot-guides">Open the pilot onboarding guide</a>.</p></section></div>
        </div>
      </main>
    </ProtectedRoute>
  )
}

function Footer({ busy, back, next, onNext }) {
  return <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">{back ? <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" type="button" onClick={back}><ChevronLeft className="h-4 w-4" />Back</button> : <span />}<button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" type={onNext ? "button" : "submit"} disabled={busy} onClick={onNext}>{busy ? "Saving..." : next}<ChevronRight className="h-4 w-4" /></button></div>
}

function Summary({ title, items }) {
  return <div className="rounded-md border border-slate-200 p-4"><h3 className="text-sm font-semibold text-slate-950">{title}</h3><ul className="mt-3 space-y-2">{items.map((item) => <li className="flex gap-2 text-sm text-slate-600" key={item}><Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />{item}</li>)}</ul></div>
}
