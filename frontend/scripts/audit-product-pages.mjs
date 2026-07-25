#!/usr/bin/env node

import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import {
  agencyProductNavigation,
  platformProductNavigation,
} from "../src/lib/moduleCatalog.js"

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(scriptDirectory, "../..")
const frontendSource = path.join(root, "frontend/src")
const pagesDirectory = path.join(frontendSource, "pages")
const appPath = path.join(frontendSource, "App.jsx")
const outputPath = path.join(root, "docs/architecture/product-page-inventory.csv")
const appSource = fs.readFileSync(appPath, "utf8")

function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(directory, entry.name)
    return entry.isDirectory() ? walk(fullPath) : [fullPath]
  })
}

function relative(filePath) {
  return path.relative(root, filePath).split(path.sep).join("/")
}

const pageFiles = walk(pagesDirectory)
  .filter((filePath) => filePath.endsWith(".jsx"))
  .sort((left, right) => relative(left).localeCompare(relative(right)))

const importsByFile = new Map()
for (const match of appSource.matchAll(/const\s+(\w+)\s*=\s*lazy\(\(\)\s*=>\s*import\("(\.\/pages\/[^"]+)"\)\)/g)) {
  const importedFile = path.resolve(frontendSource, `${match[2].slice(2)}.jsx`)
  const names = importsByFile.get(importedFile) || []
  names.push(match[1])
  importsByFile.set(importedFile, names)
}

const routesByComponent = new Map()
for (const match of appSource.matchAll(/"(\/[^"]+)"\s*:\s*(\w+)/g)) {
  const routes = routesByComponent.get(match[2]) || []
  routes.push(match[1])
  routesByComponent.set(match[2], routes)
}

function navigationMap(areas) {
  const result = new Map()
  for (const area of areas) {
    for (const item of area.items) {
      result.set(item.href, area.advanced_only ? "advanced" : "primary")
    }
  }
  return result
}

const platformNavigation = navigationMap(platformProductNavigation)
const agencyNavigation = navigationMap(agencyProductNavigation)
const portalPrimaryRoutes = new Set([
  "/portal",
  "/portal/trips",
  "/portal/travel-options",
  "/portal/requests",
  "/portal/documents",
  "/portal/communications",
  "/portal/finance",
  "/portal/profile",
  "/portal/tickets",
  "/portal/assistance",
  "/portal/timeline",
  "/portal/notifications",
])

function routePlacement(audience, routes, routeStatus) {
  if (audience === "platform") {
    if (routes.some((route) => platformNavigation.get(route) === "primary")) return "primary"
    if (routes.some((route) => platformNavigation.get(route) === "advanced")) return "advanced"
  }
  if (audience === "agency") {
    if (routes.some((route) => agencyNavigation.get(route) === "primary")) return "primary"
    if (routes.some((route) => agencyNavigation.get(route) === "advanced")) return "advanced"
  }
  if (audience.includes("portal") && routes.some((route) => portalPrimaryRoutes.has(route))) return "primary"
  if (routeStatus === "orphan") return "orphan"
  return "contextual"
}

