import { useEffect, useId, useMemo, useState } from "react"
import { fetchReferenceOptions } from "../../lib/referenceData"

function displayValue(option) {
  if (!option) return ""
  return [option.code, option.label].filter(Boolean).join(" - ")
}

export default function ReferenceAutocomplete({
  domain,
  label,
  value = "",
  selectedCode = "",
  selectedLabel = "",
  onChange,
  required = false,
  disabled = false,
  placeholder = "Search references",
  helpText = "",
  className = "",
}) {
  const generatedId = useId()
  const listId = `${generatedId}-options`
  const historical = useMemo(() => (
    value || selectedCode
      ? {
          id: value,
          value,
          code: selectedCode,
          key: selectedCode,
          label: selectedLabel || selectedCode,
          raw: { is_active: false, historical: true },
        }
      : null
  ), [selectedCode, selectedLabel, value])
  const [query, setQuery] = useState(displayValue(historical))
  const [selectedId, setSelectedId] = useState(value)
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (value !== selectedId) {
      setSelectedId(value)
      setQuery(displayValue(historical))
    }
  }, [historical, selectedId, value])

  useEffect(() => {
    let active = true
    const timeout = setTimeout(() => {
      setLoading(true)
      setError("")
      fetchReferenceOptions(domain, { query, limit: 50 })
        .then((result) => {
          if (active) setOptions(result.items || [])
        })
        .catch((requestError) => {
          if (active) setError(requestError.message)
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, 250)
    return () => {
      active = false
      clearTimeout(timeout)
    }
  }, [domain, query])

  const visibleOptions = useMemo(() => {
    if (!historical || options.some((option) => option.id === historical.id)) return options
    return [historical, ...options]
  }, [historical, options])

  function update(nextQuery) {
    setQuery(nextQuery)
    const exact = visibleOptions.find((option) => {
      const values = [displayValue(option), option.label, option.code, option.key]
      return values.some(
        (candidate) => String(candidate || "").toLowerCase() === nextQuery.toLowerCase(),
      )
    })
    setSelectedId(exact?.id || "")
    onChange(exact || null)
  }

  function validateSelection() {
    if (!query) {
      setError(required ? "Select a canonical reference." : "")
      return
    }
    const selected = visibleOptions.find((option) => option.id === selectedId)
    if (!selected || ![displayValue(selected), selected.label, selected.code, selected.key].some(
      (candidate) => String(candidate || "").toLowerCase() === query.toLowerCase(),
    )) {
      setError("No matching reference found. Select a listed reference.")
      setSelectedId("")
      onChange(null)
    }
  }

  return (
    <label className={`grid gap-1 text-sm font-medium text-slate-700 ${className}`}>
      <span>{label}</span>
      <input
        aria-autocomplete="list"
        aria-controls={listId}
        aria-describedby={`${generatedId}-status`}
        aria-expanded={Boolean(options.length)}
        aria-invalid={Boolean(error)}
        autoComplete="off"
        className="field"
        disabled={disabled}
        list={listId}
        placeholder={placeholder}
        required={required}
        role="combobox"
        value={query}
        onBlur={validateSelection}
        onChange={(event) => update(event.target.value)}
      />
      <datalist id={listId}>
        {visibleOptions.map((option) => (
          <option key={option.id || option.code} value={displayValue(option)}>
            {option.raw?.is_active === false ? "Inactive historical value" : option.label}
          </option>
        ))}
      </datalist>
      <span className={error ? "text-xs text-rose-700" : "text-xs text-slate-500"} id={`${generatedId}-status`}>
        {error || (loading ? "Loading references..." : !visibleOptions.length ? "No matching reference found." : helpText)}
      </span>
    </label>
  )
}
