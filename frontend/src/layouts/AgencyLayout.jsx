import { useEffect, useMemo, useState } from "react"
import Building2 from "lucide-react/dist/esm/icons/building-2.js"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import ChevronDown from "lucide-react/dist/esm/icons/chevron-down.js"
import ClipboardList from "lucide-react/dist/esm/icons/clipboard-list.js"
import Database from "lucide-react/dist/esm/icons/database.js"
import Files from "lucide-react/dist/esm/icons/files.js"
import Globe2 from "lucide-react/dist/esm/icons/globe-2.js"
import Inbox from "lucide-react/dist/esm/icons/inbox.js"
import Layers3 from "lucide-react/dist/esm/icons/layers-3.js"
import Menu from "lucide-react/dist/esm/icons/menu.js"
import Palette from "lucide-react/dist/esm/icons/palette.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import Phone from "lucide-react/dist/esm/icons/phone.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import Rows3 from "lucide-react/dist/esm/icons/rows-3.js"
import Settings from "lucide-react/dist/esm/icons/settings.js"
import Sparkles from "lucide-react/dist/esm/icons/sparkles.js"
import Tags from "lucide-react/dist/esm/icons/tags.js"
import UserRound from "lucide-react/dist/esm/icons/user-round.js"
import Users from "lucide-react/dist/esm/icons/users.js"
import { apiDeleteSession, apiGet } from "../lib/api"
import { clearAuthSession } from "../lib/auth"
import {
  agencyModuleGroups,
  agencyProductNavigation,
  entitlementLabel,
  entitlementTone,
  entitlementVisibilityForItem,
  flattenModuleGroups,
  productNavigationForRole,
} from "../lib/moduleCatalog"
import { agencyThemeStyle } from "../lib/theme"

const iconMap = {
  building: Building2,
  check: CheckCircle2,
  clipboard: ClipboardList,
  database: Database,
  files: Files,
  globe: Globe2,
  inbox: Inbox,
  layers: Layers3,
  plane: Plane,
  phone: Phone,
  plus: Plus,
  rows: Rows3,
  settings: Settings,
  sparkles: Sparkles,
  tags: Tags,
  user: UserRound,
  users: Users,
}

const allAgencyModules = flattenModuleGroups(agencyModuleGroups)
const allAgencyProductItems = agencyProductNavigation.flatMap((area) => area.items)

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
  const [entitlementVisibility, setEntitlementVisibility] = useState({})
  const themeStyle = agencyThemeStyle(agency)
  const brandName = agency?.branding?.brand_name || agency?.name || "AeroAssist"
  const sidebarLogo = agency?.branding?.logo_assets?.sidebar?.url || agency?.branding?.logo_url
  const initials = brandName.slice(0, 2).toUpperCase()
  const pathname = typeof window !== "undefined" ? window.location.pathname : "/agency"
  const navigationRole = agencyNavigationRole(user, agency)
  const navigation = useMemo(
    () => productNavigationForRole(agencyProductNavigation, navigationRole),
    [navigationRole],
  )
  const pageTitle = useMemo(() => {
    const productItem = allAgencyProductItems.find((navItem) => isActive(navItem, pathname))
    if (productItem) return productItem.preferred_label
    return allAgencyModules.find((navItem) => isActive(navItem, pathname))?.label || "Agency Workspace"
  }, [pathname])

  useEffect(() => {
    if (!agency?.id) {
      setEntitlementVisibility({})
      return
    }
    let active = true
    apiGet(`/api/agencies/${agency.id}/saas-subscriptions/module-visibility`)
      .then((result) => {
        if (!active) return
        setEntitlementVisibility(result.visibility_by_key || {})
      })
      .catch(() => {
        if (!active) return
        setEntitlementVisibility({})
      })
    return () => {
      active = false
    }
  }, [agency?.id])

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
            <p className="truncate text-xs" style={{ color: "var(--aa-muted-text)" }}>Agency Workspace</p>
          </div>
        ) : null}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4">
        {collapsed ? (
          <nav className="grid gap-2" aria-label="Agency workflow areas">
            {navigation.filter((area) => !area.advanced_only).map((area) => (
              <NavItem item={area.items[0]} pathname={pathname} collapsed entitlementVisibility={entitlementVisibility} icon={area.icon} title={area.title} key={area.title} />
            ))}
          </nav>
        ) : navigation.map((area) => (
          <NavSection group={area} pathname={pathname} collapsed={false} entitlementVisibility={entitlementVisibility} key={area.title} />
        ))}
      </div>

      <div className="border-t p-3" style={{ borderColor: "var(--aa-border)" }}>
        <button className="hidden w-full items-center justify-center rounded-md border px-3 py-2 text-xs font-semibold text-slate-700 lg:flex" type="button" onClick={() => setCollapsed((value) => !value)}>
          {collapsed ? "Expand" : "Collapse sidebar"}
        </button>
        {!collapsed ? (
          <div className="mt-3 rounded-md border px-3 py-3 text-xs" style={{ borderColor: "var(--aa-border)", background: "var(--aa-muted-bg)", color: "var(--aa-muted-text)" }}>
            <div className="flex items-center gap-2 font-semibold" style={{ color: "var(--aa-text)" }}>
              <Palette className="h-3.5 w-3.5" />
              Agency appearance
            </div>
            <p className="mt-1">Branding and workspace preferences are managed in Settings.</p>
          </div>
        ) : null}
        {!collapsed ? (
          <p className="mt-3 rounded-md border px-3 py-2 text-[11px] leading-4" style={{ borderColor: "var(--aa-border)", background: "var(--aa-muted-bg)", color: "var(--aa-muted-text)" }}>
            Workspace access reflects your agency’s assigned plan.
          </p>
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
                <button className="rounded-md border p-2 lg:hidden" type="button" aria-label="Open navigation" onClick={() => { setCollapsed(false); setDrawerOpen(true) }}>
                  <Menu className="h-5 w-5" />
                </button>
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--aa-primary)" }}>Agency Workspace</p>
                  <h1 className="truncate text-lg font-semibold sm:text-xl" style={{ color: "var(--aa-text)" }}>{pageTitle}</h1>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="hidden rounded-full px-3 py-1 text-xs font-semibold sm:inline-flex" style={{ background: "var(--aa-muted-bg)", color: "var(--aa-primary)" }}>Agency operations</span>
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
          <main className="aa-main-frame px-4 py-6 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  )
}