function visibleText(source) {
  const textNodes = [...source.matchAll(/>([^<{][^<]*)</g)].map((match) => match[1])
  const productProps = [...source.matchAll(/\b(?:body|description|eyebrow|label|placeholder|title)=["']([^"']+)["']/g)].map((match) => match[1])
  return [...textNodes, ...productProps].join(" ").replace(/\s+/g, " ").trim().toLowerCase()
}

const indicatorPatterns = [
  ["metadata", /\bmetadata\b/],
  ["foundation", /\bfoundation\b/],
  ["diagnostics", /\bdiagnostic(?:s)?\b/],
  ["developer_tooling", /\bdeveloper\b|\bdebug\b/],
  ["catalogue", /\bcatalog(?:ue)?\b/],
  ["engineering", /\bcanonical\b|\bentity id\b|\bstate map\b|\barchitecture\b/],
]

function indicators(source) {
  const text = visibleText(source)
  return indicatorPatterns.filter(([, pattern]) => pattern.test(text)).map(([name]) => name)
}

function surfaceClassification(placement, filePath, sourceIndicators) {
  const name = path.basename(filePath).toLowerCase()
  if (placement === "orphan") return "orphan_or_unused"
  if (placement === "primary") return "task_surface"
  if (name.includes("diagnostic") || sourceIndicators.includes("diagnostics")) return "diagnostics"
  if (name.includes("metadata") || name.includes("foundation") || sourceIndicators.includes("foundation")) return "foundation_or_metadata"
  if (/(catalog|taxonomy|reference|import|parser|blueprint|rulecomposer|governance)/.test(name)) return "catalogue_or_governance"
  if (placement === "advanced") return "specialist_tooling"
  return "contextual_detail"
}

function audienceFor(filePath) {
  const relativePath = relative(filePath)
  if (relativePath.includes("/platform/")) return "platform"
  if (relativePath.includes("/agency/")) return "agency"
  if (relativePath.includes("/portal/")) return "client_or_passenger_portal"
  if (relativePath.includes("/public/")) return "public"
  if (relativePath.includes("/auth/")) return "authentication"
  return "shared"
}

function csvValue(value) {
  const text = String(value ?? "")
  return `"${text.replaceAll('"', '""')}"`
}

const rows = pageFiles.map((filePath) => {
  const source = fs.readFileSync(filePath, "utf8")
  const importedNames = importsByFile.get(filePath) || []
  const symbolMatch = source.match(/export\s+default\s+function\s+(\w+)/)
  const symbols = importedNames.length ? importedNames : [symbolMatch?.[1] || path.basename(filePath, ".jsx")]
  const fallbackRoutes = symbols.includes("HomePage") && appSource.includes("|| HomePage") ? ["/"] : []
  const routes = [...new Set([...symbols.flatMap((symbol) => routesByComponent.get(symbol) || []), ...fallbackRoutes])].sort()
  const dynamic = symbols.some((symbol) => new RegExp(`<${symbol}\\b`).test(appSource))
  const routeStatus = routes.length
    ? (dynamic ? "exact_and_dynamic" : "exact")
    : (dynamic ? "dynamic" : "orphan")
  const audience = audienceFor(filePath)
  const placement = routePlacement(audience, routes, routeStatus)
  const sourceIndicators = indicators(source)
  const routeLabel = routes.length ? routes.join(" | ") : (dynamic ? "dynamic route in frontend/src/App.jsx" : "none found")
  const notes = routes.length > 1
    ? "Compatibility aliases share this page component."
    : placement === "advanced"
      ? "Retained under collapsed Advanced navigation."
      : placement === "orphan"
        ? "No App.jsx route reference found; review before removal."
        : "Canonical or contextual product surface."
  return [
    audience,
    relative(filePath),
    symbols.join(" | "),
    routeLabel,
    routeStatus,
    placement,
    surfaceClassification(placement, filePath, sourceIndicators),
    sourceIndicators.join(" | ") || "none",
    notes,
  ]
})

const header = [
  "audience",
  "source_file",
  "component_symbols",
  "route_paths",
  "route_status",
  "navigation_placement",
  "surface_classification",
  "visible_technical_indicators",
  "notes",
]
const csv = `${[header, ...rows].map((row) => row.map(csvValue).join(",")).join("\n")}\n`

if (process.argv.includes("--check")) {
  if (!fs.existsSync(outputPath) || fs.readFileSync(outputPath, "utf8") !== csv) {
    process.stderr.write("Product page inventory is missing or stale. Run: node frontend/scripts/audit-product-pages.mjs\n")
    process.exit(1)
  }
  process.stdout.write(`Product page inventory is current: ${rows.length} pages.\n`)
} else {
  fs.writeFileSync(outputPath, csv)
  process.stdout.write(`Wrote ${relative(outputPath)} with ${rows.length} pages.\n`)
}
