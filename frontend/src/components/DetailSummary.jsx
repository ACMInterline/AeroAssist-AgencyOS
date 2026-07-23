export default function DetailSummary({ columns = 3, items, title }) {
  const gridColumns = {
    2: "lg:grid-cols-2",
    3: "lg:grid-cols-3",
    4: "lg:grid-cols-4",
  }[columns] || "lg:grid-cols-3"
  return (
    <section aria-label={title} className="border-y border-slate-200 py-4">
      {title ? <h2 className="text-sm font-semibold text-slate-950">{title}</h2> : null}
      <dl className={`mt-3 grid gap-x-6 gap-y-4 sm:grid-cols-2 ${gridColumns}`}>
        {items.map((item) => (
          <div className="min-w-0" key={item.label}>
            <dt className="text-xs font-semibold text-slate-500">{item.label}</dt>
            <dd className="mt-1 break-words text-sm font-medium text-slate-900">{item.value ?? "Not set"}</dd>
            {item.help ? <dd className="mt-1 text-xs leading-5 text-slate-500">{item.help}</dd> : null}
          </div>
        ))}
      </dl>
    </section>
  )
}
