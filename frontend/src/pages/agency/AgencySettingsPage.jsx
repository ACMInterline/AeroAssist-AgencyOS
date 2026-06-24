import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiDelete, apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"
import { agencyThemeStyle } from "../../lib/theme"

const editableFields = [
  "workspace_id",
  "brand_name",
  "logo_fit_mode",
  "preferred_logo_usage",
  "logo_public_usage_allowed",
  "font_family_key",
  "corner_radius_key",
  "density_key",
  "theme_mode",
  "color_palette_key",
  "field_style_key",
  "button_style_key",
  "calendar_style_key",
  "card_style_key",
]

function optionEntries(options = {}) {
  return Object.entries(options).map(([key, value]) => [key, value.label || key])
}

function titleize(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1] || "")
    reader.onerror = () => reject(new Error("Logo could not be read."))
    reader.readAsDataURL(file)
  })
}

function computedThemeFromForm(form, options, fallback = {}) {
  return {
    ...fallback,
    font_stack: options.fonts?.[form.font_family_key]?.stack || fallback.font_stack,
    corner_radius: options.corner_radii?.[form.corner_radius_key] || fallback.corner_radius,
    palette: options.palettes?.[form.color_palette_key] || fallback.palette,
    theme_mode: form.theme_mode || fallback.theme_mode,
    density_key: form.density_key || fallback.density_key,
  }
}

