import { useMemo, useState } from "react"
import Building2 from "lucide-react/dist/esm/icons/building-2.js"
import ClipboardList from "lucide-react/dist/esm/icons/clipboard-list.js"
import Database from "lucide-react/dist/esm/icons/database.js"
import Files from "lucide-react/dist/esm/icons/files.js"
import Globe2 from "lucide-react/dist/esm/icons/globe-2.js"
import Inbox from "lucide-react/dist/esm/icons/inbox.js"
import Menu from "lucide-react/dist/esm/icons/menu.js"
import Palette from "lucide-react/dist/esm/icons/palette.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import Rows3 from "lucide-react/dist/esm/icons/rows-3.js"
import Settings from "lucide-react/dist/esm/icons/settings.js"
import Sparkles from "lucide-react/dist/esm/icons/sparkles.js"
import Tags from "lucide-react/dist/esm/icons/tags.js"
import UserRound from "lucide-react/dist/esm/icons/user-round.js"
import Users from "lucide-react/dist/esm/icons/users.js"
import { apiDeleteSession } from "../lib/api"
import { clearAuthSession } from "../lib/auth"
import { agencyThemeStyle } from "../lib/theme"

const primaryNav = [
  { label: "Dashboard", description: "Workspace home", href: "/agency", icon: Building2 },
  { label: "Requests", description: "Operational work", href: "/agency/requests", icon: ClipboardList },
  { label: "Trips", description: "Dossiers", href: "/agency/trips", icon: Plane },
  { label: "Offers", description: "Compare options", href: "/agency/offers", icon: Sparkles },
  { label: "Booking Workspaces", description: "PNR mirrors", href: "/agency/booking-workspaces", icon: ClipboardList },
  { label: "Booking Imports", description: "GDS drafts", href: "/agency/booking-imports", icon: Files },
  { label: "GDS Parser", description: "Parse review", href: "/agency/gds-parser", icon: Database },
  { label: "Policy Library", description: "Airline rules", href: "/agency/airline-policy-library", icon: Database },
  { label: "Service Taxonomy", description: "Canonical services", href: "/agency/service-taxonomy", icon: Tags },
  { label: "Service Mechanics", description: "SSR/EMD lookup", href: "/agency/service-mechanics", icon: ClipboardList },
  { label: "Ancillary Pricing", description: "Prices and exceptions", href: "/agency/ancillary-pricing", icon: ClipboardList },
  { label: "Policy Comparison", description: "Airline operations", href: "/agency/policy-comparison", icon: Rows3 },
  { label: "Service Advisor", description: "Operational guidance", href: "/agency/airline-service-advisor", icon: ClipboardList },
  { label: "Offer Advisor", description: "Offer policy context", href: "/agency/offer-policy-advisor", icon: Rows3 },
  { label: "Decision Packs", description: "Offer evidence", href: "/agency/offer-decision-packs", icon: Rows3 },
  { label: "Decision Explanations", description: "Timeline audit", href: "/agency/offer-decision-explanations", icon: Rows3 },
  { label: "Decision Exports", description: "Review snapshots", href: "/agency/offer-decision-exports", icon: Files },
  { label: "Export Previews", description: "Render review", href: "/agency/offer-decision-export-previews", icon: Files },
  { label: "Export Releases", description: "Manual readiness", href: "/agency/offer-decision-export-releases", icon: Files },
  { label: "Tickets & EMDs", description: "Mirror records", href: "/agency/tickets-emds", icon: Files },
  { label: "Intakes", description: "Public queue", href: "/agency/request-intakes", icon: Inbox },
  { label: "Clients", description: "Accounts", href: "/agency/clients", icon: Users },
  { label: "Passengers", description: "Travelers", href: "/agency/passengers", icon: UserRound },
  { label: "Documents", description: "Rendered files", href: "/agency/documents", icon: Files },
]

const secondaryNav = [
  { label: "Team", description: "Staff access", href: "/agency", icon: Users, badge: "Dashboard" },
  { label: "Website / CMS", description: "Public content", href: "/agency/website", icon: Globe2 },
  { label: "CMS Media", description: "Website assets", href: "/agency/website/media", icon: Files },
  { label: "Reference Data", description: "Lookups and services", href: "/agency/reference", icon: Database },
  { label: "Form Profiles", description: "Field menus", href: "/agency/settings/forms", icon: ClipboardList },
  { label: "Settings", description: "Brand and theme", href: "/agency/settings", icon: Settings },
]

async function logout() {
  await apiDeleteSession().catch(() => null)
  clearAuthSession()
  window.location.href = "/login"
}

function isActive(item, pathname) {
  if (!item.href) return false
  if (item.href === "/agency") return pathname === "/agency"
  return pathname === item.href || pathname.startsWith(`${item.href}/`)
}

