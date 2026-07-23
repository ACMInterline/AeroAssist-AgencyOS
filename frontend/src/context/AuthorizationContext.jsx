import { createContext, useContext, useEffect, useMemo, useState } from "react"
import { apiGet } from "../lib/api"

const AuthorizationContext = createContext(null)
const SELECTED_AGENCY_KEY = "aeroassist.selectedAgencyId"
const UNLINKED_PORTAL_MESSAGE = "Your portal account is not linked to a profile yet."

function isPublicPath(pathname) {
  return pathname === "/" ||
    pathname === "/login" ||
    pathname === "/invite/accept" ||
    pathname.startsWith("/site/")
}

function selectedMembership(auth) {
  const memberships = auth?.authorization?.agency_memberships || []
  const requested = new URLSearchParams(window.location.search).get("agency_id") ||
    window.localStorage.getItem(SELECTED_AGENCY_KEY)
  return memberships.find((item) => item.membership?.agency_id === requested) || memberships[0] || null
}

export function AuthorizationProvider({ children }) {
  const pathname = window.location.pathname
  const publicPath = isPublicPath(pathname)
  const [state, setState] = useState({
    auth: null,
    error: null,
    loading: !publicPath,
  })

  const load = async () => {
    if (publicPath) return
    setState((current) => ({ ...current, loading: true, error: null }))
    try {
      const auth = await apiGet("/api/auth/me")
      setState({ auth, error: null, loading: false })
    } catch (error) {
      setState({ auth: null, error, loading: false })
    }
  }

  useEffect(() => {
    load()
  }, [pathname])

  const value = useMemo(() => {
    const agencyAccess = selectedMembership(state.auth)
    const scopedPermissions = pathname.startsWith("/platform")
      ? state.auth?.authorization?.platform?.permissions || []
      : pathname.startsWith("/agency")
        ? agencyAccess?.permissions || []
        : pathname.startsWith("/portal")
          ? state.auth?.authorization?.portal?.permissions || []
          : []
    return {
      ...state,
      publicPath,
      identity: state.auth?.identity || null,
      identityType: state.auth?.authorization?.identity_type || null,
      platformAccess: state.auth?.authorization?.platform || null,
      agencyAccess,
      portalAccess: state.auth?.authorization?.portal || null,
      user: state.auth?.user || null,
      hasPermission(permission) {
        return new Set(scopedPermissions).has(permission)
      },
      refresh: load,
    }
  }, [state, publicPath, pathname])

  return <AuthorizationContext.Provider value={value}>{children}</AuthorizationContext.Provider>
}

export function useAuthorization() {
  const context = useContext(AuthorizationContext)
  if (!context) throw new Error("useAuthorization must be used within AuthorizationProvider")
  return context
}

export function AuthorizationBoundary({ children }) {
  const auth = useAuthorization()
  const pathname = window.location.pathname
  if (auth.publicPath) return children
  if (auth.loading) {
    return <AuthorizationState title="Checking access" message="Loading your current access context." />
  }
  if (auth.error) {
    const unauthorized = auth.error.status === 401
    return (
      <AuthorizationState
        title={unauthorized ? "Sign in required" : "Access check failed"}
        message={unauthorized ? "Your session is missing or no longer valid." : auth.error.message}
        action={unauthorized ? { href: "/login", label: "Sign in" } : null}
      />
    )
  }
  if (pathname.startsWith("/platform") && !auth.platformAccess) {
    return <AuthorizationState title="Platform access denied" message="Your identity has no Platform permissions." />
  }
  if (pathname.startsWith("/agency") && !auth.agencyAccess?.membership) {
    return <AuthorizationState title="Agency access denied" message="An active Agency membership is required." />
  }
  if (pathname.startsWith("/portal")) {
    if (!["client_portal", "passenger_portal"].includes(auth.identityType)) {
      return <AuthorizationState title="Portal access denied" message="A Portal identity is required." />
    }
    if (!auth.portalAccess?.linked) {
      return <AuthorizationState title="Profile link required" message={UNLINKED_PORTAL_MESSAGE} />
    }
    if (auth.portalAccess.subject_type === "passenger" && !passengerPortalPathAllowed(pathname)) {
      return <AuthorizationState title="Passenger Portal access denied" message="This page is outside your linked Passenger scope." />
    }
  }
  return children
}

function passengerPortalPathAllowed(pathname) {
  return pathname === "/portal" ||
    pathname === "/portal/profile" ||
    pathname === "/portal/passengers" ||
    /^\/portal\/passengers\/[^/]+$/.test(pathname)
}

function AuthorizationState({ title, message, action }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <section className="w-full max-w-lg rounded-md border border-slate-200 bg-white p-6 shadow-sm" role="alert">
        <p className="text-xs font-semibold uppercase text-blue-700">AeroAssist access</p>
        <h1 className="mt-2 text-xl font-semibold text-slate-950">{title}</h1>
        <p className="mt-2 text-sm text-slate-600">{message}</p>
        {action ? <a className="mt-5 inline-flex rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white" href={action.href}>{action.label}</a> : null}
      </section>
    </main>
  )
}
