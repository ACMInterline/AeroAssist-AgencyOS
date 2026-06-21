import { Building2, Plane, ShieldCheck } from "lucide-react"

export default function PlatformLayout({ children, user }) {
  return (
    <div className="min-h-screen bg-slate-100">
      <aside className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">AeroAssist Global</p>
            <h1 className="text-lg font-semibold text-slate-950">Platform Owner Layer</h1>
          </div>
          <nav className="flex items-center gap-2 text-sm">
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform">
              <ShieldCheck className="h-4 w-4" />
              Summary
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/agency">
              <Building2 className="h-4 w-4" />
              Agency
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/airlines">
              <Plane className="h-4 w-4" />
              Airlines / Knowledge
            </a>
          </nav>
          {user ? <p className="text-sm text-slate-500">{user.full_name}</p> : null}
        </div>
      </aside>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  )
}
