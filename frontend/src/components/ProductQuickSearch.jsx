import { useEffect, useMemo, useRef, useState } from "react"
import Search from "lucide-react/dist/esm/icons/search.js"
import X from "lucide-react/dist/esm/icons/x.js"

export default function ProductQuickSearch({
  areas = [],
  label = "Search pages",
}) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const inputRef = useRef(null)
  const items = useMemo(
    () => areas.flatMap((area) => area.items.map((item) => ({
      ...item,
      area: area.title,
    }))),
    [areas],
  )
  const results = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return items.filter((item) => !item.advanced_only).slice(0, 8)
    return items.filter((item) => [
      item.preferred_label,
      item.preferred_description,
      item.label,
      item.description,
      item.area,
    ].some((value) => String(value || "").toLowerCase().includes(needle))).slice(0, 10)
  }, [items, query])

  useEffect(() => {
    if (!open) return undefined
    inputRef.current?.focus()
    function closeOnEscape(event) {
      if (event.key === "Escape") setOpen(false)
    }
    document.addEventListener("keydown", closeOnEscape)
    return () => document.removeEventListener("keydown", closeOnEscape)
  }, [open])

  return (
    <div className="relative">
      <button
        aria-expanded={open}
        aria-haspopup="dialog"
        className="icon-button"
        onClick={() => setOpen((value) => !value)}
        title={label}
        type="button"
      >
        <Search aria-hidden="true" className="h-4 w-4" />
        <span className="sr-only">{label}</span>
      </button>
      {open ? (
        <div
          aria-label={label}
          className="fixed inset-x-3 top-20 z-50 mx-auto max-w-xl overflow-hidden rounded-lg border border-slate-200 bg-white shadow-2xl sm:absolute sm:inset-auto sm:right-0 sm:top-11 sm:w-[min(92vw,34rem)]"
          role="dialog"
        >
          <div className="flex items-center gap-2 border-b border-slate-200 p-3">
            <Search aria-hidden="true" className="h-4 w-4 shrink-0 text-slate-400" />
            <label className="sr-only" htmlFor="product-page-search">{label}</label>
            <input
              className="min-w-0 flex-1 border-0 bg-transparent px-1 py-2 text-sm outline-none"
              id="product-page-search"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search tasks and pages"
              ref={inputRef}
              value={query}
            />
            <button
              aria-label="Close page search"
              className="icon-button"
              onClick={() => setOpen(false)}
              type="button"
            >
              <X aria-hidden="true" className="h-4 w-4" />
            </button>
          </div>
          <div className="max-h-[min(60vh,28rem)] overflow-y-auto p-2">
            {results.length ? results.map((item) => (
              <a
                className="block rounded-md px-3 py-3 hover:bg-slate-50 focus-visible:bg-slate-50"
                href={item.href}
                key={`${item.area}-${item.href}`}
              >
                <span className="block text-sm font-semibold text-slate-900">{item.preferred_label || item.label}</span>
                <span className="mt-0.5 block text-xs text-slate-500">{item.area} · {item.preferred_description || item.description}</span>
              </a>
            )) : (
              <p className="px-3 py-6 text-center text-sm text-slate-500">No permitted page matches that search.</p>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