export default function AgencySettingsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({})
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const branding = context.agency ? await apiGet(`/api/agencies/${context.agency.id}/branding`) : null
    const agency = context.agency && branding ? { ...context.agency, branding: branding.branding, computed_theme: branding.computed_theme, design_options: branding.design_options } : context.agency
    setState({ ...context, agency, branding })
    setForm(branding?.branding || {})
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function save(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    const payload = Object.fromEntries(editableFields.filter((field) => form[field] !== undefined).map((field) => [field, form[field] || null]))
    try {
      const result = await apiPut(`/api/agencies/${state.agency.id}/branding`, payload)
      setState((current) => ({ ...current, agency: { ...current.agency, branding: result.branding, computed_theme: result.computed_theme, design_options: result.design_options }, branding: result }))
      setForm(result.branding)
      setMessage("Branding settings saved.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function resetTheme() {
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/branding/reset`)
      setState((current) => ({ ...current, agency: { ...current.agency, branding: result.branding, computed_theme: result.computed_theme, design_options: result.design_options }, branding: result }))
      setForm(result.branding)
      setMessage("Theme reset to defaults.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function uploadLogo(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setError("")
    setMessage("")
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
      setError("Logo must be PNG, JPEG, or WEBP. SVG is not accepted.")
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      setError("Logo must be 2MB or smaller.")
      return
    }
    try {
      const dataBase64 = await fileToBase64(file)
      const result = await apiPost(`/api/agencies/${state.agency.id}/branding/logo`, {
        filename: file.name,
        content_type: file.type,
        data_base64: dataBase64,
      })
      setState((current) => ({ ...current, agency: { ...current.agency, branding: result.branding, computed_theme: result.computed_theme, design_options: result.design_options }, branding: result }))
      setForm(result.branding)
      setMessage("Logo uploaded.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function regenerateLogo() {
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/branding/logo/regenerate`)
      setState((current) => ({ ...current, agency: { ...current.agency, branding: result.branding, computed_theme: result.computed_theme, design_options: result.design_options }, branding: result }))
      setForm(result.branding)
      setMessage("Logo variants regenerated.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function removeLogo() {
    setError("")
    setMessage("")
    try {
      const result = await apiDelete(`/api/agencies/${state.agency.id}/branding/logo`)
      setState((current) => ({ ...current, agency: { ...current.agency, branding: result.branding, computed_theme: result.computed_theme, design_options: result.design_options }, branding: result }))
      setForm(result.branding)
      setMessage("Logo removed.")
    } catch (err) {
      setError(err.message)
    }
  }

  const options = state?.branding?.design_options || state?.agency?.design_options || {}
  const previewComputedTheme = computedThemeFromForm(form, options, state?.branding?.computed_theme || state?.agency?.computed_theme || {})
  const previewAgency = state?.agency ? { ...state.agency, branding: form, computed_theme: previewComputedTheme } : null
  const logoAssets = form.logo_assets || {}
  const sidebarLogo = logoAssets.sidebar?.url || form.logo_url
  const headerLogo = logoAssets.public_header?.url || form.logo_url
  const faviconLogo = logoAssets.favicon?.url || form.logo_url

  return (
    <AgencyLayout user={state?.me?.user} agency={previewAgency || state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        {state?.agency ? (
          <form className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr]" onSubmit={save}>
            <section className="grid gap-5 rounded-lg border border-slate-200 bg-white p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Agency Settings</p>
                  <h2 className="mt-2 text-2xl font-semibold text-slate-950">Branding, logo assets, and theme</h2>
                  <p className="mt-2 text-sm text-slate-600">Personalize the workspace through controlled presets and prepared logo variants. No arbitrary CSS or scripts.</p>
                </div>
                <div className="flex gap-2">
                  <button className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700" type="button" onClick={resetTheme}>Reset to text brand</button>
                  <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white" type="submit">Save settings</button>
                </div>
              </div>
              {message ? <p className="mt-4 rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
              {error ? <p className="mt-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}

              <div className="grid gap-5 rounded-lg border border-slate-200 p-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-blue-700">1. Brand identity</p>
                  <p className="mt-1 text-sm text-slate-600">Used across the AgencyOS shell, rendered documents, and public website fallback text.</p>
                </div>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Brand name
                  <input className="rounded-md border border-slate-200 px-3 py-2" value={form.brand_name || ""} onChange={(event) => setField("brand_name", event.target.value)} placeholder={state.agency.name} />
                </label>
              </div>

              <div className="grid gap-4 rounded-lg border border-slate-200 p-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-blue-700">2. Logo assets</p>
                  <h3 className="mt-1 text-sm font-semibold text-slate-900">Upload, prepare, preview</h3>
                  <p className="mt-1 text-sm text-slate-600">PNG, JPEG, or WEBP only. Max 2MB. SVG is blocked unless a sanitizer is added later.</p>
                </div>
                <div className="grid gap-4 lg:grid-cols-[170px_1fr]">
                  <div className="flex h-36 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 p-3">
                    {headerLogo ? <img className="max-h-full max-w-full object-contain" src={headerLogo} alt="Current agency logo" /> : <span className="text-sm text-slate-500">No logo</span>}
                  </div>
                  <div className="grid gap-3">
                    <input type="file" accept="image/png,image/jpeg,image/webp" onChange={uploadLogo} />
                    <div className="grid gap-3 md:grid-cols-2">
                      <Select label="Logo fit mode" value={form.logo_fit_mode || "contain"} onChange={(value) => setField("logo_fit_mode", value)} options={(options.logo_fit_modes || ["contain", "cover", "center"]).map((item) => [item, titleize(item)])} />
                      <Select label="Preferred usage" value={form.preferred_logo_usage || "horizontal"} onChange={(value) => setField("preferred_logo_usage", value)} options={(options.preferred_logo_usage || ["horizontal", "square", "compact"]).map((item) => [item, titleize(item)])} />
                    </div>
                    <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                      <input type="checkbox" checked={form.logo_public_usage_allowed !== false} onChange={(event) => setField("logo_public_usage_allowed", event.target.checked)} />
                      Allow public website to use prepared public-safe logo variants
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <button className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700" type="button" onClick={regenerateLogo}>Regenerate variants</button>
                      <button className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700" type="button" onClick={removeLogo}>Remove logo</button>
                    </div>
                    <p className="text-xs text-slate-500">Original uploads stay private; public surfaces receive generated PNG derivatives only.</p>
                  </div>
                </div>
              </div>

              <div className="grid gap-4 rounded-lg border border-slate-200 p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-blue-700">3–6. Typography, color palette, shape, and theme mode</p>
                <div className="grid gap-4 md:grid-cols-2">
                  <Select label="Font" value={form.font_family_key} onChange={(value) => setField("font_family_key", value)} options={optionEntries(options.fonts)} />
                  <Select label="Theme mode" value={form.theme_mode} onChange={(value) => setField("theme_mode", value)} options={(options.theme_modes || []).map((item) => [item, titleize(item)])} />
                  <Select label="Palette" value={form.color_palette_key} onChange={(value) => setField("color_palette_key", value)} options={optionEntries(options.palettes)} />
                  <Select label="Corner radius" value={form.corner_radius_key} onChange={(value) => setField("corner_radius_key", value)} options={optionEntries(options.corner_radii)} />
                  <Select label="Density" value={form.density_key} onChange={(value) => setField("density_key", value)} options={optionEntries(options.density)} />
                  <Select label="Field style" value={form.field_style_key} onChange={(value) => setField("field_style_key", value)} options={(options.field_styles || []).map((item) => [item, titleize(item)])} />
                  <Select label="Button style" value={form.button_style_key} onChange={(value) => setField("button_style_key", value)} options={(options.button_styles || []).map((item) => [item, titleize(item)])} />
                  <Select label="Date input style" value={form.calendar_style_key} onChange={(value) => setField("calendar_style_key", value)} options={(options.calendar_styles || []).map((item) => [item, titleize(item)])} />
                  <Select label="Card style" value={form.card_style_key} onChange={(value) => setField("card_style_key", value)} options={(options.card_styles || []).map((item) => [item, titleize(item)])} />
                </div>
              </div>
            </section>

            <aside className="rounded-lg border border-slate-200 bg-white p-6">
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">7. Live preview</p>
              <div className="mt-4 rounded-lg border p-5" style={agencyThemeStyle({ branding: form, computed_theme: previewComputedTheme })}>
                <div className="rounded-lg border p-4" style={{ background: "var(--aa-surface)", borderColor: "var(--aa-border)" }}>
                  <div className="grid gap-3 rounded-lg border p-3" style={{ borderColor: "var(--aa-border)", background: "var(--aa-muted-bg)" }}>
                    <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--aa-primary)" }}>Logo previews</p>
                    <div className="grid grid-cols-2 gap-3 text-xs" style={{ color: "var(--aa-muted-text)" }}>
                      <LogoPreview title="Sidebar" src={sidebarLogo} className="h-12 w-12 rounded-md object-contain p-1" />
                      <LogoPreview title="Top bar" src={headerLogo} className="h-10 max-w-[150px] object-contain" />
                      <LogoPreview title="Public header" src={headerLogo} className="h-11 max-w-[170px] object-contain" />
                      <LogoPreview title="Favicon" src={faviconLogo} className="h-8 w-8 rounded object-contain" />
                    </div>
                  </div>
                  <span className="rounded-full px-3 py-1 text-xs font-semibold" style={{ background: "var(--aa-muted-bg)", color: "var(--aa-primary)" }}>Request Builder</span>
                  <h3 className="mt-4 text-xl font-semibold" style={{ color: "var(--aa-primary)" }}>{form.brand_name || state.agency.name}</h3>
                  <p className="mt-2 text-sm" style={{ color: "var(--aa-muted-text)" }}>Theme variables apply to headers, navigation, buttons, inputs, cards, badges, and date fields.</p>
                  <div className="mt-4 grid gap-3">
                    <input className="rounded-md border px-3 py-2" value="SOF → JFK mobility assistance" readOnly />
                    <input className="rounded-md border px-3 py-2" type="date" readOnly />
                    <button className="rounded-md px-4 py-2 text-sm font-semibold" type="button">Create request</button>
                  </div>
                </div>
              </div>
            </aside>
          </form>
        ) : null}
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Select({ label, value, options, onChange }) {
  return (
    <label className="grid gap-2 text-sm font-medium text-slate-700">
      {label}
      <select className="rounded-md border border-slate-200 px-3 py-2" value={value || ""} onChange={(event) => onChange(event.target.value)}>
        {options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}
      </select>
    </label>
  )
}

function LogoPreview({ title, src, className }) {
  return (
    <div className="rounded-md border bg-white p-2">
      <p className="mb-2 font-semibold text-slate-600">{title}</p>
      {src ? <img className={className} src={src} alt={`${title} logo preview`} /> : <div className="flex h-10 items-center justify-center rounded bg-slate-100 text-[11px] text-slate-500">Text brand</div>}
    </div>
  )
}
