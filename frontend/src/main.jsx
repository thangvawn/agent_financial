import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { engine } from 'animejs'
import './index.css'
import App from './App.jsx'
import ErrorBoundary from './ErrorBoundary.jsx'
import QueryProvider from './shared/query/QueryProvider.jsx'

engine.timeUnit = 's'


createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryProvider>
        <App />
      </QueryProvider>
    </ErrorBoundary>
  </StrictMode>,
)
