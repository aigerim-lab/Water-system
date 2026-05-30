import React from 'react'

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null, componentStack: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('AquaMonitor render error:', error, info)
    this.setState({ componentStack: info?.componentStack || null })
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.error) {
      const { error, componentStack } = this.state
      return (
        <div className="error-boundary" style={{ margin: '2rem', maxWidth: 720 }}>
          <h2 style={{ marginBottom: '0.75rem', fontSize: '1.25rem' }}>UI error</h2>
          <p style={{ marginBottom: '0.5rem', fontWeight: 600 }}>{error?.message || String(error)}</p>
          {componentStack && (
            <pre
              style={{
                marginTop: '1rem',
                padding: '1rem',
                overflow: 'auto',
                fontSize: '0.75rem',
                background: 'rgba(0,0,0,0.35)',
                borderRadius: 8,
                whiteSpace: 'pre-wrap',
              }}
            >
              {componentStack.trim()}
            </pre>
          )}
          <button
            type="button"
            className="btn-primary"
            style={{ marginTop: '1.25rem' }}
            onClick={this.handleReload}
          >
            Reload application
          </button>
          {this.props.fallback}
        </div>
      )
    }
    return this.props.children
  }
}
