import { useMemo, useState } from "react"
import Building2 from "lucide-react/dist/esm/icons/building-2.js"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import ChevronDown from "lucide-react/dist/esm/icons/chevron-down.js"
import Database from "lucide-react/dist/esm/icons/database.js"
import FileText from "lucide-react/dist/esm/icons/file-text.js"
import Layers3 from "lucide-react/dist/esm/icons/layers-3.js"
import Menu from "lucide-react/dist/esm/icons/menu.js"
import PanelLeftClose from "lucide-react/dist/esm/icons/panel-left-close.js"
import PanelLeftOpen from "lucide-react/dist/esm/icons/panel-left-open.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import Tags from "lucide-react/dist/esm/icons/tags.js"
import { apiDeleteSession } from "../lib/api"
import { clearAuthSession } from "../lib/auth"
import {
  flattenModuleGroups,
  platformModuleGroups,
  platformProductNavigation,
  productNavigationForRole,
} from "../lib/moduleCatalog"

const iconMap = {
  building: Building2,
  check: CheckCircle2,
  database: Database,
  file: FileText,
  layers: Layers3,
  plane: Plane,
  shield: ShieldCheck,
  tags: Tags,
}

const allPlatformModules = flattenModuleGroups(platformModuleGroups)
const allProductItems = platformProductNavigation.flatMap((area) => area.items)

async function logout() {
  await apiDeleteSession().catch(() => null)
  clearAuthSession()
  window.location.href = "/login"
}

function isActive(item, pathname) {
  if (!item.href) return false
  if (item.href === "/platform") return pathname === "/platform"
  return pathname === item.href || pathname.startsWith(`${item.href}/`)
}

export default function PlatformLayout({ children, user }) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const pathname = typeof window !== "undefined" ? window.location.pathname : "/platform"
  const navigation = useMemo(
    () => productNavigationForRole(platformProductNavigation, user?.global_role),
    [user?.global_role],
  )
  const pageTitle = useMemo(() => {
    const productItem = allProductItems.find((item) => isActive(item, pathname))
    if (productItem) return productItem.preferred_label
    return allPlatformModules.find((item) => isActive(item, pathname))?.label || "Platform Console"
  }, [pathname])

  const sidebar = (
    <PlatformSidebar
      collapsed={collapsed}
      navigation={navigation}
      pathname={pathname}
      onCollapse={() => setCollapsed((value) => !value)}
    />
  )

  return (
    <div
      className="aa-themed min-h-screen bg-slate-100"
      style={{
        "--aa-bg": "#f8fafc",
        "--aa-surface": "#ffffff",
        "--aa-shell": "#ffffff",
        "--aa-border": "#dbe3ef",
        "--aa-muted-bg": "#f1f5f9",
        "--aa-muted-text": "#475569",
        "--aa-primary": "#1d4ed8",
        "--aa-primary-contrast": "#ffffff",
        "--aa-text": "#0f172a",
        "--aa-radius": "6px",
      }}
    >
      <div className="aa-shell-grid min-h-screen">
        <div className="hidden lg:block">{sidebar}</div>
        {drawerOpen ? (
          <div className="fixed inset-0 z-40 lg:hidden">
            <button className="absolute inset-0 bg-slate-950/45" type="button" aria-label="Close navigation" onClick={() => setDrawerOpen(false)} />
            <div className="relative h-full w-[min(88vw,320px)] shadow-2xl">{sidebar}</div>
          </div>
        ) : null}

        <div className="min-w-0">
          <header className="aa-topbar sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
            <div className="flex min-h-16 items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
              <div className="flex min-w-0 items-center gap-3">
                <button
                  className="icon-button lg:hidden"
                  type="button"
                  aria-label="Open navigation"
                  onClick={() => {
                    setCollapsed(false)
                    setDrawerOpen(true)
                  }}
                >
                  <Menu className="h-5 w-5" />
                </button>
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase text-blue-700">Platform Console</p>
                  <h1 className="truncate text-lg font-semibold text-slate-950 sm:text-xl">{pageTitle}</h1>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="hidden min-w-0 text-right md:block">
                  <p className="truncate text-sm font-medium text-slate-900">{user?.full_name || "Platform user"}</p>
                  <p className="truncate text-xs text-slate-500">{formatRole(user?.global_role)}</p>
                </div>
                <button className="secondary-button" type="button" onClick={logout}>Logout</button>
              </div>
            </div>
          </header>
          <main className="aa-main-frame px-4 py-6 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  )
}

function PlatformSidebar({ collapsed, navigation, onCollapse, pathname }) {
  return (
    <aside className={`aa-sidebar flex h-screen flex-col border-r border-slate-200 bg-white ${collapsed ? "w-[84px]" : "w-[288px]"}`}>
      <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-blue-700 text-sm font-bold text-white">AA</div>
        {!collapsed ? <div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-950">AeroAssist</p><p className="truncate text-xs text-slate-500">Platform Console</p></div> : null}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4">
        {collapsed ? (
          <nav className="grid gap-2" aria-label="Platform areas">
            {navigation.filter((area) => !area.advanced_only).map((area) => (
              <PlatformNavItem collapsed item={area.items[0]} pathname={pathname} icon={area.icon} key={area.title} title={area.title} />
            ))}
          </nav>
        ) : navigation.map((area) => (
          <PlatformArea area={area} pathname={pathname} key={area.title} />
        ))}
      </div>

      <div className="border-t border-slate-200 p-3">
        <button className="icon-button ml-auto hidden lg:inline-flex" type="button" onClick={onCollapse} title={collapsed ? "Expand navigation" : "Collapse navigation"} aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}>
          {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  )
}

function PlatformArea({ area, pathname }) {
  const Icon = iconMap[area.icon] || FileText
  if (area.advanced_only) {
    return (
      <details className="aa-advanced-navigation mt-5 border-t border-slate-200 pt-4">
        <summary className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100">
          <Icon className="h-4 w-4" />
          <span className="flex-1">{area.title}</span>
          <ChevronDown className="h-4 w-4" />
        </summary>
        <p className="px-3 pb-2 pt-1 text-xs leading-5 text-slate-500">{area.description}</p>
        <nav className="grid gap-1" aria-label={`${area.title} modules`}>
          {area.items.map((item) => <PlatformNavItem item={item} pathname={pathname} key={item.href} />)}
        </nav>
      </details>
    )
  }
  return (
    <section className="mb-5">
      <div className="mb-1 flex items-center gap-2 px-3 text-[11px] font-bold uppercase text-slate-500">
        <Icon className="h-3.5 w-3.5" />
        <span>{area.title}</span>
      </div>
      <nav className="grid gap-1" aria-label={area.title}>
        {area.items.map((item) => <PlatformNavItem item={item} pathname={pathname} key={item.href} />)}
      </nav>
    </section>
  )
}

function PlatformNavItem({ collapsed = false, icon, item, pathname, title }) {
  const Icon = iconMap[icon || item.icon] || FileText
  const active = isActive(item, pathname)
  return (
    <a
      className={`aa-nav-item ${active ? "aa-nav-active" : ""}`}
      href={item.href}
      aria-current={active ? "page" : undefined}
      title={collapsed ? title || item.preferred_label : item.preferred_description}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed ? <span className="min-w-0 text-sm font-semibold">{item.preferred_label}</span> : null}
    </a>
  )
}

function formatRole(value) {
  return String(value || "Signed in").replaceAll("_", " ")
}
