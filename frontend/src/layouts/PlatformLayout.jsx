import Building2 from "lucide-react/dist/esm/icons/building-2.js"
import ClipboardCheck from "lucide-react/dist/esm/icons/clipboard-check.js"
import Database from "lucide-react/dist/esm/icons/database.js"
import FileText from "lucide-react/dist/esm/icons/file-text.js"
import GitBranch from "lucide-react/dist/esm/icons/git-branch.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import Tags from "lucide-react/dist/esm/icons/tags.js"
import { apiDeleteSession } from "../lib/api"
import { clearAuthSession } from "../lib/auth"

async function logout() {
  await apiDeleteSession().catch(() => null)
  clearAuthSession()
  window.location.href = "/login"
}

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
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/agencies">
              <Building2 className="h-4 w-4" />
              Agencies
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/airlines">
              <Plane className="h-4 w-4" />
              Airlines / Knowledge
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/airline-policy-ingestion">
              <FileText className="h-4 w-4" />
              Policy Ingestion
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/service-taxonomy">
              <Tags className="h-4 w-4" />
              Service Taxonomy
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/reference">
              <Database className="h-4 w-4" />
              Reference Data
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/rules-services">
              <ClipboardCheck className="h-4 w-4" />
              Rules & Services
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/document-templates">
              <FileText className="h-4 w-4" />
              Documents
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/gds-parser">
              <Database className="h-4 w-4" />
              GDS Parser
            </a>
            <a className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" href="/platform/blueprint">
              <GitBranch className="h-4 w-4" />
              Blueprint
            </a>
          </nav>
          <div className="flex items-center gap-3">
            {user ? <p className="text-sm text-slate-500">{user.full_name}</p> : null}
            <button className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100" type="button" onClick={logout}>Logout</button>
          </div>
        </div>
      </aside>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  )
}
