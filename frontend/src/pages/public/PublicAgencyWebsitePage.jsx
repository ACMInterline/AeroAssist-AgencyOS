import { useEffect, useMemo, useState } from "react"
import PublicLayout from "../../layouts/PublicLayout"
import { apiGet, apiPost } from "../../lib/api"
import { agencyThemeStyle } from "../../lib/theme"

const serviceOptions = ["booking_or_planning", "mobility_assistance", "medical_travel", "pet_travel", "child_or_unaccompanied_minor", "special_baggage", "documents_or_visa", "disruption_or_claims", "other"]

export default function PublicAgencyWebsitePage({ slug, pageSlug, requestMode = false }) {
  const [site, setSite] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    const path = pageSlug ? `/api/public/websites/${slug}/pages/${pageSlug}` : `/api/public/websites/${slug}`
    apiGet(path).then(setSite).catch((err) => setError(err.message))
  }, [slug, pageSlug])

  const activePage = useMemo(() => {
    if (!site?.pages?.length) return null
    if (pageSlug) return site.pages[0]
    return site.pages.find((page) => page.page_type === "home") || site.pages[0]
  }, [site, pageSlug])

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
    return <PublicLayout><p className="text-sm text-slate-600">Loading website…</p></PublicLayout>
  }

  return (
    <div style={agencyThemeStyle({ computed_theme: site.computed_theme, ...site.branding })}>
    <PublicLayout>
      <SiteHeader site={site} slug={slug} />
      {requestMode ? <WebsiteRequestForm site={site} slug={slug} pageSlug={pageSlug} /> : <RenderedPage page={activePage} site={site} slug={slug} />}
    </PublicLayout>
    </div>
  )
}

function SiteHeader({ site, slug }) {
  const publicLogo = site.branding?.logo_assets?.public_header?.url || site.branding?.logo_url
  const brandName = site.branding?.brand_name || site.settings.site_name
  return (
    <header className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-sm backdrop-blur">
      <a className="flex items-center gap-3" href={`/site/${slug}`}>
        {publicLogo ? <img className="h-12 max-w-[220px] rounded-md border object-contain p-1" src={publicLogo} alt={`${brandName} logo`} /> : null}
        <div>
          <p className="text-lg font-semibold text-slate-950">{brandName}</p>
          <p className="text-sm text-slate-600">{site.settings.tagline}</p>
        </div>
      </a>
      <nav className="flex flex-wrap gap-2 text-sm font-semibold text-slate-700">
        {(site.navigation || site.pages || []).map((page) => <a className="rounded-md px-3 py-2 hover:bg-slate-100" href={page.page_type === "home" ? `/site/${slug}` : `/site/${slug}/${page.slug}`} key={page.slug}>{page.title}</a>)}
        {site.settings.show_request_cta ? <a className="rounded-full px-4 py-2 text-white shadow-sm" style={{ background: "var(--aa-primary)" }} href={`/site/${slug}/request`}>Request assistance</a> : null}
      </nav>
    </header>
  )
}

function RenderedPage({ page, site, slug }) {
  if (!page) return null
  return (
    <main id={page.slug} className="mb-8 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 bg-gradient-to-br from-slate-950 to-blue-950 p-8 text-white md:p-12">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-200">{page.page_type.replaceAll("_", " ")}</p>
        <h1 className="mt-4 max-w-4xl text-4xl font-semibold tracking-tight md:text-6xl">{page.title}</h1>
        {site.settings.tagline ? <p className="mt-4 max-w-2xl text-base leading-7 text-blue-100">{site.settings.tagline}</p> : null}
      </div>
      <div className="grid gap-8 p-5 md:p-8">
        {(page.sections || []).map((section, index) => <RenderedSection section={section} settings={site.settings} mediaAssets={site.media_assets || {}} slug={slug} key={index} />)}
      </div>
    </main>
  )
}

