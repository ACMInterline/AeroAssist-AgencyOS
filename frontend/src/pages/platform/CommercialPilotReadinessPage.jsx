import { useEffect, useState } from "react"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import OperationalAlert from "../../components/OperationalAlert"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"
import { productLabel } from "../../lib/productLanguage"

export default function CommercialPilotReadinessPage() {
  const [state, setState] = useState(null)
  const [agencyId, setAgencyId] = useState("")
  const [error, setError] = useState("")

  async function load(nextAgencyId = agencyId) {
    const [me, agencies, assessment] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/commercial-pilot-readiness${nextAgencyId ? `?agency_id=${encodeURIComponent(nextAgencyId)}` : ""}`),
    ])
    setState({ me, agencies: agencies.items || [], assessment })
    setError("")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function changeAgency(value) {
    setAgencyId(value)
    setState((current) => current ? { ...current, assessment: null } : current)
    try {
      await load(value)
    } catch (err) {
      setError(err.message)
    }
  }

  const assessment = state?.assessment
  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <main className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Platform", href: "/platform" }, { label: "Commercial Pilot readiness" }]}
            eyebrow="Commercial Pilot"
            title="Commercial Pilot readiness"
            description="A deterministic product-readiness view for controlled agency use. It supplements, and never replaces, the Phase 57 production release gate and human sign-off."
            status={assessment ? <StatusBadge label={productLabel(assessment.status)} status={assessment.status === "conditionally_ready" ? "warning" : assessment.status} /> : null}
            actions={<label className="grid gap-1 text-xs font-semibold text-slate-600">Agency scope<select className="field min-w-56 text-sm" value={agencyId} onChange={(event) => changeAgency(event.target.value)}><option value="">All product capabilities</option>{(state?.agencies || []).map((agency) => <option value={agency.id} key={agency.id}>{agency.name}</option>)}</select></label>}
          />

          {error ? <OperationalAlert title="Readiness could not be assessed" tone="error">{error}</OperationalAlert> : null}
          {assessment ? <>
            <section className="grid gap-3 sm:grid-cols-3">
              <Metric label="Blocking checks" value={assessment.blocker_count} tone={assessment.blocker_count ? "danger" : "success"} />
              <Metric label="Warnings" value={assessment.warning_count} tone={assessment.warning_count ? "warning" : "success"} />
              <Metric label="Registered pilot documents" value={assessment.documentation?.length || 0} tone="default" />
            </section>

            <OperationalAlert title="Phase 57 governance remains authoritative" tone="info">Commercial Pilot readiness does not approve a release. Production evidence, backup evidence, tenant-isolation evidence, rollback reference, assessment snapshot, and authorized human sign-off remain governed by Phase 57.</OperationalAlert>

            <section>
              <h2 className="text-base font-semibold text-slate-950">Readiness checks</h2>
              <div className="mt-3 divide-y divide-slate-200 border-y border-slate-200 bg-white">
                {assessment.checks.map((item) => <div className="flex flex-wrap items-start justify-between gap-4 px-4 py-4" key={item.key}><div className="flex min-w-0 gap-3"><CheckCircle2 aria-hidden="true" className={`mt-0.5 h-5 w-5 shrink-0 ${item.status === "pass" ? "text-emerald-600" : item.status === "warning" ? "text-amber-600" : "text-red-600"}`} /><div><h3 className="text-sm font-semibold text-slate-950">{item.label}</h3><p className="mt-1 text-sm text-slate-600">{item.summary}</p>{item.remediation && item.status !== "pass" ? <p className="mt-2 text-xs font-medium text-slate-700">Next: {item.remediation}</p> : null}</div></div><StatusBadge label={item.status === "pass" ? "Pass" : productLabel(item.status)} status={item.status === "pass" ? "ready" : item.status} /></div>)}
              </div>
            </section>

            <section>
              <div className="flex items-start gap-3"><ShieldCheck aria-hidden="true" className="mt-0.5 h-5 w-5 text-blue-700" /><div><h2 className="text-base font-semibold text-slate-950">Controlled pilot package</h2><p className="mt-1 text-sm text-slate-600">Stable repository references for onboarding, daily use, recovery, incidents, feedback, acceptance, and exit.</p></div></div>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {assessment.documentation.map((item) => <div className="border-y border-slate-200 bg-white px-4 py-3" key={item.key}><p className="text-sm font-semibold text-slate-900">{item.label}</p><p className="mt-1 break-all text-xs text-slate-500">{item.path}</p></div>)}
              </div>
            </section>
          </> : null}
        </main>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Metric({ label, tone, value }) {
  const toneClass = tone === "danger" ? "text-red-700" : tone === "warning" ? "text-amber-700" : tone === "success" ? "text-emerald-700" : "text-slate-950"
  return <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className={`mt-2 text-2xl font-semibold ${toneClass}`}>{value}</p></div>
}
