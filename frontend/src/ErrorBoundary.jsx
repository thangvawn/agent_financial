import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: '#0f172a',
          color: '#e2e8f0',
          fontFamily: 'system-ui, sans-serif',
          padding: 32,
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
          <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 8 }}>
            Hệ thống gặp lỗi không mong muốn
          </h1>
          <p style={{ color: '#94a3b8', maxWidth: 480, marginBottom: 24 }}>
            Vui lòng tải lại trang. Nếu lỗi tiếp tục xảy ra, hãy liên hệ đội kỹ thuật.
          </p>
          <code style={{
            background: '#1e293b',
            padding: '8px 16px',
            borderRadius: 8,
            fontSize: 13,
            color: '#f87171',
            marginBottom: 24,
            maxWidth: 600,
            overflow: 'auto',
          }}>
            {this.state.error?.message || 'Unknown error'}
          </code>
          <button
            onClick={() => window.location.reload()}
            style={{
              background: '#3b82f6',
              color: '#fff',
              border: 'none',
              padding: '10px 24px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            Tải lại trang
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