function RenderedSection({ section, settings, mediaAssets, slug }) {
  const cards = section.cards || []
  const primaryTarget = normalizeTarget(section.primary_cta_target || section.cta_href, slug)
  const secondaryTarget = normalizeTarget(section.secondary_cta_target, slug)
  const media = section.image_asset_id ? mediaAssets[section.image_asset_id] : null
  const imageUrl = media?.hero_url || media?.card_url || media?.thumbnail_url
  const image = imageUrl ? <img className="h-full min-h-64 w-full rounded-2xl object-cover shadow-sm" src={imageUrl} alt={media.alt_text || section.heading} /> : null
  const isHero = section.section_type === "hero"
  const isImageText = section.section_type === "image_text"
  return (
    <section className={`rounded-3xl border border-slate-100 bg-slate-50/80 p-6 md:p-8 ${section.alignment === "center" ? "text-center" : ""}`}>
      <div className={`${(isHero || isImageText) && image ? `grid items-center gap-8 lg:grid-cols-2 ${section.image_position === "left" ? "lg:[&>*:first-child]:order-2" : ""}` : ""}`}>
        <div>
      {section.eyebrow ? <p className="text-xs font-bold uppercase tracking-[0.18em]" style={{ color: "var(--aa-primary)" }}>{section.eyebrow}</p> : null}
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">{section.headline || section.heading}</h2>
      {section.subheadline ? <p className="mt-3 text-lg leading-8 text-slate-600">{section.subheadline}</p> : null}
      {section.body ? <p className="mt-4 whitespace-pre-line text-base leading-8 text-slate-600">{section.body}</p> : null}
      {section.items?.length ? <ul className="mt-5 grid gap-3 text-sm text-slate-700 sm:grid-cols-2">{section.items.map((item) => <li className="rounded-2xl bg-white p-4 shadow-sm" key={item}>{item}</li>)}</ul> : null}
        </div>
        {image ? <div>{image}{media?.caption ? <p className="mt-2 text-xs text-slate-500">{media.caption}</p> : null}</div> : null}
      </div>
      {cards.length ? <CardGrid cards={cards} type={section.section_type} /> : null}
      {section.section_type === "contact_details" || section.section_type === "contact" ? <ContactDetails settings={settings} /> : null}
      <div className="mt-6 flex flex-wrap gap-3">
        {section.primary_cta_label || section.cta_label ? <a className="inline-flex rounded-full px-5 py-3 text-sm font-semibold text-white shadow-sm" style={{ background: "var(--aa-primary)" }} href={primaryTarget}>{section.primary_cta_label || section.cta_label}</a> : null}
        {section.secondary_cta_label ? <a className="inline-flex rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800" href={secondaryTarget}>{section.secondary_cta_label}</a> : null}
        {section.section_type === "request_form_cta" || section.section_type === "intake_link" ? <a className="inline-flex rounded-full px-5 py-3 text-sm font-semibold text-white shadow-sm" style={{ background: "var(--aa-primary)" }} href={`/site/${slug}/request`}>Request assistance</a> : null}
      </div>
    </section>
  )
}

function CardGrid({ cards, type }) {
  return (
    <div className="mt-5 grid gap-4 md:grid-cols-2">
      {cards.map((card, index) => (
        <article className="rounded-2xl bg-white p-5 shadow-sm" key={index}>
          <p className="font-semibold text-slate-950">{card.title || card.question || card.name || card.label}</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">{card.description || card.answer || card.quote}</p>
          {type === "testimonials" && card.role_or_context ? <p className="mt-2 text-xs font-semibold text-slate-500">{card.role_or_context}</p> : null}
        </article>
      ))}
    </div>
  )
}

function ContactDetails({ settings }) {
  return (
    <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
      {settings.contact_email ? <div className="rounded-md bg-white p-3"><dt className="font-semibold text-slate-900">Email</dt><dd className="mt-1 text-slate-600">{settings.contact_email}</dd></div> : null}
      {settings.contact_phone ? <div className="rounded-md bg-white p-3"><dt className="font-semibold text-slate-900">Phone</dt><dd className="mt-1 text-slate-600">{settings.contact_phone}</dd></div> : null}
    </dl>
  )
}

