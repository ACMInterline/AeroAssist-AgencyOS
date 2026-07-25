# Frontend Performance Report

**Status:** initial eager JavaScript reduction target met.

## Measurements

Production builds were measured from generated files, with gzip calculated
from file contents. The baseline was captured before the route-registry split;
the after measurement uses Vite 7.3.6 after dependency remediation.

| Measure | Before | After | Change |
|---|---:|---:|---:|
| Initial `index` JavaScript | 224,240 B | 155,379 B | -30.7% |
| Initial `index` gzip | 65,883 B | 50,919 B | -22.7% |
| Total lazy JavaScript | 3,498,807 B | 3,382,018 B | -3.3% |
| Total JavaScript gzip | 1,052,680 B | 1,018,069 B | -3.3% |
| JavaScript files | 391 | 392 | route granularity retained |

The raw initial shell exceeds the required 30% improvement. Total code remains
broad because AeroAssist retains 311 governed product pages; those pages are no
longer eagerly evaluated.

## Chunk Map

| Group | After raw | After gzip | Routes |
|---|---:|---:|---|
| React/application shell (`index`) | 155,379 B | 50,919 B | all |
| Route resolver | 75,227 B | 14,989 B | all route lookup |
| Module catalogue | 63,602 B | 12,793 B | authenticated navigation |
| Agency layout | 13,810 B | about 4,790 B | `/agency/*` |
| Platform layout | 6,340 B | about 2,330 B | `/platform/*` |
| Portal layout | 4,530 B | about 1,970 B | `/portal/*` |
| Largest page: Request creation | 67,217 B | 16,262 B | `/agency/requests/new` |
| Reference console | 65,053 B | 13,441 B | Platform reference routes |

No generated chunk exceeds 500 kB.

## Implementation

- `App.jsx` loads only authorization, loading, and application error handling,
  then dynamically imports `RoutedApplication`.
- `RoutedApplication` dynamically imports every page module.
- Specialist Platform, Agency, and Portal pages remain independently lazy.
- Deep links and manual route precedence remain unchanged.
- Playwright exercises deep links across all four authorization surfaces.

## Duplicate Dependency Review

**Evidence:** the Vite manifest/build output contains one React application
runtime and shared layout/catalogue chunks. Lucide icons remain tree-shaken
per icon. No second router framework or production dependency was added.

## Remaining Work

- The 75 kB route resolver and 64 kB catalogue reflect the breadth of the
  retained product surface. Further reduction requires a reviewed route
  registry decomposition, not threshold inflation.
- No production Real User Monitoring, network-throttled mobile profile, or
  long-session memory measurement was performed.