function NavSection({ group, pathname, collapsed, entitlementVisibility }) {
  const navigationItems = group.items.filter((item) => item.navigation_visibility !== "contextual")
  const Icon = iconMap[group.icon] || Files
  if (group.advanced_only) {
    return (
      <details className="aa-advanced-navigation mt-5 border-t pt-4" style={{ borderColor: "var(--aa-border)" }}>
        <summary className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold" style={{ color: "var(--aa-muted-text)" }}>
          <Icon className="h-4 w-4" />
          <span className="flex-1">Advanced</span>
          <ChevronDown className="h-4 w-4" />
        </summary>
        <p className="px-3 pb-2 pt-1 text-[11px] leading-4" style={{ color: "var(--aa-muted-text)" }}>{group.description}</p>
        <nav className="grid gap-1" aria-label="Advanced agency modules">
          {navigationItems.map((item) => <NavItem item={item} pathname={pathname} collapsed={false} entitlementVisibility={entitlementVisibility} key={`${group.title}-${item.href}-${item.label}`} />)}
        </nav>
      </details>
    )
  }
  return (
    <div className="mb-5">
      {!collapsed ? (
        <div className="mb-2 px-3">
          <p className="flex items-center gap-2 text-[11px] font-bold uppercase" style={{ color: "var(--aa-muted-text)" }}><Icon className="h-3.5 w-3.5" />{group.title}</p>
        </div>
      ) : null}
      <nav className="grid gap-1" aria-label={group.title}>
        {navigationItems.map((item) => <NavItem item={item} pathname={pathname} collapsed={collapsed} entitlementVisibility={entitlementVisibility} key={`${group.title}-${item.href}-${item.label}`} />)}
      </nav>
    </div>
  )
}

function NavItem({ item, pathname, collapsed, entitlementVisibility, icon, title }) {
  const Icon = iconMap[icon || item.icon] || Files
  const active = isActive(item, pathname)
  const visibility = entitlementVisibilityForItem(item, entitlementVisibility)
  const content = (
    <>
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed ? (
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold">{item.preferred_label || item.label}</span>
          <span className="block text-[11px] leading-4 opacity-75">{item.preferred_description || item.description}</span>
        </span>
      ) : null}
      {!collapsed ? (
        <span className="flex shrink-0 flex-col items-end gap-1">
          {item.badge ? <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: "var(--aa-muted-bg)" }}>{item.badge}</span> : null}
          {visibility ? <EntitlementBadge status={visibility.status} title={visibility.reason} /> : null}
          {item.disabled ? <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: "var(--aa-muted-bg)" }}>Soon</span> : null}
        </span>
      ) : null}
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
    <a className={`aa-nav-item ${active ? "aa-nav-active" : ""}`} href={item.href} aria-current={active ? "page" : undefined} title={collapsed ? title || item.preferred_label || item.label : undefined}>
      {content}
    </a>
  )
}

function agencyNavigationRole(user, agency) {
  const membershipRole = agency?.current_membership?.agency_role
  if (membershipRole) return membershipRole
  if (["platform_owner", "platform_admin"].includes(user?.global_role)) return "agency_owner"
  if (user?.global_role === "platform_support") return "agency_readonly"
  return null
}

function EntitlementBadge({ status, title }) {
  return (
    <span className={`max-w-[104px] truncate rounded-full px-2 py-0.5 text-[9px] font-semibold ring-1 ${entitlementTone(status)}`} title={title || entitlementLabel(status)}>
      {entitlementLabel(status)}
    </span>
  )
}
