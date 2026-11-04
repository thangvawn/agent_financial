import { useCallback, useEffect, useRef, useState } from 'react'
import '../../market-portfolio/pages/market-portfolio-panels.css'
import { fetchArticleDetail } from '../services'
import NewsFilters from './components/NewsFilters'
import NewsHighlightsSection from './components/NewsHighlightsSection'
import NewsFeedList from './components/NewsFeedList'
import NewsArticleReader from './components/NewsArticleReader'
import NewsDataStatus from './components/NewsDataStatus'
import useNewsHighlights from './hooks/useNewsHighlights'
import useNewsFeed from './hooks/useNewsFeed'
import useNewsAutoRefresh from './hooks/useNewsAutoRefresh'
import './news.css'
import './social.css'
import NewsWorkspaceTabs from './components/NewsWorkspaceTabs'

const DEFAULT_MARKET_LENS = 'vietnam'
const DEFAULT_TIME_RANGE_HOURS = 168
const MARKET_LENS_FILTERS = {
  vietnam: { preset: 'vietnam', region: 'VN', sourceGroup: '' },
  global: { preset: 'global_macro', region: '', sourceGroup: 'global_macro' },
  cross_impact: { preset: 'balanced', region: '', sourceGroup: '' },
}

export default function NewsPage({ onOpenSocial }) {
  // Filter state
  const [marketLens, setMarketLens] = useState(DEFAULT_MARKET_LENS)
  const [category, setCategory] = useState('all')
  const [query, setQuery] = useState('')
  const [timeRangeHours, setTimeRangeHours] = useState(DEFAULT_TIME_RANGE_HOURS)
  const [sentiment, setSentiment] = useState('')
  const [impactLevel, setImpactLevel] = useState('')
  const [importance, setImportance] = useState('')

  // Article details
  const [activeArticleId, setActiveArticleId] = useState('')
  const [articleDetail, setArticleDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [detailAttempt, setDetailAttempt] = useState(0)
  const [mobileTab, setMobileTab] = useState('feed')

  const {
    period: highlightPeriod,
    setPeriod: setHighlightPeriod,
    payload: highlightPayload,
    items: highlightItems,
    loading: highlightsLoading,
    error: highlightsError,
    refresh: refreshHighlights,
  } = useNewsHighlights({ limit: 8 })

  const feedSentinelRef = useRef(null)

  // Map preset / filters depending on lens selection
  const activeLensFilters = MARKET_LENS_FILTERS[marketLens] || MARKET_LENS_FILTERS.cross_impact
  const { preset, region, sourceGroup } = activeLensFilters
  const filterScope = JSON.stringify([marketLens, category, query, timeRangeHours, sentiment, impactLevel, importance])
  const [selectionScope, setSelectionScope] = useState(filterScope)
  if (selectionScope !== filterScope) {
    setSelectionScope(filterScope)
    setActiveArticleId('')
    setArticleDetail(null)
  }


  // Sync mobile tab automatically on mobile widths
  const selectArticle = useCallback((id) => {
    setActiveArticleId(id)
    if (window.matchMedia('(max-width: 899px)').matches) {
      setMobileTab('detail')
    }
  }, [])

  const feed = useNewsFeed({ category: category === 'all' ? '' : category, q: query,
    timeRangeHours, region, sourceGroup, preset, sentiment, impactLevel, importance })
  const { payload, loading, error, refresh: refreshFeed, loadingMore, loadMore, retry } = feed
  const refreshAll = useCallback(async (force = false) => {
    await refreshFeed({ force, background: !force })
    await refreshHighlights({ force: false })
  }, [refreshFeed, refreshHighlights])
  const autoRefresh = useCallback(() => refreshAll(false), [refreshAll])
  useNewsAutoRefresh(autoRefresh)

  useEffect(() => {
    if (mobileTab === 'detail' && window.matchMedia('(max-width: 899px)').matches) {
      document.getElementById('news-mobile-detail-panel')?.scrollIntoView({ block: 'start' })
    }
  }, [mobileTab, activeArticleId])

  // Fetch article detail
  useEffect(() => {
    if (!activeArticleId) { setArticleDetail(null); setDetailLoading(false); setDetailError(''); return }
    let cancelled = false
    const controller = new AbortController()
    async function loadDetail() {
      setDetailLoading(true)
      setDetailError('')
      try {
        const data = await fetchArticleDetail(activeArticleId, { signal: controller.signal })
        if (!cancelled) setArticleDetail(data)
      } catch {
        if (!cancelled) { setArticleDetail(null); setDetailError('Không thể tải phân tích bài viết. Vui lòng thử lại.') }
      } finally {
        if (!cancelled) setDetailLoading(false)
      }
    }
    loadDetail()
    return () => { cancelled = true; controller.abort() }
  }, [activeArticleId, detailAttempt])

  const handleResetFilters = () => {
    setMarketLens(DEFAULT_MARKET_LENS)
    setCategory('all')
    setQuery('')
    setTimeRangeHours(DEFAULT_TIME_RANGE_HOURS)
    setSentiment('')
    setImpactLevel('')
    setImportance('')
  }

  // Derived articles lists
  const articles = payload?.articles || []
  const matchingDetail = articleDetail?.article?.article_id === activeArticleId ? articleDetail : null
  const activeArticle = matchingDetail?.article
    || articles.find((article) => article.article_id === activeArticleId)
    || highlightItems.find((article) => article.article_id === activeArticleId)
    || (!activeArticleId ? articles[0] : null)
  const effectiveArticleId = activeArticleId || articles[0]?.article_id
  useEffect(() => {
    if (!activeArticleId && effectiveArticleId) setActiveArticleId(effectiveArticleId)
  }, [activeArticleId, effectiveArticleId])

  // Infinite scroll intersection observer
  useEffect(() => {
    const sentinel = feedSentinelRef.current
    if (!sentinel || !payload?.has_more || loading || loadingMore || error) return
    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting) {
        loadMore()
      }
    }, { root: sentinel.closest('.news-feed__scroll'), rootMargin: '50px 0px' })
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [payload?.has_more, articles.length, loading, loadingMore, loadMore, error])

  return (
    <section className="news-desk">
      <NewsWorkspaceTabs active="news" onSocial={onOpenSocial} />
      <NewsFilters
        marketLens={marketLens}
        onLensChange={value => { setMarketLens(value); setActiveArticleId('') }}
        query={query}
        onQueryChange={value => { setQuery(value); setActiveArticleId('') }}
        timeRangeHours={timeRangeHours}
        onTimeRangeHoursChange={setTimeRangeHours}
        sentiment={sentiment}
        onSentimentChange={setSentiment}
        impactLevel={impactLevel}
        onImpactLevelChange={setImpactLevel}
        importance={importance}
        onImportanceChange={setImportance}
        onResetFilters={handleResetFilters}
      />

      <NewsDataStatus payload={payload} loading={loading} error={error} pending={feed.pending} onRefresh={() => refreshAll(true)} />

      {/* Mobile Switch Tabs */}
      <div className="news-mobile-switch" role="group" aria-label="Chế độ xem tin tức">
        <button
          type="button"
          aria-pressed={mobileTab === 'feed'}
          aria-controls="news-mobile-feed-panel"
          className={mobileTab === 'feed' ? 'is-active' : ''}
          onClick={() => setMobileTab('feed')}
        >
          Dòng tin ({articles.length})
        </button>
        <button
          type="button"
          aria-pressed={mobileTab === 'detail'}
          aria-controls="news-mobile-detail-panel"
          className={mobileTab === 'detail' ? 'is-active' : ''}
          onClick={() => setMobileTab('detail')}
          disabled={!activeArticle}
        >
          Chi tiết bài đọc
        </button>
      </div>

      {/* Split studio: discovery on the left, reading on the right. */}
      <div className="news-desk-grid">
        <div
          id="news-mobile-feed-panel"
          role="region"
          aria-label="Dòng tin"
          className={`news-desk__pane news-desk__pane--stream${mobileTab === 'feed' ? ' is-mobile-active' : ''}`}
        >
          <NewsHighlightsSection
            period={highlightPeriod}
            payload={highlightPayload}
            items={highlightItems}
            loading={highlightsLoading}
            error={highlightsError}
            activeArticleId={activeArticleId}
            onPeriodChange={setHighlightPeriod}
            onSelect={selectArticle}
            onRetry={() => refreshHighlights({ force: false })}
          />

          <NewsFeedList
            articles={articles}
            feedArticles={articles}
            total={payload?.total || 0}
            loadingMore={loadingMore}
            onRetry={retry}
            activeArticleId={activeArticleId}
            onSelectArticle={selectArticle}
            category={category}
            onCategoryChange={value => { setCategory(value); setActiveArticleId('') }}
            loading={loading}
            error={error}
            feedSentinelRef={feedSentinelRef}
            onLoadMore={loadMore}
            hasMore={Boolean(payload?.has_more)}
          />
        </div>

        <div
          id="news-mobile-detail-panel"
          role="region"
          aria-label="Chi tiết bài đọc"
          className={`news-desk__pane news-desk__pane--reader${mobileTab === 'detail' ? ' is-mobile-active' : ''}`}
        >
          <NewsArticleReader
            activeArticle={activeArticle}
            detail={matchingDetail}
            detailLoading={detailLoading}
            error={detailError}
            onRetry={() => setDetailAttempt(v => v + 1)}
            onSelectRelated={selectArticle}
          />
        </div>
      </div>

      <footer className="news-desk__footer">
        Tin tức là bối cảnh phân tích, không phải khuyến nghị đầu tư. © Northstar Finance Lab.
      </footer>
    </section>
  )
}
