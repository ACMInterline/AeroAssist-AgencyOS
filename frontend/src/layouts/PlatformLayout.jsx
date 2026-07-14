import Building2 from "lucide-react/dist/esm/icons/building-2.js"
import ClipboardCheck from "lucide-react/dist/esm/icons/clipboard-check.js"
import Database from "lucide-react/dist/esm/icons/database.js"
import FileText from "lucide-react/dist/esm/icons/file-text.js"
import GitBranch from "lucide-react/dist/esm/icons/git-branch.js"
import Layers3 from "lucide-react/dist/esm/icons/layers-3.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import Phone from "lucide-react/dist/esm/icons/phone.js"
import Rows3 from "lucide-react/dist/esm/icons/rows-3.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import Tags from "lucide-react/dist/esm/icons/tags.js"
import { apiDeleteSession } from "../lib/api"
import { clearAuthSession } from "../lib/auth"
import { platformModuleGroups } from "../lib/moduleCatalog"

const iconMap = {
  building: Building2,
  check: ClipboardCheck,
  database: Database,
  file: FileText,
  git: GitBranch,
  layers: Layers3,
  plane: Plane,
  phone: Phone,
  rows: Rows3,
  shield: ShieldCheck,
  tags: Tags,
}

async function logout() {
  await apiDeleteSession().catch(() => null)
  clearAuthSession()
  window.location.href = "/login"
}

export default function PlatformLayout({ children, user }) {
  const pathname = typeof window !== "undefined" ? window.location.pathname : "/platform"
  return (
    <div className="min-h-screen bg-slate-100">
      <aside className="border-b border-slate-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-4 px-4 py-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">AeroAssist Global</p>
              <h1 className="text-lg font-semibold text-slate-950">Platform Console</h1>
              <p className="mt-1 text-sm text-slate-600">System owner workspace for SaaS setup, airline intelligence, CMS, portal, offer evidence, and readiness metadata.</p>
            </div>
            <div className="flex items-center gap-3">
              {user ? <p className="text-sm text-slate-500">{user.full_name}</p> : null}
              <button className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100" type="button" onClick={logout}>Logout</button>
            </div>
          </div>
          <nav className="grid gap-3 text-sm lg:grid-cols-2 xl:grid-cols-3" aria-label="Platform Console modules">
            {platformModuleGroups.map((group) => <PlatformModuleGroup group={group} pathname={pathname} key={group.title} />)}
          </nav>
        </div>
      </aside>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  )
}

function PlatformModuleGroup({ group, pathname }) {
  return (
    <section className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-slate-700">{group.title}</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">{group.description}</p>
        </div>
        <span className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-blue-700 ring-1 ring-blue-100">{group.safety}</span>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {group.items.map((item) => <PlatformModuleLink item={item} pathname={pathname} key={`${group.title}-${item.href}-${item.label}`} />)}
      </div>
    </section>
  )
}

function PlatformModuleLink({ item, pathname }) {
  const Icon = iconMap[item.icon] || FileText
  const active = pathname === item.href || (item.href !== "/platform" && pathname.startsWith(`${item.href}/`))
  return (
    <a className={`inline-flex max-w-full items-center gap-2 rounded-md px-2.5 py-2 text-xs font-semibold ${active ? "bg-blue-600 text-white" : "bg-white text-slate-700 hover:bg-slate-100"}`} href={item.href} title={`${item.description} · ${item.badge || "Platform only"}`}>
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{item.label}</span>
      {item.badge ? <span className={`hidden rounded-full px-1.5 py-0.5 text-[10px] sm:inline ${active ? "bg-white/20 text-white" : "bg-slate-100 text-slate-500"}`}>{item.badge}</span> : null}
    </a>
  )
}
