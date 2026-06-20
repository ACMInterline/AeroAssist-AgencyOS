import LoadingState from "./LoadingState"

export default function ProtectedRoute({ loading, error, children }) {
  if (loading) {
    return <LoadingState label="Checking demo session" />
  }

  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800">
        {error}
      </div>
    )
  }

  return children
}
