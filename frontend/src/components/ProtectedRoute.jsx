import ErrorState from "./ErrorState"
import LoadingState from "./LoadingState"

export default function ProtectedRoute({ loading, error, children }) {
  if (loading) {
    return <LoadingState />
  }

  if (error) {
    return <ErrorState message={error} />
  }

  return children
}