function WebsiteRequestForm({ site, slug, pageSlug }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "", organization: "", origin: "", destination: "", departure_date: "", passenger_count: 1, service: "booking_or_planning", message: "", consent: false })
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState("")

  async function submit(event) {
    event.preventDefault()
    setError("")
    try {
      const result = await apiPost(`/api/public/websites/${slug}/request${pageSlug ? `?page_slug=${pageSlug}` : ""}`, {
        contact: { name: form.name, email: form.email || undefined, phone: form.phone || undefined, organization: form.organization || undefined, privacy_policy_accepted: form.consent, data_processing_consent: form.consent },
        travel: { origin: form.origin || undefined, destination: form.destination || undefined, departure_date: form.departure_date || undefined, passenger_count: Number(form.passenger_count) || 1, itinerary_notes: form.message || undefined },
        services: { selected_service_categories: [form.service.replaceAll("_", " ")], [form.service]: true },
        request_details: form.message || undefined,
      })
      setSuccess(result.intake)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-10">
      <p className="text-sm font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--aa-primary)" }}>{site.settings.site_name}</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 md:text-5xl">Request assistance</h1>
      <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">Tell the agency what you need. This creates an intake for staff review; it does not create a booking or operational request automatically.</p>
      {success ? <p className="mt-6 rounded-2xl bg-emerald-50 p-5 text-sm text-emerald-900">We received your request. Reference: <span className="font-semibold">{success.reference_code}</span></p> : (
        <form className="mt-6 grid gap-5 md:grid-cols-2" onSubmit={submit}>
          <Field label="Name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} required />
          <Field label="Email" type="email" value={form.email} onChange={(value) => setForm({ ...form, email: value })} />
          <Field label="Phone" value={form.phone} onChange={(value) => setForm({ ...form, phone: value })} />
          <Field label="Organization" value={form.organization} onChange={(value) => setForm({ ...form, organization: value })} />
          <Field label="Departure / origin" value={form.origin} onChange={(value) => setForm({ ...form, origin: value })} />
          <Field label="Arrival / destination" value={form.destination} onChange={(value) => setForm({ ...form, destination: value })} />
          <Field label="Travel date" type="date" value={form.departure_date} onChange={(value) => setForm({ ...form, departure_date: value })} />
          <Field label="Passengers" type="number" value={form.passenger_count} onChange={(value) => setForm({ ...form, passenger_count: value })} />
          <label className="block text-sm font-medium text-slate-700">Assistance interest<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.service} onChange={(event) => setForm({ ...form, service: event.target.value })}>{serviceOptions.map((item) => <option value={item} key={item}>{item.replaceAll("_", " ")}</option>)}</select></label>
          <label className="block text-sm font-medium text-slate-700 md:col-span-2">Message<textarea className="mt-2 min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.message} required onChange={(event) => setForm({ ...form, message: event.target.value })} /></label>
          <label className="flex gap-3 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 md:col-span-2"><input type="checkbox" checked={form.consent} onChange={(event) => setForm({ ...form, consent: event.target.checked })} required /> I consent to this agency reviewing my request, processing the information provided, and contacting me about this request.</label>
          {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800 md:col-span-2">{error}</p> : null}
          <button className="rounded-full px-5 py-3 text-sm font-semibold text-white shadow-sm md:w-fit" style={{ background: "var(--aa-primary)" }} type="submit">Submit website request</button>
        </form>
      )}
    </section>
  )
}

function normalizeTarget(value, slug) {
  if (!value) return `/site/${slug}/request`
  if (value === "/request") return `/site/${slug}/request`
  return value
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} required={required} onChange={(event) => onChange(event.target.value)} /></label>
}
