import { lazy, Suspense } from "react"
import ApplicationErrorBoundary from "./components/ApplicationErrorBoundary"
import LoadingState from "./components/LoadingState"
import { AuthorizationBoundary, AuthorizationProvider } from "./context/AuthorizationContext"

const RoutedApplication = lazy(() => import("./routes/RoutedApplication"))

export default function App() {
  return (
    <ApplicationErrorBoundary>
      <AuthorizationProvider>
        <AuthorizationBoundary>
          <Suspense fallback={<main className="mx-auto max-w-3xl p-6"><LoadingState label="Opening page" /></main>}>
            <RoutedApplication />
          </Suspense>
        </AuthorizationBoundary>
      </AuthorizationProvider>
    </ApplicationErrorBoundary>
  )
}
