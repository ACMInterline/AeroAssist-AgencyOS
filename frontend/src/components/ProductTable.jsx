import { useEffect, useMemo, useState } from "react"
import ArrowUpDown from "lucide-react/dist/esm/icons/arrow-up-down.js"
import ChevronLeft from "lucide-react/dist/esm/icons/chevron-left.js"
import ChevronRight from "lucide-react/dist/esm/icons/chevron-right.js"
import EmptyState from "./EmptyState"

const defaultRowKey = (row) => row.id
const emptyRows = []

export default function ProductTable({
  bulkActions = [],
  caption,
  columns,
  defaultSort,
  emptyBody,
  emptyTitle,
  getRowHref,
  getRowKey = defaultRowKey,
  pageSize = 25,
  rows = emptyRows,
  selectable = false,
}) {
  const [page, setPage] = useState(1)
  const [selectedKeys, setSelectedKeys] = useState([])
  const [sort, setSort] = useState(defaultSort || null)
  const orderedRows = useMemo(() => {
    if (!sort?.key) return rows
    const column = columns.find((item) => item.key === sort.key)
    if (!column?.sortValue) return rows
    const direction = sort.direction === "desc" ? -1 : 1
    return [...rows].sort((left, right) => compare(column.sortValue(left), column.sortValue(right)) * direction)
  }, [columns, rows, sort])
  const totalPages = Math.max(1, Math.ceil(orderedRows.length / pageSize))
  const visibleRows = orderedRows.slice((page - 1) * pageSize, page * pageSize)
  const visibleKeys = visibleRows.map((row) => String(getRowKey(row)))
  const selectedRows = rows.filter((row) => selectedKeys.includes(String(getRowKey(row))))
  const allVisibleSelected = Boolean(visibleKeys.length) && visibleKeys.every((key) => selectedKeys.includes(key))
  const tableLabel = caption || "Records"

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages))
    const available = new Set(rows.map((row) => String(getRowKey(row))))
    setSelectedKeys((current) => {
      const retained = current.filter((key) => available.has(key))
      return retained.length === current.length ? current : retained
    })
  }, [getRowKey, rows, totalPages])

  if (!rows.length) {
    return <EmptyState title={emptyTitle} body={emptyBody} />
  }

  function changeSort(column) {
    if (!column.sortValue) return
    setSort((current) => ({
      key: column.key,
      direction: current?.key === column.key && current.direction === "asc" ? "desc" : "asc",
    }))
    setPage(1)
  }

  function toggleVisible() {
    setSelectedKeys((current) => allVisibleSelected
      ? current.filter((key) => !visibleKeys.includes(key))
      : [...new Set([...current, ...visibleKeys])])
  }

  function toggleRow(row) {
    const key = String(getRowKey(row))
    setSelectedKeys((current) => current.includes(key)
      ? current.filter((item) => item !== key)
      : [...current, key])
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      {selectable && bulkActions.length ? (
        <div className="aa-sticky-actions flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3">
          <p className="text-sm text-slate-600">{selectedRows.length} selected</p>
          <div className="flex flex-wrap gap-2">
            {bulkActions.map((action) => (
              <button
                className={action.tone === "danger" ? "danger-button" : "secondary-button"}
                disabled={!selectedRows.length || action.disabled?.(selectedRows)}
                key={action.label}
                onClick={() => action.onClick(selectedRows)}
                type="button"
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      ) : null}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <caption className="sr-only">{tableLabel}</caption>
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-600">
            <tr>
              {selectable ? (
                <th className="w-12 px-4 py-3" scope="col">
                  <input aria-label="Select visible rows" checked={allVisibleSelected} onChange={toggleVisible} type="checkbox" />
                </th>
              ) : null}
              {columns.map((column) => (
                <th aria-sort={sort?.key === column.key ? (sort.direction === "asc" ? "ascending" : "descending") : undefined} className="px-4 py-3" key={column.key} scope="col">
                  {column.sortValue ? (
                    <button className="inline-flex items-center gap-1 font-semibold uppercase" onClick={() => changeSort(column)} type="button">
                      {column.label}
                      <ArrowUpDown aria-hidden="true" className="h-3.5 w-3.5" />
                    </button>
                  ) : column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {visibleRows.map((row) => {
              const href = getRowHref?.(row)
              const rowKey = String(getRowKey(row))
              return (
                <tr className="hover:bg-slate-50" key={rowKey}>
                  {selectable ? (
                    <td className="w-12 px-4 py-3 align-top">
                      <input aria-label={`Select row ${rowKey}`} checked={selectedKeys.includes(rowKey)} onChange={() => toggleRow(row)} type="checkbox" />
                    </td>
                  ) : null}
                  {columns.map((column, index) => (
                    <td className="max-w-md px-4 py-3 align-top text-slate-700" key={column.key}>
                      {index === 0 && href ? <a className="font-semibold text-blue-700 hover:underline" href={href}>{column.render(row)}</a> : column.render(row)}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {totalPages > 1 ? (
        <nav aria-label={`${tableLabel} pages`} className="flex items-center justify-between gap-3 border-t border-slate-200 px-4 py-3">
          <p className="text-xs text-slate-500">Page {page} of {totalPages} · {rows.length} records</p>
          <div className="flex items-center gap-2">
            <button aria-label="Previous page" className="icon-button" disabled={page === 1} onClick={() => setPage((current) => Math.max(1, current - 1))} type="button">
              <ChevronLeft aria-hidden="true" className="h-4 w-4" />
            </button>
            <button aria-label="Next page" className="icon-button" disabled={page === totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))} type="button">
              <ChevronRight aria-hidden="true" className="h-4 w-4" />
            </button>
          </div>
        </nav>
      ) : null}
    </div>
  )
}

function compare(left, right) {
  const first = left ?? ""
  const second = right ?? ""
  if (typeof first === "number" && typeof second === "number") return first - second
  return String(first).localeCompare(String(second), undefined, { numeric: true, sensitivity: "base" })
}
