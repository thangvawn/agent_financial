import { useEffect, useMemo, useState } from 'react'

import { fetchInsightsDashboard } from '../../modules/insights'
import {
  CrossAssetPulseChart,
  EventCalendarCard,
  LearnFromInsightsCard,
  MarketIntelligenceHero,
  MarketNarrativeCard,
  ScenarioMonitorCard,
  SectorRotationCard,
  SnapshotRow,
  TrendRadarCard,
  WatchlistImpactCard,
} from './InsightsSections'
import { adaptDashboard } from './insightsModel'
import { trackAnalyticsEvent } from '../../shared/analytics/trackEvent'
import './insights.css'

export default function InsightsPage({ sessionId, onOpenLearning, onOpenGuidedInvesting }) {
  const [apiData, setApiData] = useState(null)
  const [range, setRange] = useState('1M')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const payload = await fetchInsightsDashboard({ sessionId, range })
        if (active) setApiData(payload)
      } catch (err) {
        if (active) setError(err.message || 'Không tải được Insights.')
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [sessionId, range])

  const data = useMemo(() => adaptDashboard(apiData), [apiData])

  function openLearn() {
    trackAnalyticsEvent({ event_name: 'insights_learn_link_clicked', module: 'insights', surface: 'insights', session_id: sessionId })
    onOpenLearning?.()
  }

  function reviewExposure() {
    trackAnalyticsEvent({ event_name: 'insights_review_exposure_clicked', module: 'insights', surface: 'insights', session_id: sessionId })
    onOpenGuidedInvesting?.('watchlist')
  }

  return (
    <section className="insights-v2">
      {error ? <div className="insights-v2__notice">Đang dùng dữ liệu mẫu do API tạm thời chưa sẵn sàng.</div> : null}
      <MarketIntelligenceHero summary={data.marketSummary} onReview={reviewExposure} />
      <SnapshotRow summary={data.marketSummary} />

      <section className="insights-v2__grid insights-v2__grid--top">
        <MarketNarrativeCard narrative={data.narrative} loading={loading} />
        <TrendRadarCard rows={data.trendRadar} />
      </section>

      <section className="insights-v2__grid insights-v2__grid--middle">
        <CrossAssetPulseChart series={data.crossAssetSeries} range={range} onRange={setRange} />
        <ScenarioMonitorCard scenarios={data.scenarios} />
        <SectorRotationCard sectors={data.sectors} />
      </section>

      <section className="insights-v2__grid insights-v2__grid--bottom">
        <WatchlistImpactCard rows={data.watchlistImpact} />
        <LearnFromInsightsCard links={data.learnLinks} onOpen={openLearn} />
        <EventCalendarCard events={data.macroEvents} />
      </section>
      <p className="insights-v2__disclaimer">Insights là bối cảnh phân tích, không phải khuyến nghị mua/bán.</p>
    </section>
  )
}
