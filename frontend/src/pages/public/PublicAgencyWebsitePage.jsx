import { useEffect, useState } from "react"
import PublicLayout from "../../layouts/PublicLayout"
import { apiGet } from "../../lib/api"

export default function PublicAgencyWebsitePage({ slug }) {
  const [site, setSite] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    apiGet(`/api/public/websites/${slug}`).then(setSite).catch((err) => setError(err.message))
  }, [slug])

  if (error) {
    return (
      <PublicLayout>
        <section className="rounded-lg border border-slate-200 bg-white p-8">
          <h1 className="text-2xl font-semibold text-slate-950">Website not published</h1>
          <p className="mt-2 text-sm text-slate-600">{error}</p>
        </section>
      </PublicLayout>
    )
  }

  if (!site) {
    return (
      <PublicLayout>
        <p className="text-sm text-slate-600">Loading website…</p>
      </PublicLayout>
    )
  }

  const home = site.pages.find((page) => page.page_type === "home") || site.pages[0]
  const otherPages = site.pages.filter((page) => page.id !== home?.id)

  return (
    <PublicLayout>
      <header className="mb-8 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-3">
          {site.branding?.logo_url ? <img className="h-11 w-11 rounded-md border object-contain p-1" src={site.branding.logo_url} alt={`${site.settings.site_name} logo`} /> : null}
          <div>
            <p className="text-lg font-semibold text-slate-950">{site.settings.site_name}</p>
            <p className="text-sm text-slate-600">{site.settings.tagline}</p>
          </div>
        </div>
        <nav className="flex flex-wrap gap-2 text-sm font-semibold text-slate-700">
          {site.pages.map((page) => <a className="rounded-md px-3 py-2 hover:bg-slate-100" href={`#${page.slug}`} key={page.id}>{page.title}</a>)}
        </nav>
      </header>

      {home ? <RenderedPage page={home} settings={site.settings} primary /> : null}
      {otherPages.map((page) => <RenderedPage page={page} settings={site.settings} key={page.id} />)}
    </PublicLayout>
  )
}

function RenderedPage({ page, settings, primary = false }) {
  return (
    <main id={page.slug} className="mb-8 rounded-lg border border-slate-200 bg-white p-6">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">{primary ? settings.site_name : page.page_type.replaceAll("_", " ")}</p>
      <h1 className={`${primary ? "text-4xl md:text-5xl" : "text-3xl"} mt-3 font-semibold tracking-tight text-slate-950`}>{page.title}</h1>
      <div className="mt-8 grid gap-5">
        {(page.sections || []).map((section, index) => <RenderedSection section={section} settings={settings} key={index} />)}
      </div>
    </main>
  )
}

function RenderedSection({ section, settings }) {
  return (
    <section className="rounded-lg border border-slate-100 bg-slate-50 p-5">
      {section.eyebrow ? <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{section.eyebrow}</p> : null}
      <h2 className="mt-1 text-xl font-semibold text-slate-950">{section.heading}</h2>
      {section.body ? <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-600">{section.body}</p> : null}
      {section.items?.length ? <ul className="mt-4 grid gap-2 text-sm text-slate-700 sm:grid-cols-2">{section.items.map((item) => <li className="rounded-md bg-white p-3" key={item}>{item}</li>)}</ul> : null}
      {section.section_type === "contact" ? (
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          {settings.contact_email ? <div className="rounded-md bg-white p-3"><dt className="font-semibold text-slate-900">Email</dt><dd className="mt-1 text-slate-600">{settings.contact_email}</dd></div> : null}
          {settings.contact_phone ? <div className="rounded-md bg-white p-3"><dt className="font-semibold text-slate-900">Phone</dt><dd className="mt-1 text-slate-600">{settings.contact_phone}</dd></div> : null}
        </dl>
      ) : null}
      {section.cta_label ? <a className="mt-4 inline-flex rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href={section.cta_href || "/"}>{section.cta_label}</a> : null}
      {section.section_type === "intake_link" && settings.show_request_cta ? <a className="mt-4 inline-flex rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/">Request assistance</a> : null}
    </section>
  )
}
