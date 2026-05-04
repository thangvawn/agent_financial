import { useEffect, useState } from 'react'

import {
  createCommunityComment,
  createCommunityPost,
  fetchCommunityHome,
  fetchCommunityPosts,
  joinCommunitySpace,
  updateCommunityNotificationState,
} from '../../modules/community'
import {
  UsersIcon, MessageSquareIcon, ThumbsUpIcon, BookmarkIcon, ShareIcon,
  TrophyIcon, HashIcon, FilterIcon, ImageIcon, SearchIcon, EditIcon,
  ShieldIcon, TargetIcon, BarChartIcon, FlagIcon, GlobeIcon, CheckCircleIcon,
  ArrowRightIcon, ClockIcon, StarIcon, PiggyBankIcon, CalculatorIcon,
  ScaleIcon, ShieldPlusIcon, FileTextIcon, PieChartIcon, CalendarIcon,
} from '../../shared/Icons'
import './community.css'

const SPACE_ICONS = {
  shield: ShieldIcon,
  target: TargetIcon,
  bar_chart: BarChartIcon,
  flag: FlagIcon,
  users: UsersIcon,
  globe: GlobeIcon,
}

const TOPIC_ICONS = [
  { key: 'market-discussion', label: 'Market Discussion', sub: 'Thảo luận xu hướng, tin tức thị trường', posts: '12.6K bài viết', Icon: BarChartIcon },
  { key: 'bctc-analysis', label: 'BCTC Analysis', sub: 'Phân tích BCTC, đánh giá doanh nghiệp', posts: '8.9K bài viết', Icon: FileTextIcon },
  { key: 'portfolio-basics', label: 'Portfolio Basics', sub: 'Xây dựng danh mục, phân bổ tài sản', posts: '6.2K bài viết', Icon: PieChartIcon },
  { key: 'goals-personal-finance', label: 'Goals & Personal Finance', sub: 'Quỹ tài chính cá nhân, mục tiêu', posts: '4.7K bài viết', Icon: TargetIcon },
  { key: 'pro-lab-research', label: 'Pro Lab Research', sub: 'Nghiên cứu chuyên sâu & phân tích', posts: '3.3K bài viết', Icon: ScaleIcon },
]

const DEMO_POSTS = [
  {
    id: 'demo-1',
    author: 'Minh Hoàng',
    badge: 'Pro Lab Member',
    time: '2 giờ trước',
    title: 'Góc nhìn BCTC: KQKD Q1/2024 của MWG – Tăng trưởng lợi nhuận trở lại',
    body: 'MWG ghi nhận doanh thu thuần 30 nghìn tỷ (+25% YoY). Biên gộp cải thiện nhờ cơ cấu sản phẩm và tỷ lệ trích lập dự phòng. Mình tập trung phân tích 3 điểm: Biên hoạt động, Bình lưu hàng tồn kho...',
    tags: ['BCTC', 'VN30', 'Retail', 'Fundamental'],
    votes: 74,
    comments: 45,
    shares: 12,
  },
  {
    id: 'demo-2',
    author: 'Lan Anh',
    badge: 'Newbie',
    time: '4 giờ trước',
    title: 'Câu hỏi: Nên phân bổ tài sản như thế nào khi mới bắt đầu đầu tư?',
    body: 'Mình vừa bắt đầu tìm hiểu về đầu tư, thu nhập hàng tháng 8-10 triệu. Mọi người có thể chia sẻ về cách phân bổ tài sản ban đầu không? Mình có thể bỏ ra khoảng 15-20% thu nhập hàng tháng để đầu tư.',
    tags: ['Question', 'Portfolio Basics', 'Risk'],
    votes: 27,
    comments: 39,
    shares: 12,
  },
  {
    id: 'demo-3',
    author: 'Quang Huy',
    badge: 'Active Member',
    time: '6 giờ trước',
    title: 'Bài học rút ra: Đừng để cảm xúc chi phối quyết định đầu tư',
    body: 'Tuần trước FOMO đã khiến mình mở vị trí trong lúc thị trường đang tăng mạnh trong 5 phiên. Bài học: Mình cần kế hoạch đầu tư rõ ràng, đặc biệt là stop-loss và position sizing trước khi vào lệnh...',
    tags: ['Lesson Learned', 'Risk Management'],
    votes: 63,
    comments: 18,
    shares: 31,
  },
]

