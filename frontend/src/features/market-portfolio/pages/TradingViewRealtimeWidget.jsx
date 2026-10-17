import { useEffect, useRef, memo } from 'react'
import { resolveTradingViewSymbol } from './tradingViewUtils'

export function TradingViewRealtimeWidget({
  symbol = 'XAU',
  height = 680,
  interval = 'D',
  ariaLabel = 'Biểu đồ kỹ thuật TradingView Realtime',
}) {
  const containerRef = useRef(null)

  const isDark = (() => {
    if (typeof document === 'undefined') return true
    return (
      document.documentElement.dataset.theme === 'dark' ||
      document.documentElement.closest('[data-theme="dark"]') != null ||
      document.querySelector('[data-theme="dark"]') != null
    )
  })()

  const tvSymbol = resolveTradingViewSymbol(symbol)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.innerHTML = ''

    const widgetDiv = document.createElement('div')
    widgetDiv.className = 'tradingview-widget-container__widget'
    widgetDiv.style.height = `${height}px`
    widgetDiv.style.minHeight = `${height}px`
    widgetDiv.style.width = '100%'
    container.appendChild(widgetDiv)

    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js'
    script.type = 'text/javascript'
    script.async = true
    script.innerHTML = JSON.stringify({
      autosize: false,
      width: '100%',
      height: height,
      symbol: tvSymbol,
      interval: interval,
      timezone: 'Asia/Ho_Chi_Minh',
      theme: isDark ? 'dark' : 'light',
      style: '1',
      locale: 'vi_VN',
      enable_publishing: false,
      allow_symbol_change: true,
      hide_side_toolbar: false,
      withdateranges: true,
      details: false,
      hotlist: false,
      calendar: false,
      show_popup_button: true,
      popup_width: '1200',
      popup_height: '800',
      support_host: 'https://www.tradingview.com',
    })

    container.appendChild(script)

    return () => {
      container.innerHTML = ''
    }
  }, [tvSymbol, isDark, interval, height])

  return (
    <div
      ref={containerRef}
      className="tradingview-widget-container"
      style={{
        height: `${height}px`,
        minHeight: `${height}px`,
        width: '100%',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
      aria-label={ariaLabel}
    />
  )
}

export default memo(TradingViewRealtimeWidget)