export default function AgencyLayout({ children, user, agency }) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const themeStyle = agencyThemeStyle(agency)
  const brandName = agency?.branding?.brand_name || agency?.name || "AeroAssist"
  const sidebarLogo = agency?.branding?.logo_assets?.sidebar?.url || agency?.branding?.logo_url
  const initials = brandName.slice(0, 2).toUpperCase()
  const pathname = typeof window !== "undefined" ? window.location.pathname : "/agency"
  const pageTitle = useMemo(() => {
    const item = [...primaryNav, ...secondaryNav].find((navItem) => isActive(navItem, pathname))
    return item?.label || "Agency Workspace"
  }, [pathname])

  const sidebar = (
    <aside className={`aa-sidebar flex h-full flex-col border-r ${collapsed ? "w-[92px]" : "w-[286px]"}`} style={{ background: "var(--aa-shell)", borderColor: "var(--aa-border)" }}>
      <div className="flex items-center gap-3 border-b px-4 py-4" style={{ borderColor: "var(--aa-border)" }}>
        {sidebarLogo ? (
          <img className="h-11 w-11 shrink-0 rounded-md border object-contain p-1" src={sidebarLogo} alt={`${brandName} logo`} style={{ borderColor: "var(--aa-border)", background: "var(--aa-muted-bg)" }} />
        ) : (
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md text-sm font-bold" style={{ background: "var(--aa-muted-bg)", color: "var(--aa-primary)" }}>
            {initials}
          </div>
        )}
        {!collapsed ? (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold" style={{ color: "var(--aa-text)" }}>{brandName}</p>
            <p className="truncate text-xs" style={{ color: "var(--aa-muted-text)" }}>AgencyOS Workspace</p>
          </div>
        ) : null}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4">
        <NavSection title="Workspace" items={primaryNav} pathname={pathname} collapsed={collapsed} />
        <NavSection title="Operations" items={secondaryNav} pathname={pathname} collapsed={collapsed} />
      </div>

      <div className="border-t p-3" style={{ borderColor: "var(--aa-border)" }}>
        <button className="hidden w-full items-center justify-center rounded-md border px-3 py-2 text-xs font-semibold text-slate-700 lg:flex" type="button" onClick={() => setCollapsed((value) => !value)}>
          {collapsed ? "Expand" : "Collapse sidebar"}
        </button>
        {!collapsed ? (
          <div className="mt-3 rounded-md border px-3 py-3 text-xs" style={{ borderColor: "var(--aa-border)", background: "var(--aa-muted-bg)", color: "var(--aa-muted-text)" }}>
            <div className="flex items-center gap-2 font-semibold" style={{ color: "var(--aa-text)" }}>
              <Palette className="h-3.5 w-3.5" />
              Theme active
            </div>
            <p className="mt-1">Brand presets control fonts, radius, colors, and surfaces.</p>
          </div>
        ) : null}
      </div>
    </aside>
  )

  return (
    <div className="aa-themed min-h-screen" style={themeStyle}>
      <div className="aa-shell-grid min-h-screen">
        <div className="hidden lg:block">{sidebar}</div>
        {drawerOpen ? (
          <div className="fixed inset-0 z-40 lg:hidden">
            <button className="absolute inset-0 bg-slate-950/45" type="button" aria-label="Close navigation" onClick={() => setDrawerOpen(false)} />
            <div className="relative h-full w-[min(86vw,320px)] shadow-2xl">{sidebar}</div>
          </div>
        ) : null}

        <div className="min-w-0">
          <header className="aa-topbar sticky top-0 z-30 border-b backdrop-blur" style={{ background: "color-mix(in srgb, var(--aa-bg), transparent 8%)", borderColor: "var(--aa-border)" }}>
            <div className="flex min-h-16 items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
              <div className="flex min-w-0 items-center gap-3">
                <button className="rounded-md border p-2 lg:hidden" type="button" aria-label="Open navigation" onClick={() => setDrawerOpen(true)}>
                  <Menu className="h-5 w-5" />
                </button>
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--aa-primary)" }}>Agency Workspace</p>
                  <h1 className="truncate text-lg font-semibold sm:text-xl" style={{ color: "var(--aa-text)" }}>{pageTitle}</h1>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="hidden rounded-full px-3 py-1 text-xs font-semibold sm:inline-flex" style={{ background: "var(--aa-muted-bg)", color: "var(--aa-primary)" }}>Manual operations</span>
                <a className="aa-primary-action inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold" href="/agency/requests/new">
                  <Plus className="h-4 w-4" />
                  <span className="hidden sm:inline">Create request</span>
                  <span className="sm:hidden">Create</span>
                </a>
                <div className="hidden min-w-0 text-right md:block">
                  <p className="truncate text-sm font-medium" style={{ color: "var(--aa-text)" }}>{user?.full_name || "Staff user"}</p>
                  <p className="truncate text-xs" style={{ color: "var(--aa-muted-text)" }}>{user?.email || "Signed in"}</p>
                </div>
                <button className="rounded-md border px-3 py-2 text-sm font-semibold" type="button" onClick={logout}>Logout</button>
              </div>
            </div>
          </header>
          <main className="aa-main-frame px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-[1440px]">{children}</div>
          </main>
        </div>
      </div>
    </div>
  )
}

function NavSection({ title, items, pathname, collapsed }) {
  return (
    <div className="mb-6">
      {!collapsed ? <p className="mb-2 px-3 text-[11px] font-bold uppercase tracking-[0.18em]" style={{ color: "var(--aa-muted-text)" }}>{title}</p> : null}
      <nav className="grid gap-1" aria-label={title}>
        {items.map((item) => <NavItem item={item} pathname={pathname} collapsed={collapsed} key={item.label} />)}
      </nav>
    </div>
  )
}

function NavItem({ item, pathname, collapsed }) {
  const Icon = item.icon
  const active = isActive(item, pathname)
  const content = (
    <>
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed ? (
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold">{item.label}</span>
          <span className="block truncate text-[11px] opacity-75">{item.description}</span>
        </span>
      ) : null}
      {!collapsed && item.badge ? <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: "var(--aa-muted-bg)" }}>{item.badge}</span> : null}
      {!collapsed && item.disabled ? <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: "var(--aa-muted-bg)" }}>Soon</span> : null}
    </>
  )

  if (item.disabled) {
    return (
      <button className="aa-nav-item cursor-not-allowed opacity-60" type="button" disabled title={`${item.label} coming soon`}>
        {content}
      </button>
    )
  }

  return (
    <a className={`aa-nav-item ${active ? "aa-nav-active" : ""}`} href={item.href} aria-current={active ? "page" : undefined} title={collapsed ? item.label : undefined}>
      {content}
    </a>
  )
}
