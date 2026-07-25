import ArrowLeft from "lucide-react/dist/esm/icons/arrow-left.js"
import SearchX from "lucide-react/dist/esm/icons/search-x.js"

function destination(pathname) {
  if (pathname.startsWith("/platform")) return ["/platform", "Platform overview"]
  if (pathname.startsWith("/agency")) return ["/agency", "Operations Command Centre"]
  if (pathname.startsWith("/portal")) return ["/portal", "Portal dashboard"]
  return ["/", "AeroAssist home"]
}

export default function NotFoundPage() {
  const [href, label] = destination(window.location.pathname)
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4" id="main-content">
      <section className="w-full max-w-lg rounded-md border border-slate-200 bg-white p-6 text-center shadow-sm">
        <SearchX aria-hidden="true" className="mx-auto h-9 w-9 text-slate-400" />
        <p className="mt-4 text-sm font-semibold text-blue-700">AeroAssist navigation</p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-950">Page not found</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          This address does not match an AeroAssist page. Check the address or return to a known workspace. No records were changed.
        </p>
        <a className="primary-button mt-6" href={href}>
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          {label}
        </a>
      </section>
    </main>
  )
}
