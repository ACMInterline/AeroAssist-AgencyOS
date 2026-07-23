import { SlidersHorizontal } from "lucide-react"

export default function OperationsFilters({ metadata, value, onChange }) {
  if (!metadata) return null
  function update(key, nextValue) {
    onChange({ ...value, [key]: nextValue })
  }
  return (
    <div className="flex flex-wrap items-center gap-2" aria-label="Operations filters">
      <SlidersHorizontal className="h-4 w-4 text-slate-500" aria-hidden="true" />
      <FilterSelect label="Assignment" value={value.assignment} options={metadata.assignment_options} onChange={(next) => update("assignment", next)} />
      <FilterSelect label="Consultant" value={value.assignee_id} options={metadata.assignee_options} onChange={(next) => update("assignee_id", next)} />
      <FilterSelect label="Urgency" value={value.urgency} options={metadata.urgency_options} onChange={(next) => update("urgency", next)} />
      <FilterSelect label="Work type" value={value.work_type} options={metadata.work_type_options} onChange={(next) => update("work_type", next)} />
      <FilterSelect label="Due" value={value.due_period} options={metadata.due_options} onChange={(next) => update("due_period", next)} />
    </div>
  )
}

function FilterSelect({ label, value, options = [], onChange }) {
  return (
    <label className="sr-only">
      {label}
      <select className="not-sr-only rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700" aria-label={label} value={value || options[0]?.value || ""} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}
      </select>
    </label>
  )
}
