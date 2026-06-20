import PublicLayout from "../../layouts/PublicLayout"

export default function HomePage() {
  return (
    <PublicLayout>
      <section className="grid gap-6 md:grid-cols-[1.4fr_1fr] md:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Phase 1 Foundation</p>
          <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-normal text-slate-950 md:text-5xl">
            AeroAssist AgencyOS
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Multi-tenant operating platform foundation for micro and small travel agencies.
            This build establishes platform identity, agency workspace setup, roles, reference
            data, and tenant-aware API scaffolding.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/login">
              Open demo login
            </a>
            <a className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800" href="/platform">
              View platform foundation
            </a>
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-base font-semibold text-slate-950">Implemented layers</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>AeroAssist Global / Platform Owner foundation</li>
            <li>Agency Workspace identity and settings foundation</li>
            <li>Global reference data seed layer</li>
            <li>Audit event scaffolding</li>
          </ul>
        </div>
      </section>
    </PublicLayout>
  )
}
