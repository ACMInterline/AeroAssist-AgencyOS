import { Component } from "react"
import ErrorState from "./ErrorState"

export default class ApplicationErrorBoundary extends Component {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  componentDidCatch(error) {
    console.error("AeroAssist view failed to render.", {
      name: error?.name || "Error",
    })
  }

  retry = () => {
    this.setState({ failed: false })
    window.location.reload()
  }

  render() {
    if (!this.state.failed) return this.props.children
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl items-center px-6 py-12">
        <ErrorState
          message="The page encountered an unexpected display error. Your existing work has not been changed."
          onRetry={this.retry}
          title="This view needs to be reopened"
        />
      </main>
    )
  }
}
