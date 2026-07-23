import SlidersHorizontal from "lucide-react/dist/esm/icons/sliders-horizontal.js"
import X from "lucide-react/dist/esm/icons/x.js"

export default function FilterBar({
  children,
  onClear,
  resultCount,
  title = "Filters",
}) {
  return (
    <section aria-label={title} className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
          <SlidersHorizontal aria-hidden="true" className="h-4 w-4 text-slate-500" />
          {title}
        </h2>
        <div className="flex items-center gap-3">
          {Number.isFinite(resultCount) ? <span aria-live="polite" className="text-xs font-medium text-slate-500">{resultCount} shown</span> : null}
          {onClear ? (
            <button className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-950" onClick={onClear} type="button">
              <X aria-hidden="true" className="h-3.5 w-3.5" />
              Clear filters
            </button>
          ) : null}
        </div>
      </div>
      <div className="grid gap-3">{children}</div>
    </section>
  )
}
