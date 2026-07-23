import { useId } from "react"

export default function FormSection({ children, description, title }) {
  const titleId = useId()
  return (
    <section aria-labelledby={titleId} className="border-t border-slate-200 pt-5 first:border-t-0 first:pt-0">
      <div className="max-w-3xl">
        <h2 className="text-base font-semibold text-slate-950" id={titleId}>{title}</h2>
        {description ? <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p> : null}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  )
}
