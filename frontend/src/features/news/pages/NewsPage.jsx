import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  fetchArticleDetail,
  fetchNewsFeed,
  saveNewsArticle,
  unsaveNewsArticle,
} from '../services'
import FinancialLearningContext from '../../../shared/ui/FinancialLearningContext'
import NewsHeader from './components/NewsHeader'
import NewsFilters from './components/NewsFilters'
import TodayBriefSection from './components/TodayBriefSection'
import NewsFeedList from './components/NewsFeedList'
import NewsArticleReader from './components/NewsArticleReader'
import './news.css'

const FEED_LIST_INITIAL = 12
const FEED_LIST_STEP = 12

export default function NewsPage({ sessionId, onBack, onOpenGlobalTerminal }) {
  // Feed state
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Filter state
  const [marketLens, setMarketLens] = useState('vietnam')
  const [category, setCategory] = useState('all')
  const [query, setQuery] = useState('')
  const [timeRangeHours, setTimeRangeHours] = useState(168)
  const [sentiment, setSentiment] = useState('')
  const [impactLevel, setImpactLevel] = useState('')
  const [importance, setImportance] = useState('')

  // Article details & saved list
  const [activeArticleId, setActiveArticleId] = useState('')
  const [articleDetail, setArticleDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [savedIds, setSavedIds] = useState(new Set())
  const [feedVisible, setFeedVisible] = useState(FEED_LIST_INITIAL)
  const [mobileTab, setMobileTab] = useState('feed')

  const feedSentinelRef = useRef(null)

  // Map preset / filters depending on lens selection
  const preset = marketLens === 'vietnam' ? 'vietnam' : marketLens === 'global' ? 'global_macro' : ''
  const region = marketLens === 'vietnam' ? 'VN' : marketLens === 'global' ? 'global' : ''
  const sourceGroup = marketLens === 'vietnam' ? 'vn_markets' : marketLens === 'global' ? 'global_macro' : ''

  // Sync mobile tab automatically on mobile widths
  const selectArticle = useCallback((id) => {
    setActiveArticleId(id)
    if (window.matchMedia('(max-width: 1024px)').matches) {
      setMobileTab('detail')
    }
  }, [])

  // Fetch news feed
  useEffect(() => {
    let cancelled = false
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
        })
        if (!cancelled) {
          setPayload(data)
          setActiveArticleId((cur) => cur || data.articles?.[0]?.article_id || '')
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    const delayTimer = setTimeout(loadFeed, 250)
    return () => { cancelled = true; clearTimeout(delayTimer) }
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
        preset, force: true,
      })
      setPayload(data)
      setFeedVisible(FEED_LIST_INITIAL)
      setActiveArticleId(data.articles?.[0]?.article_id || '')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  // Toggle save article
  const handleSave = useCallback(async (articleId) => {
    const isSaved = savedIds.has(articleId)
    try {
      if (isSaved) {
        await unsaveNewsArticle(articleId)
        setSavedIds((prev) => { const next = new Set(prev); next.delete(articleId); return next })
      } else {
        await saveNewsArticle(articleId)
        setSavedIds((prev) => new Set(prev).add(articleId))
      }
    } catch { /* fail silently */ }
  }, [savedIds])

  const handleResetFilters = () => {
    setQuery('')
    setTimeRangeHours(168)
    setSentiment('')
    setImpactLevel('')
    setImportance('')
  }

  // Derived articles lists
  const articles = payload?.articles || []
  const feedArticles = articles.slice(0, Math.min(feedVisible, articles.length))
  const activeArticle = articles.find((a) => a.article_id === activeArticleId) || articles[0]
  const todayBrief = payload?.today_brief || []

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
    <section className="news-desk px-4 md:px-6 py-6 text-[#f8fafc] font-sans max-w-[1480px] mx-auto min-h-screen">
      <NewsHeader
        topBrief={todayBrief[0]}
        onSelectTopBrief={() => selectArticle(todayBrief[0]?.article_id)}
        onRefresh={handleRefresh}
        loading={loading}
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

      <TodayBriefSection
        todayBrief={todayBrief}
        activeArticleId={activeArticleId}
        savedIds={savedIds}
        onSelectBrief={selectArticle}
        onSaveBrief={handleSave}
      />

      {/* Mobile Switch Tabs */}
      <div className="flex lg:hidden bg-[#0f1420] border border-[#1f293d] rounded-md p-0.5 mb-4 shrink-0">
        <button
          type="button"
          className={`flex-1 text-center py-2 text-xs font-bold rounded cursor-pointer transition-all ${
            mobileTab === 'feed' ? 'bg-[#1f293d] text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
          onClick={() => setMobileTab('feed')}
        >
          Dòng tin ({articles.length})
        </button>
        <button
          type="button"
          className={`flex-1 text-center py-2 text-xs font-bold rounded cursor-pointer transition-all ${
            mobileTab === 'detail' ? 'bg-[#1f293d] text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
          onClick={() => setMobileTab('detail')}
          disabled={!activeArticle}
        >
          Chi tiết bài đọc
        </button>
      </div>

      {/* Responsive grid style — feed column is FIXED width, never changes */}
      <style dangerouslySetInnerHTML={{ __html: `
        .news-desk-grid {
          display: grid !important;
          gap: 24px !important;
          align-items: start !important;
          grid-template-columns: 1fr !important;
        }
        @media (min-width: 1024px) {
          .news-desk-grid {
            grid-template-columns: 420px 1fr !important;
          }
        }
        @media (min-width: 1440px) {
          .news-desk-grid {
            grid-template-columns: 480px 1fr !important;
          }
        }
      `}} />

      {/* Workspace Split Desk */}
      <div className="news-desk-grid">
        <div className={mobileTab === 'feed' ? 'block' : 'hidden lg:block'}>
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

        <div className={mobileTab === 'detail' ? 'block' : 'hidden lg:block'}>
          <NewsArticleReader
            activeArticle={activeArticle}
            detail={articleDetail}
            detailLoading={detailLoading}
            savedIds={savedIds}
            onSave={handleSave}
            onSelectRelated={selectArticle}
          />
        </div>
      </div>

      <footer className="text-center text-[10px] text-slate-500 font-bold border-t border-[#1f293d]/50 mt-10 pt-4 pb-2">
        Tin tức là bối cảnh phân tích, không phải khuyến nghị đầu tư. © Northstar Finance Lab.
      </footer>
    </section>
  )
}
