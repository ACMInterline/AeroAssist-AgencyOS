import { useId } from "react"

export default function SectionHeader({ action, description, title }) {
  const titleId = useId()
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 className="text-lg font-semibold text-slate-950" id={titleId}>{title}</h2>
        {description ? <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}
