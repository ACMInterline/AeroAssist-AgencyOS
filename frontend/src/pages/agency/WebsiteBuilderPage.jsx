import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const pageTypes = ["home", "about", "services", "contact", "custom"]
const sectionTypes = ["hero", "text", "services", "cta", "contact", "intake_link"]

const blankSection = () => ({
  section_type: "text",
  eyebrow: "",
  heading: "New section",
  body: "",
  cta_label: "",
  cta_href: "",
  items: [],
  sort_order: 0,
})

export default function WebsiteBuilderPage() {
  const [state, setState] = useState(null)
  const [settings, setSettings] = useState(null)
  const [pages, setPages] = useState([])
  const [selectedPageId, setSelectedPageId] = useState("")
  const [pageForm, setPageForm] = useState(null)
  const [newPage, setNewPage] = useState({ title: "Home", slug: "home", page_type: "home" })
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [website, pageList] = context.agency ? await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/website`),
      apiGet(`/api/agencies/${context.agency.id}/website/pages`),
    ]) : [{ settings: null }, { items: [] }]
    setState(context)
    setSettings(website.settings)
    setPages(pageList.items)
    const firstPage = pageList.items[0] || null
    setSelectedPageId((current) => current || firstPage?.id || "")
    setPageForm(firstPage)
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedPage = useMemo(() => pages.find((page) => page.id === selectedPageId) || pages[0] || null, [pages, selectedPageId])

  useEffect(() => {
    if (selectedPage) setPageForm(selectedPage)
  }, [selectedPage?.id])

  function setSetting(name, value) {
    setSettings((current) => ({ ...current, [name]: value }))
  }

  function setPage(name, value) {
    setPageForm((current) => ({ ...current, [name]: value }))
  }

  function updateSection(index, patch) {
    setPageForm((current) => ({
      ...current,
      sections: (current.sections || []).map((section, sectionIndex) => sectionIndex === index ? { ...section, ...patch } : section),
    }))
  }

  async function saveSettings(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const result = await apiPut(`/api/agencies/${state.agency.id}/website`, {
        site_name: settings.site_name,
        slug: settings.slug,
        tagline: settings.tagline || null,
        status: settings.status,
        seo_title: settings.seo_title || null,
        seo_description: settings.seo_description || null,
        contact_email: settings.contact_email || null,
        contact_phone: settings.contact_phone || null,
        show_request_cta: settings.show_request_cta,
      })
      setSettings(result.settings)
      setMessage("Website settings saved.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function createPage(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/website/pages`, {
        title: newPage.title,
        slug: newPage.slug,
        page_type: newPage.page_type,
        sections: [blankSection()],
      })
      setPages((current) => [...current, result.page])
      setSelectedPageId(result.page.id)
      setPageForm(result.page)
      setMessage("Website page created.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function savePage(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const result = await apiPut(`/api/agencies/${state.agency.id}/website/pages/${pageForm.id}`, {
        title: pageForm.title,
        slug: pageForm.slug,
        page_type: pageForm.page_type,
        seo_title: pageForm.seo_title || null,
        seo_description: pageForm.seo_description || null,
        sections: (pageForm.sections || []).map((section, index) => ({ ...section, sort_order: index })),
      })
      setPages((current) => current.map((page) => page.id === result.page.id ? result.page : page))
      setPageForm(result.page)
      setMessage("Page saved.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function publishPage() {
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/website/pages/${pageForm.id}/publish`)
      setPages((current) => current.map((page) => page.id === result.page.id ? result.page : page))
      setPageForm(result.page)
      setMessage("Page published.")
    } catch (err) {
      setError(err.message)
    }
  }

  async function archivePage() {
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/website/pages/${pageForm.id}/archive`)
      setPages((current) => current.map((page) => page.id === result.page.id ? result.page : page))
      setPageForm(result.page)
      setMessage("Page archived.")
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Website / CMS</p>
                <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Agency website builder</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Create controlled public website content from safe sections. No custom code, CMS publishing automation, pricing, or domain routing changes are included in this phase.</p>
              </div>
              {settings?.slug ? <a className="rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" href={`/site/${settings.slug}`} target="_blank" rel="noreferrer">Open public preview</a> : null}
            </div>
            {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          </section>

          {settings ? (
            <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
              <form className="space-y-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveSettings}>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Site settings</p>
                  <h3 className="mt-1 text-lg font-semibold text-slate-950">Public identity</h3>
                </div>
                <Field label="Site name" value={settings.site_name || ""} onChange={(value) => setSetting("site_name", value)} required />
                <Field label="Public slug" value={settings.slug || ""} onChange={(value) => setSetting("slug", value)} required help={`Public route: /site/${settings.slug || "agency"}`} />
                <Field label="Tagline" value={settings.tagline || ""} onChange={(value) => setSetting("tagline", value)} />
                <Select label="Website status" value={settings.status || "not_configured"} onChange={(value) => setSetting("status", value)} options={["not_configured", "draft", "active", "suspended"]} />
                <Field label="SEO title" value={settings.seo_title || ""} onChange={(value) => setSetting("seo_title", value)} />
                <TextArea label="SEO description" value={settings.seo_description || ""} onChange={(value) => setSetting("seo_description", value)} />
                <div className="grid gap-3 md:grid-cols-2">
                  <Field label="Contact email" type="email" value={settings.contact_email || ""} onChange={(value) => setSetting("contact_email", value)} />
                  <Field label="Contact phone" value={settings.contact_phone || ""} onChange={(value) => setSetting("contact_phone", value)} />
                </div>
                <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                  <input type="checkbox" checked={Boolean(settings.show_request_cta)} onChange={(event) => setSetting("show_request_cta", event.target.checked)} />
                  Show request-assistance CTA
                </label>
                <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Save settings</button>
              </form>

              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Pages</p>
                    <h3 className="mt-1 text-lg font-semibold text-slate-950">Controlled page builder</h3>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{pages.length} pages</span>
                </div>

                <form className="mt-4 grid gap-3 rounded-md border border-slate-100 bg-slate-50 p-3 md:grid-cols-[1fr_1fr_160px_auto]" onSubmit={createPage}>
                  <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Page title" value={newPage.title} onChange={(event) => setNewPage({ ...newPage, title: event.target.value })} required />
                  <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="page-slug" value={newPage.slug} onChange={(event) => setNewPage({ ...newPage, slug: event.target.value })} required />
                  <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={newPage.page_type} onChange={(event) => setNewPage({ ...newPage, page_type: event.target.value })}>{pageTypes.map((type) => <option key={type} value={type}>{type}</option>)}</select>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="submit">Add page</button>
                </form>

                <div className="mt-4 grid gap-2">
                  {pages.map((page) => (
                    <button className={`rounded-md border px-3 py-3 text-left text-sm ${page.id === pageForm?.id ? "border-blue-300 bg-blue-50" : "border-slate-200 bg-white"}`} type="button" onClick={() => setSelectedPageId(page.id)} key={page.id}>
                      <span className="font-semibold text-slate-950">{page.title}</span>
                      <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{page.status}</span>
                      <span className="mt-1 block text-xs text-slate-500">/{page.slug} · {page.page_type}</span>
                    </button>
                  ))}
                  {!pages.length ? <EmptyState title="No pages yet" body="Create a home page to start the agency website." /> : null}
                </div>
              </section>
            </div>
          ) : null}

          {pageForm ? (
            <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
              <form className="space-y-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={savePage}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Edit page</p>
                    <h3 className="mt-1 text-lg font-semibold text-slate-950">{pageForm.title}</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={publishPage}>Publish</button>
                    <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-rose-700" type="button" onClick={archivePage}>Archive</button>
                    <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Save page</button>
                  </div>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <Field label="Title" value={pageForm.title || ""} onChange={(value) => setPage("title", value)} required />
                  <Field label="Slug" value={pageForm.slug || ""} onChange={(value) => setPage("slug", value)} required />
                  <Select label="Type" value={pageForm.page_type || "custom"} onChange={(value) => setPage("page_type", value)} options={pageTypes} />
                </div>
                <Field label="SEO title" value={pageForm.seo_title || ""} onChange={(value) => setPage("seo_title", value)} />
                <TextArea label="SEO description" value={pageForm.seo_description || ""} onChange={(value) => setPage("seo_description", value)} />

                <div className="space-y-3">
                  {(pageForm.sections || []).map((section, index) => (
                    <div className="rounded-lg border border-slate-200 p-4" key={index}>
                      <div className="grid gap-3 md:grid-cols-3">
                        <Select label="Section type" value={section.section_type} onChange={(value) => updateSection(index, { section_type: value })} options={sectionTypes} />
                        <Field label="Eyebrow" value={section.eyebrow || ""} onChange={(value) => updateSection(index, { eyebrow: value })} />
                        <Field label="Heading" value={section.heading || ""} onChange={(value) => updateSection(index, { heading: value })} required />
                      </div>
                      <TextArea label="Body" value={section.body || ""} onChange={(value) => updateSection(index, { body: value })} />
                      <div className="grid gap-3 md:grid-cols-2">
                        <Field label="CTA label" value={section.cta_label || ""} onChange={(value) => updateSection(index, { cta_label: value })} />
                        <Field label="CTA href" value={section.cta_href || ""} onChange={(value) => updateSection(index, { cta_href: value })} />
                      </div>
                      <TextArea label="List items, one per line" value={(section.items || []).join("\n")} onChange={(value) => updateSection(index, { items: value.split("\n").map((item) => item.trim()).filter(Boolean) })} />
                      <button className="mt-2 text-sm font-semibold text-rose-700" type="button" onClick={() => setPage("sections", (pageForm.sections || []).filter((_, itemIndex) => itemIndex !== index))}>Remove section</button>
                    </div>
                  ))}
                </div>
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => setPage("sections", [...(pageForm.sections || []), blankSection()])}>Add section</button>
              </form>

              <WebsitePreview settings={settings} page={pageForm} />
            </div>
          ) : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function WebsitePreview({ settings, page }) {
  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Live Preview</p>
      <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
        <div className="bg-slate-950 p-4 text-white">
          <p className="text-sm font-semibold">{settings?.site_name}</p>
          <h3 className="mt-4 text-2xl font-semibold">{page?.title}</h3>
          <p className="mt-2 text-sm text-slate-300">{settings?.tagline}</p>
        </div>
        <div className="space-y-4 p-4">
          {(page?.sections || []).map((section, index) => (
            <section className="rounded-md border border-slate-200 p-4" key={index}>
              {section.eyebrow ? <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{section.eyebrow}</p> : null}
              <h4 className="mt-1 font-semibold text-slate-950">{section.heading}</h4>
              {section.body ? <p className="mt-2 text-sm leading-6 text-slate-600">{section.body}</p> : null}
              {section.items?.length ? <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-600">{section.items.map((item) => <li key={item}>{item}</li>)}</ul> : null}
              {section.cta_label ? <span className="mt-3 inline-flex rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">{section.cta_label}</span> : null}
            </section>
          ))}
        </div>
      </div>
    </aside>
  )
}

function Field({ label, value, onChange, type = "text", required = false, help }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} required={required} onChange={(event) => onChange(event.target.value)} />{help ? <span className="mt-1 block text-xs text-slate-500">{help}</span> : null}</label>
}

function TextArea({ label, value, onChange }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<textarea className="mt-2 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, onChange, options }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option} value={option}>{option.replaceAll("_", " ")}</option>)}</select></label>
}