const FEED_TABS = ['Nổi bật', 'Mới nhất', 'Đang theo dõi', 'Q&A']

export default function CommunityPage({
  sessionId,
  initialSpaceId = '',
  onBack,
  onOpenLearning,
  onOpenGoals,
  onOpenModeration,
}) {
  const [home, setHome] = useState(null)
  const [selectedSpaceId, setSelectedSpaceId] = useState(initialSpaceId)
  const [posts, setPosts] = useState([])
  const [form, setForm] = useState({ title: '', body: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitResult, setSubmitResult] = useState(null)
  const [commentDrafts, setCommentDrafts] = useState({})
  const [activeTab, setActiveTab] = useState('Nổi bật')

  useEffect(() => {
    let cancelled = false
    async function run() {
      if (!sessionId) return
      setLoading(true)
      setError('')
      try {
        const payload = await fetchCommunityHome(sessionId)
        if (cancelled) return
        setHome(payload)
        const recommended = initialSpaceId || payload.recommended_space_ids[0] || payload.spaces[0]?.space_id || ''
        setSelectedSpaceId(recommended)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [sessionId, initialSpaceId])

  useEffect(() => {
    let cancelled = false
    async function run() {
      if (!selectedSpaceId) { setPosts([]); return }
      try {
        const payload = await fetchCommunityPosts(selectedSpaceId)
        if (!cancelled) setPosts(payload)
      } catch (err) {
        if (!cancelled) setError(err.message)
      }
    }
    run()
    return () => { cancelled = true }
  }, [selectedSpaceId])

  async function handleJoin(spaceId) {
    setError('')
    try {
      await joinCommunitySpace(sessionId, spaceId)
      const payload = await fetchCommunityHome(sessionId)
      setHome(payload)
      setSelectedSpaceId(spaceId)
    } catch (err) { setError(err.message) }
  }

  async function handlePost() {
    if (!selectedSpaceId) return
    setError('')
    try {
      const payload = await createCommunityPost({
        session_id: sessionId,
        space_id: selectedSpaceId,
        post_type: 'discussion',
        title: form.title || 'Thảo luận mới',
        body: form.body,
      })
      setSubmitResult(payload)
      const nextPosts = await fetchCommunityPosts(selectedSpaceId)
      setPosts(nextPosts)
      const nextHome = await fetchCommunityHome(sessionId)
      setHome(nextHome)
      setForm({ title: '', body: '' })
    } catch (err) { setError(err.message) }
  }

  async function handleComment(postId, parentCommentId = '') {
    const key = draftKey(postId, parentCommentId)
    const body = (commentDrafts[key] || '').trim()
    if (!body) return
    setError('')
    try {
      await createCommunityComment({
        session_id: sessionId,
        post_id: postId,
        body,
        parent_comment_id: parentCommentId || null,
      })
      setCommentDrafts((c) => ({ ...c, [key]: '' }))
      const nextPosts = await fetchCommunityPosts(selectedSpaceId)
      setPosts(nextPosts)
    } catch (err) { setError(err.message) }
  }

  if (!sessionId) return <p className="text-sm text-slate-600">Chưa có session onboarding.</p>
  if (loading) return <p className="text-sm text-slate-600">Đang tải Community...</p>
  if (error && !home) return <p className="community-error">{error}</p>
  if (!home) return <p className="text-sm text-slate-600">Chưa có dữ liệu Community.</p>

  const stats = home.stats || {}
  const topContributors = home.top_contributors || []
  const trendingTopics = home.trending_topics || []
  const events = home.community_events || []
  const savedDiscussions = home.saved_discussions || []
  const selectedSpace = home.spaces.find((s) => s.space_id === selectedSpaceId) || null

  return (
    <section className="community-page">
      {error ? <p className="community-error">{error}</p> : null}

      {/* ===== HERO ===== */}
      <div className="community-hero">
        <div className="community-hero__copy">
          <h1>Community</h1>
          <p>
            Nơi nhà đầu tư và người học cùng chia sẻ, thảo luận, đặt câu hỏi
            và chia sẻ nghiên cứu một cách có trách nhiệm.
            Giáo dục là trọng tâm – nơi không có pump &amp; dump, tín hiệu mù quáng.
          </p>
          <div className="community-hero__badges">
            <span className="community-hero__badge"><ShieldIcon size={14} /> Moderated</span>
            <span className="community-hero__badge"><FileTextIcon size={14} /> Research-first</span>
            <span className="community-hero__badge"><CheckCircleIcon size={14} /> No buy/sell guarantee</span>
          </div>
          <div className="community-hero__actions">
            <button type="button" className="community-btn community-btn--primary" onClick={() => document.getElementById('community-composer')?.focus()}>
              <EditIcon size={16} /> Tạo bài viết
            </button>
            <button type="button" className="community-btn community-btn--outline">
              <SearchIcon size={16} /> Khám phá chủ đề
            </button>
            <button type="button" className="community-btn community-btn--outline">
              <UsersIcon size={16} /> Hỏi cộng đồng
            </button>
          </div>
        </div>

        <div className="community-hero__stats-card">
          <h3>Cộng đồng Northstar</h3>
          <div className="community-hero__stats-mini">
            <div className="community-hero__stat">
              <span className="community-hero__stat-label">Thành viên</span>
              <span className="community-hero__stat-value">{stats.active_members || '36.2K'}</span>
              <span className="community-hero__stat-delta">{stats.active_members_delta || ''}</span>
            </div>
            <div className="community-hero__stat">
              <span className="community-hero__stat-label">Thảo luận hôm nay</span>
              <span className="community-hero__stat-value">{stats.discussions_today || 0}</span>
              <span className="community-hero__stat-delta">{stats.discussions_delta || ''}</span>
            </div>
            <div className="community-hero__stat">
              <span className="community-hero__stat-label">Tỉ lệ tương tác</span>
              <span className="community-hero__stat-value">68%</span>
              <span className="community-hero__stat-delta">↑ 5.1%</span>
            </div>
            <div className="community-hero__stat">
              <span className="community-hero__stat-label">Moderation</span>
              <span className="community-hero__stat-value">{stats.moderation_status || 'Ổn định'}</span>
              <span className="community-hero__stat-delta">{stats.moderation_note || ''}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ===== STATS BAR ===== */}
      <div className="community-stats">
        <div className="community-stat-card">
          <div className="community-stat-card__icon"><UsersIcon size={20} /></div>
          <div className="community-stat-card__content">
            <p>Thành viên hoạt động</p>
            <strong>{stats.active_members || '36.2K'}</strong>
            <span>{stats.active_members_delta || ''}</span>
          </div>
        </div>
        <div className="community-stat-card">
          <div className="community-stat-card__icon"><MessageSquareIcon size={20} /></div>
          <div className="community-stat-card__content">
            <p>Thảo luận hôm nay</p>
            <strong>{stats.discussions_today || 0}</strong>
            <span>{stats.discussions_delta || ''}</span>
          </div>
        </div>
        <div className="community-stat-card">
          <div className="community-stat-card__icon"><BarChartIcon size={20} /></div>
          <div className="community-stat-card__content">
            <p>Watchlist được chia sẻ</p>
            <strong>{stats.watchlists_shared || '1.25K'}</strong>
            <span>{stats.watchlists_delta || ''}</span>
          </div>
        </div>
        <div className="community-stat-card">
          <div className="community-stat-card__icon"><CheckCircleIcon size={20} /></div>
          <div className="community-stat-card__content">
            <p>Câu hỏi đã được trả lời</p>
            <strong>{stats.questions_answered || 0}</strong>
            <span>{stats.questions_delta || ''}</span>
          </div>
        </div>
        <div className="community-stat-card">
          <div className="community-stat-card__icon" style={{ background: '#f0fdf4', color: '#16a34a' }}>
            <ShieldIcon size={20} />
          </div>
          <div className="community-stat-card__content">
            <p>Tình trạng kiểm duyệt</p>
            <strong>{stats.moderation_status || 'Ổn định'}</strong>
            <span style={{ color: '#16a34a' }}>{stats.moderation_note || ''}</span>
          </div>
        </div>
      </div>

      {/* ===== MAIN (Feed + Sidebar) ===== */}
      <div className="community-main">
        {/* --- Feed Column --- */}
        <div className="community-feed">
          <div className="community-feed-header">
            <h2>Bảng tin cộng đồng</h2>
            <div className="community-feed-tabs">
              {FEED_TABS.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`community-feed-tab${activeTab === tab ? ' is-active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {/* Post Composer */}
          <div className="community-composer">
            <div className="community-composer__input-row">
              <div className="community-composer__avatar">NP</div>
              <input
                id="community-composer"
                className="community-composer__placeholder"
                placeholder="Bạn muốn chia sẻ điều gì?"
                value={form.body}
                onChange={(e) => setForm((c) => ({ ...c, body: e.target.value }))}
              />
              <button type="button" className="community-composer__btn" onClick={handlePost}>Đăng bài</button>
            </div>
            <div className="community-composer__types">
              <button type="button" className="community-composer__type-btn"><ImageIcon size={14} /> Ảnh</button>
              <button type="button" className="community-composer__type-btn"><BarChartIcon size={14} /> Poll</button>
              <button type="button" className="community-composer__type-btn"><HashIcon size={14} /> Gắn mã (ticker)</button>
            </div>
          </div>

          {/* Submit Result */}
          {submitResult ? (
            <div className="community-post-card" style={{ borderColor: '#ccfbf1', background: '#f0fdfa' }}>
              <strong style={{ color: '#0d9488' }}>Kết quả moderation: {submitResult.moderation_status}</strong>
              {submitResult.moderation_message ? <p style={{ fontSize: '0.85rem', color: '#475569' }}>{submitResult.moderation_message}</p> : null}
            </div>
          ) : null}

          {/* Demo Posts */}
          {DEMO_POSTS.map((post) => (
            <article key={post.id} className="community-post-card">
              <div className="community-post-card__author">
                <div className="community-post-card__avatar">{post.author[0]}</div>
                <div className="community-post-card__author-info">
                  <strong>{post.author} <span className="community-post-card__author-badge">{post.badge}</span></strong>
                  <small>{post.time}</small>
                </div>
              </div>
              <div className="community-post-card__body">
                <h3>{post.title}</h3>
                <p>{post.body}</p>
              </div>
              <div className="community-post-card__tags">
                {post.tags.map((t) => <span key={t} className="community-tag">{t}</span>)}
              </div>
              <div className="community-post-card__actions">
                <button type="button" className="community-post-action"><ThumbsUpIcon size={16} /> {post.votes}</button>
                <button type="button" className="community-post-action"><MessageSquareIcon size={16} /> {post.comments}</button>
                <button type="button" className="community-post-action"><ShareIcon size={16} /> {post.shares}</button>
                <span style={{ flex: 1 }} />
                <button type="button" className="community-post-action">Tham gia thảo luận</button>
              </div>
            </article>
          ))}

          {/* Real Posts from API */}
          {posts.map((post) => (
            <article key={post.post_id} className="community-post-card">
              <div className="community-post-card__author">
                <div className="community-post-card__avatar">{(post.user_id || 'U')[0].toUpperCase()}</div>
                <div className="community-post-card__author-info">
                  <strong>{post.user_id}</strong>
                  <small>{post.moderation_status} · {new Date(post.created_at).toLocaleDateString('vi-VN')}</small>
                </div>
              </div>
              <div className="community-post-card__body">
                <h3>{post.title}</h3>
                <p>{post.body}</p>
              </div>
              {selectedSpace?.is_joined ? (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    className="community-composer__placeholder"
                    value={commentDrafts[draftKey(post.post_id)] || ''}
                    onChange={(e) => setCommentDrafts((c) => ({ ...c, [draftKey(post.post_id)]: e.target.value }))}
                    placeholder="Bình luận..."
                  />
                  <button type="button" className="community-composer__btn" onClick={() => handleComment(post.post_id)}>Gửi</button>
                </div>
              ) : null}
              {post.comments?.length ? (
                <div style={{ paddingLeft: '1rem' }}>
                  {post.comments.map((c) => (
                    <div key={c.comment_id} style={{ padding: '0.5rem 0', borderTop: '1px solid #f1f5f9', fontSize: '0.85rem', color: '#475569' }}>
                      <strong style={{ color: '#0f172a' }}>{c.user_id}</strong>: {c.body}
                    </div>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
        </div>

        {/* --- Sidebar --- */}
        <div className="community-sidebar">
          {/* Trending Topics */}
          <div className="community-widget">
            <div className="community-widget__head">
              <h3>Chủ đề nổi bật</h3>
              <button type="button" className="community-widget__link">Xem tất cả</button>
            </div>
            <div className="community-topics-row">
              {trendingTopics.map((t) => (
                <span key={t.topic_id} className="community-topic-chip">{t.label}</span>
              ))}
            </div>
          </div>

          {/* Groups / Clubs */}
          <div className="community-widget">
            <div className="community-widget__head">
              <h3>Nhóm / Club bạn có thể quan tâm</h3>
              <button type="button" className="community-widget__link">Xem tất cả</button>
            </div>
            <div className="community-groups-list">
              {home.spaces.slice(0, 4).map((space) => {
                const Icon = SPACE_ICONS[space.icon_key] || UsersIcon
                return (
                  <div key={space.space_id} className="community-group-row" onClick={() => setSelectedSpaceId(space.space_id)}>
                    <div className="community-group-row__icon"><Icon size={18} /></div>
                    <div className="community-group-row__info">
                      <strong>{space.title}</strong>
                      <span>{(space.member_count / 1000).toFixed(1)}K thành viên</span>
                    </div>
                    {!space.is_joined ? (
                      <button type="button" className="community-group-row__join" onClick={(e) => { e.stopPropagation(); handleJoin(space.space_id) }}>Tham gia</button>
                    ) : null}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Leaderboard */}
          <div className="community-widget">
            <div className="community-widget__head">
              <h3>Leaderboard / Thành viên tích cực</h3>
              <button type="button" className="community-widget__link">Xem bảng đầy đủ</button>
            </div>
            <div className="community-leaderboard">
              {topContributors.map((c) => (
                <div key={c.rank} className="community-leaderboard-row">
                  <div className={`community-leaderboard-rank community-leaderboard-rank--${c.rank}`}>{c.rank}</div>
                  <div className="community-leaderboard-avatar">{c.display_name[0]}</div>
                  <div className="community-leaderboard-info">
                    <strong>{c.display_name}</strong>
                    <span>{c.role_badge}</span>
                  </div>
                  <div className="community-leaderboard-points">
                    <StarIcon size={14} fill="currentColor" /> {c.points.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Community Guidelines */}
          <div className="community-widget">
            <div className="community-widget__head">
              <h3>Community Guidelines</h3>
            </div>
            <div className="community-guidelines-list">
              {home.policy_highlights.map((item, i) => (
                <div key={i} className="community-guideline-item">
                  <CheckCircleIcon size={16} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Events Calendar */}
          {events.length > 0 ? (
            <div className="community-widget">
              <div className="community-widget__head">
                <h3>Lịch sự kiện cộng đồng</h3>
                <button type="button" className="community-widget__link">Xem tất cả sự kiện</button>
              </div>
              <div className="community-events-list">
                {events.map((evt) => (
                  <div key={evt.event_id} className="community-event-row">
                    <div>
                      <strong>{evt.title}</strong>
                      <span>{evt.schedule}</span>
                    </div>
                    <button type="button" className="community-btn community-btn--sm community-btn--primary">{evt.cta_label}</button>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* Saved Discussions */}
          {savedDiscussions.length > 0 ? (
            <div className="community-widget">
              <div className="community-widget__head">
                <h3>Saved Discussions</h3>
                <button type="button" className="community-widget__link">Xem tất cả</button>
              </div>
              <div className="community-saved-list">
                {savedDiscussions.map((d) => (
                  <div key={d.discussion_id} className="community-saved-item">
                    <BookmarkIcon size={16} className="community-saved-item__icon" />
                    <div className="community-saved-item__content">
                      <strong>{d.title}</strong>
                      <span>{d.snippet}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* ===== Topic Cards (Bottom) ===== */}
      <div className="community-topic-section">
        <div className="community-topic-section__head">
          <h2>Thảo luận theo chủ đề</h2>
          <button type="button" className="community-widget__link">Xem tất cả chủ đề</button>
        </div>
        <div className="community-topic-cards">
          {TOPIC_ICONS.map((topic) => (
            <div key={topic.key} className="community-topic-card">
              <div className="community-topic-card__icon"><topic.Icon size={20} /></div>
              <strong>{topic.label}</strong>
              <span>{topic.sub}</span>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{topic.posts}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function draftKey(postId, parentCommentId = '') {
  return `${postId}:${parentCommentId || 'root'}`
}
