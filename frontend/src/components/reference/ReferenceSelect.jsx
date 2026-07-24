import { useEffect, useId, useMemo, useState } from "react"
import { fetchReferenceOptions } from "../../lib/referenceData"

function optionValue(option, valueMode) {
  return String(valueMode === "code" ? option?.code || option?.key || "" : option?.id || "")
}

function historicalOption({ value, selectedCode, selectedLabel, valueMode }) {
  if (!value && !selectedCode) return null
  const code = selectedCode || (valueMode === "code" ? value : "")
  const historicalId = value || (code ? `legacy:${code}` : "")
  return {
    id: valueMode === "id" ? historicalId : "",
    value: valueMode === "id" ? historicalId : "",
    code,
    key: code,
    label: selectedLabel || code || "Inactive reference",
    raw: { is_active: false, historical: true },
  }
}

export default function ReferenceSelect({
  domain,
  label,
  value = "",
  selectedCode = "",
  selectedLabel = "",
  onChange,
  required = false,
  disabled = false,
  valueMode = "id",
  placeholder = "Select a reference",
  helpText = "",
  className = "",
}) {
  const generatedId = useId()
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let active = true
    setLoading(true)
    setError("")
    fetchReferenceOptions(domain, { limit: 200 })
      .then((result) => {
        if (active) setOptions(result.items || [])
      })
      .catch((requestError) => {
        if (active) setError(requestError.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [domain])

  const visibleOptions = useMemo(() => {
    const current = historicalOption({ value, selectedCode, selectedLabel, valueMode })
    if (!current || options.some((option) => optionValue(option, valueMode) === String(value))) {
      return options
    }
    return [current, ...options]
  }, [options, selectedCode, selectedLabel, value, valueMode])
  const activeCodeMatch = options.find(
    (option) => String(option.code || option.key || "").toLowerCase() === String(selectedCode || "").toLowerCase(),
  )
  const controlValue = String(
    value
      || (valueMode === "code" ? selectedCode : activeCodeMatch?.id || (selectedCode ? `legacy:${selectedCode}` : "")),
  )

  useEffect(() => {
    if (!value && selectedCode && activeCodeMatch) onChange(activeCodeMatch)
  }, [activeCodeMatch, onChange, selectedCode, value])

  function select(event) {
    const nextValue = event.target.value
    const option = visibleOptions.find((item) => optionValue(item, valueMode) === nextValue)
    onChange(option || null)
  }

  return (
    <label className={`grid gap-1 text-sm font-medium text-slate-700 ${className}`}>
      <span>{label}</span>
      <select
        aria-describedby={`${generatedId}-status`}
        className="field"
        disabled={disabled || loading}
        id={generatedId}
        required={required}
        value={controlValue}
        onChange={select}
      >
        <option value="">{loading ? "Loading references..." : placeholder}</option>
        {visibleOptions.map((option) => {
          const optionKey = optionValue(option, valueMode)
          const inactive = option.raw?.is_active === false
          return (
            <option key={`${option.id || option.code}-${optionKey}`} value={optionKey}>
              {[option.code, option.label].filter(Boolean).join(" - ")}
              {inactive ? " (inactive historical value)" : ""}
            </option>
          )
        })}
      </select>
      <span className={error ? "text-xs text-rose-700" : "text-xs text-slate-500"} id={`${generatedId}-status`}>
        {error || (!loading && !visibleOptions.length ? "No matching reference found." : helpText)}
      </span>
    </label>
  )
}
