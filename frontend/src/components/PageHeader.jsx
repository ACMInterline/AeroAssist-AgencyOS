export default function PageHeader({
  actions,
  breadcrumbs = [],
  description,
  eyebrow,
  status,
  title,
}) {
  return (
    <header className="border-b border-slate-200 pb-5">
      {breadcrumbs.length ? (
        <nav aria-label="Breadcrumb" className="mb-3">
          <ol className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
            {breadcrumbs.map((item, index) => (
              <li className="flex items-center gap-2" key={`${item.href || item.label}-${index}`}>
                {index ? <span aria-hidden="true" className="text-slate-400">/</span> : null}
                {item.href ? <a className="font-medium text-blue-700 hover:underline" href={item.href}>{item.label}</a> : <span>{item.label}</span>}
              </li>
            ))}
          </ol>
        </nav>
      ) : null}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 max-w-3xl">
          {eyebrow ? <p className="text-sm font-semibold text-blue-700">{eyebrow}</p> : null}
          <div className="mt-1 flex min-w-0 flex-wrap items-center gap-3">
            <h1 className="min-w-0 text-2xl font-semibold text-slate-950">{title}</h1>
            {status}
          </div>
          {description ? <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
    </header>
  )
}
