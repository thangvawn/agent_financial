import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchArticleDetail, fetchNewsFeed } from '../services'
import FinancialLearningContext from '../../../shared/ui/FinancialLearningContext'
import NewsHeader from './components/NewsHeader'
import NewsFilters from './components/NewsFilters'
import NewsHighlightsSection from './components/NewsHighlightsSection'
import NewsFeedList from './components/NewsFeedList'
import NewsArticleReader from './components/NewsArticleReader'
import useNewsHighlights from './hooks/useNewsHighlights'
import './news.css'

const FEED_LIST_INITIAL = 12
const FEED_LIST_STEP = 12
const DEFAULT_MARKET_LENS = 'vietnam'
const DEFAULT_TIME_RANGE_HOURS = 168
const MARKET_LENS_FILTERS = {
  vietnam: { preset: 'vietnam', region: 'VN', sourceGroup: '' },
  global: { preset: 'global_macro', region: '', sourceGroup: 'global_macro' },
  cross_impact: { preset: 'balanced', region: '', sourceGroup: '' },
}

export default function NewsPage() {
  // Feed state
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
  const [feedVisible, setFeedVisible] = useState(FEED_LIST_INITIAL)
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

  // Sync mobile tab automatically on mobile widths
  const selectArticle = useCallback((id) => {
    setActiveArticleId(id)
    if (window.matchMedia('(max-width: 899px)').matches) {
      setMobileTab('detail')
    }
  }, [])

  // Fetch news feed
  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()
    async function loadFeed() {
      setLoading(true)
      setError('')
      try {
        const data = await fetchNewsFeed({
          category: category === 'all' ? '' : category,
          q: query,
          limit: 80,
          timeRangeHours,
          region,
          sourceGroup,
          preset,
          sentiment: sentiment || undefined,
          impactLevel: impactLevel || undefined,
          importance: importance || undefined,
          signal: controller.signal,
        })
        if (!cancelled) {
          setPayload(data)
          setActiveArticleId((current) => {
            const hasCurrent = data.articles?.some((article) => article.article_id === current)
            return hasCurrent ? current : data.articles?.[0]?.article_id || ''
          })
        }
      } catch (err) {
        if (!cancelled && err.name !== 'AbortError') setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    const delayTimer = setTimeout(loadFeed, 250)
    return () => { cancelled = true; clearTimeout(delayTimer); controller.abort() }
  }, [category, query, preset, region, sourceGroup, timeRangeHours, sentiment, impactLevel, importance])

  // Fetch article detail
  useEffect(() => {
    if (!activeArticleId) { setArticleDetail(null); return }
    let cancelled = false
    async function loadDetail() {
      setDetailLoading(true)
      try {
        const data = await fetchArticleDetail(activeArticleId)
        if (!cancelled) setArticleDetail(data)
      } catch {
        if (!cancelled) setArticleDetail(null)
      } finally {
        if (!cancelled) setDetailLoading(false)
      }
    }
    loadDetail()
    return () => { cancelled = true }
  }, [activeArticleId])

  useEffect(() => {
    setFeedVisible(FEED_LIST_INITIAL)
  }, [category, query, preset, region, sourceGroup, timeRangeHours, sentiment, impactLevel, importance])

  // Refresh handler
  const handleRefresh = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await fetchNewsFeed({
        category: category === 'all' ? '' : category,
        q: query, limit: 80, timeRangeHours, region, sourceGroup,
        preset, force: true, sentiment, impactLevel, importance,
      })
      setPayload(data)
      setFeedVisible(FEED_LIST_INITIAL)
      setActiveArticleId((current) => {
        const hasCurrent = data.articles?.some((article) => article.article_id === current)
        return hasCurrent ? current : data.articles?.[0]?.article_id || ''
      })
    } catch (err) { setError(err.message) }
    finally {
      await refreshHighlights({ force: false })
      setLoading(false)
    }
  }

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
  const feedArticles = articles.slice(0, Math.min(feedVisible, articles.length))
  const matchingDetail = articleDetail?.article?.article_id === activeArticleId ? articleDetail : null
  const activeArticle = matchingDetail?.article
    || articles.find((article) => article.article_id === activeArticleId)
    || highlightItems.find((article) => article.article_id === activeArticleId)
    || (!activeArticleId ? articles[0] : null)
  const todayBrief = payload?.today_brief || []
  const topHighlight = highlightItems[0] || todayBrief[0]

  // Infinite scroll intersection observer
  useEffect(() => {
    const sentinel = feedSentinelRef.current
    if (!sentinel || feedVisible >= articles.length) return
    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting) {
        setFeedVisible((prev) => Math.min(prev + FEED_LIST_STEP, articles.length))
      }
    }, { rootMargin: '100px 0px' })
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [articles.length, feedVisible])

  return (
    <section className="news-desk">
      <NewsHeader
        topHighlight={topHighlight}
        onSelectTopHighlight={() => selectArticle(topHighlight?.article_id)}
        onRefresh={handleRefresh}
        loading={loading || highlightsLoading}
        freshness={payload?.freshness || 'loading'}
        sourceCount={payload?.source_count || 0}
        successfulSourceCount={payload?.successful_source_count || 0}
      />

      <FinancialLearningContext
        objective="Phân biệt sự kiện, nhận định và tác động có thể xảy ra thay vì phản ứng theo tiêu đề."
        practice="Đọc nguồn, kiểm tra thời điểm, so sánh nhiều góc nhìn rồi ghi lại giả thuyết cần theo dõi."
        riskNote="Sắc thái và mức tác động chỉ hỗ trợ sàng lọc. Tin tức không phải tín hiệu mua bán và có thể thay đổi nhanh."
      />

      <NewsFilters
        marketLens={marketLens}
        onLensChange={setMarketLens}
        query={query}
        onQueryChange={setQuery}
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
            feedArticles={feedArticles}
            activeArticleId={activeArticleId}
            onSelectArticle={selectArticle}
            category={category}
            onCategoryChange={setCategory}
            loading={loading}
            error={error}
            feedSentinelRef={feedSentinelRef}
            onLoadMore={() => setFeedVisible((v) => Math.min(v + FEED_LIST_STEP, articles.length))}
            hasMore={feedArticles.length < articles.length}
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
