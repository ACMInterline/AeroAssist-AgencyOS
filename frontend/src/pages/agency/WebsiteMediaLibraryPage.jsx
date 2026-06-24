import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiDelete, apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const usageContexts = ["hero", "section_image", "card_image", "gallery", "background", "document", "general"]
const assetTypes = ["image", "background", "illustration", "icon"]

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1] || "")
    reader.onerror = () => reject(new Error("Media file could not be read."))
    reader.readAsDataURL(file)
  })
}

export default function WebsiteMediaLibraryPage() {
  const [state, setState] = useState(null)
  const [assets, setAssets] = useState([])
  const [form, setForm] = useState({ title: "", alt_text: "", caption: "", usage_context: "general", asset_type: "image", public_usage_allowed: true })
  const [selectedFile, setSelectedFile] = useState(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const media = context.agency ? await apiGet(`/api/agencies/${context.agency.id}/website/media`) : { items: [] }
    setState(context)
    setAssets(media.items)
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function upload(event) {
    event.preventDefault()
    if (!selectedFile) {
      setError("Choose an image before uploading.")
      return
    }
    setError("")
    setMessage("")
    try {
      const dataBase64 = await fileToBase64(selectedFile)
      const result = await apiPost(`/api/agencies/${state.agency.id}/website/media`, {
        filename: selectedFile.name,
        content_type: selectedFile.type,
        data_base64: dataBase64,
        ...form,
      })
      setAssets((current) => [result.asset, ...current])
      setSelectedFile(null)
      setForm({ title: "", alt_text: "", caption: "", usage_context: "general", asset_type: "image", public_usage_allowed: true })
      setMessage("Media asset uploaded and variants generated.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function updateAsset(asset, patch) {
    setError("")
    setMessage("")
    try {
      const result = await apiPut(`/api/agencies/${state.agency.id}/website/media/${asset.id}`, { ...patch })
      setAssets((current) => current.map((item) => item.id === asset.id ? result.asset : item))
      setMessage("Media asset updated.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function archiveAsset(asset) {
    setError("")
    setMessage("")
    try {
      const result = await apiDelete(`/api/agencies/${state.agency.id}/website/media/${asset.id}`)
      setAssets((current) => current.map((item) => item.id === asset.id ? result.asset : item))
      setMessage("Media asset archived.")
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Website / CMS</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Media library</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Upload public-safe website images with generated thumbnail, card, hero, and normalized variants. SVG, raw URLs, and private filesystem paths are not allowed.</p>
            {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          </section>

          <form className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5 lg:grid-cols-3" onSubmit={upload}>
            <label className="block text-sm font-medium text-slate-700">Image file<input className="mt-2 w-full text-sm" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setSelectedFile(event.target.files?.[0] || null)} /></label>
            <Field label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} required />
            <Field label="Alt text" value={form.alt_text} onChange={(value) => setForm({ ...form, alt_text: value })} required />
            <Select label="Asset type" value={form.asset_type} options={assetTypes} onChange={(value) => setForm({ ...form, asset_type: value })} />
            <Select label="Usage context" value={form.usage_context} options={usageContexts} onChange={(value) => setForm({ ...form, usage_context: value })} />
            <Field label="Caption" value={form.caption} onChange={(value) => setForm({ ...form, caption: value })} />
            <label className="flex items-center gap-2 text-sm font-medium text-slate-700"><input type="checkbox" checked={form.public_usage_allowed} onChange={(event) => setForm({ ...form, public_usage_allowed: event.target.checked })} /> Allow public website usage</label>
            <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white lg:w-fit" type="submit">Upload image</button>
          </form>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {assets.map((asset) => (
              <article className="overflow-hidden rounded-lg border border-slate-200 bg-white" key={asset.id}>
                <div className="flex h-44 items-center justify-center bg-slate-100">
                  {asset.thumbnail_url ? <img className="h-full w-full object-cover" src={asset.thumbnail_url} alt={asset.alt_text} /> : <span className="text-sm text-slate-500">No preview</span>}
                </div>
                <div className="space-y-3 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-slate-950">{asset.title}</p>
                      <p className="text-xs text-slate-500">{asset.mime_type} · {asset.width_px}×{asset.height_px} · {Math.round((asset.file_size_bytes || 0) / 1024)} KB</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{asset.status}</span>
                  </div>
                  <Field label="Title" value={asset.title || ""} onChange={(value) => updateAsset(asset, { title: value })} />
                  <Field label="Alt text" value={asset.alt_text || ""} onChange={(value) => updateAsset(asset, { alt_text: value })} />
                  <Select label="Usage" value={asset.usage_context || "general"} options={usageContexts} onChange={(value) => updateAsset(asset, { usage_context: value })} />
                  <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={Boolean(asset.public_usage_allowed)} onChange={(event) => updateAsset(asset, { public_usage_allowed: event.target.checked })} /> Public usage allowed</label>
                  <button className="text-sm font-semibold text-rose-700" type="button" onClick={() => archiveAsset(asset)}>Archive asset</button>
                </div>
              </article>
            ))}
            {!assets.length ? <EmptyState title="No media assets yet" body="Upload the first website image to use in hero, card, CTA, and image/text sections." /> : null}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Field({ label, value, onChange, required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value || ""} required={required} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, options, onChange }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value || ""} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{option.replaceAll("_", " ")}</option>)}</select></label>
}
