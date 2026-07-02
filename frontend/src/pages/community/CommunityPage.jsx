import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

import {
  createCommunityComment,
  createCommunityPost,
  fetchCommunityHome,
  fetchCommunityPosts,
  joinCommunitySpace,
} from '../../modules/community'
import {
  UsersIcon, MessageSquareIcon, ThumbsUpIcon, BookmarkIcon, ShareIcon,
  TrophyIcon, HashIcon, ImageIcon, SearchIcon, EditIcon,
  ShieldIcon, TargetIcon, BarChartIcon, FlagIcon, GlobeIcon, CheckCircleIcon,
  StarIcon, ScaleIcon, FileTextIcon, PieChartIcon,
} from '../../shared/Icons'

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
  { key: 'planning-personal-finance', label: 'Personal Finance Planning', sub: 'Quỹ tài chính cá nhân, kế hoạch', posts: '4.7K bài viết', Icon: TargetIcon },
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

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1
    }
  }
}

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15
    }
  }
}

export default function CommunityPage({
  sessionId,
  initialSpaceId = '',
  onBack,
  onOpenLearning,
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

  if (!sessionId) return <p className="p-8 text-sm text-slate-500 dark:text-zinc-400">Chưa có session onboarding.</p>
  if (loading) return <p className="p-8 text-sm text-slate-500 dark:text-zinc-400">Đang tải Community...</p>
  if (error && !home) return <p className="p-4 m-4 bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 rounded-xl border border-red-200 dark:border-red-900/30 text-sm">{error}</p>
  if (!home) return <p className="p-8 text-sm text-slate-500 dark:text-zinc-400">Chưa có dữ liệu Community.</p>

  const stats = home.stats || {}
  const topContributors = home.top_contributors || []
  const trendingTopics = home.trending_topics || []
  const events = home.community_events || []
  const savedDiscussions = home.saved_discussions || []
  const selectedSpace = home.spaces.find((s) => s.space_id === selectedSpaceId) || null

  return (
    <motion.section
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="w-full min-h-[100dvh] bg-transparent text-slate-900 dark:text-zinc-100 font-sans transition-colors duration-300 py-6 md:py-8"
    >
      <div className="max-w-[1720px] mx-auto w-full flex flex-col gap-8 px-6 md:px-10">
      {error ? (
        <div className="p-4 bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 rounded-xl border border-red-200 dark:border-red-900/30 text-sm">
          {error}
        </div>
      ) : null}

      {/* ===== HERO ===== */}
      <motion.div
        variants={cardVariants}
        className="relative overflow-hidden grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-8 p-6 md:p-10 rounded-3xl bg-gradient-to-br from-zinc-900 via-zinc-950 to-emerald-950 text-slate-100 shadow-xl border border-zinc-800"
      >
        <div className="flex flex-col gap-4 z-10">
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white font-sans">
            Community
          </h1>
          <p className="text-sm md:text-base text-zinc-300 leading-relaxed max-w-2xl">
            Nơi nhà đầu tư và người học cùng chia sẻ, thảo luận, đặt câu hỏi và nghiên cứu một cách có trách nhiệm. Giáo dục là trọng tâm – nơi không có pump & dump, tín hiệu mù quáng.
          </p>
          <div className="flex flex-wrap gap-2.5 mt-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-white/10 bg-white/5 text-zinc-200">
              <ShieldIcon size={13} className="text-teal-400" /> Moderated
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-white/10 bg-white/5 text-zinc-200">
              <FileTextIcon size={13} className="text-teal-400" /> Research-first
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-white/10 bg-white/5 text-zinc-200">
              <CheckCircleIcon size={13} className="text-teal-400" /> No buy/sell guarantee
            </span>
          </div>
          <div className="flex flex-wrap gap-3 mt-6">
            <button
              type="button"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full font-semibold text-sm cursor-pointer transition-all duration-200 bg-teal-500 hover:bg-teal-600 text-white shadow-lg shadow-teal-500/20 active:scale-95"
              onClick={() => document.getElementById('community-composer')?.focus()}
            >
              <EditIcon size={15} /> Tạo bài viết
            </button>
            <button type="button" className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full font-semibold text-sm cursor-pointer transition-all duration-200 bg-white/5 hover:bg-white/10 border border-white/20 text-white active:scale-95">
              <SearchIcon size={15} /> Khám phá chủ đề
            </button>
            <button type="button" className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full font-semibold text-sm cursor-pointer transition-all duration-200 bg-white/5 hover:bg-white/10 border border-white/20 text-white active:scale-95">
              <UsersIcon size={15} /> Hỏi cộng đồng
            </button>
          </div>
        </div>

        <div className="z-10 p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex flex-col gap-4 justify-between">
          <h3 className="text-sm font-bold text-zinc-200 uppercase tracking-wider">Cộng đồng Northstar</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-0.5">
              <span className="text-[11px] text-zinc-400 font-medium">Thành viên</span>
              <span className="text-xl font-bold text-white leading-tight">{stats.active_members || '36.2K'}</span>
              <span className="text-[10px] text-emerald-400 font-semibold">{stats.active_members_delta || ''}</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-[11px] text-zinc-400 font-medium">Thảo luận hôm nay</span>
              <span className="text-xl font-bold text-white leading-tight">{stats.discussions_today || 0}</span>
              <span className="text-[10px] text-emerald-400 font-semibold">{stats.discussions_delta || ''}</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-[11px] text-zinc-400 font-medium">Tương tác</span>
              <span className="text-xl font-bold text-white leading-tight">68%</span>
              <span className="text-[10px] text-emerald-400 font-semibold">↑ 5.1%</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-[11px] text-zinc-400 font-medium">Moderation</span>
              <span className="text-xl font-bold text-white leading-tight">{stats.moderation_status || 'Ổn định'}</span>
              <span className="text-[10px] text-zinc-400">{stats.moderation_note || ''}</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ===== STATS BAR ===== */}
      <motion.div
        variants={cardVariants}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4"
      >
        <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex items-center gap-4 hover:shadow-md transition-all duration-300">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-teal-50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 shrink-0">
            <UsersIcon size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider">Hoạt động</p>
            <strong className="block text-xl font-extrabold text-slate-900 dark:text-white leading-none mt-1">{stats.active_members || '36.2K'}</strong>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">{stats.active_members_delta || ''}</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex items-center gap-4 hover:shadow-md transition-all duration-300">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-teal-50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 shrink-0">
            <MessageSquareIcon size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider">Hôm nay</p>
            <strong className="block text-xl font-extrabold text-slate-900 dark:text-white leading-none mt-1">{stats.discussions_today || 0}</strong>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">{stats.discussions_delta || ''}</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex items-center gap-4 hover:shadow-md transition-all duration-300">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-teal-50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 shrink-0">
            <BarChartIcon size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider">Watchlists</p>
            <strong className="block text-xl font-extrabold text-slate-900 dark:text-white leading-none mt-1">{stats.watchlists_shared || '1.25K'}</strong>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">{stats.watchlists_delta || ''}</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex items-center gap-4 hover:shadow-md transition-all duration-300">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-teal-50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 shrink-0">
            <CheckCircleIcon size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider">Đã giải đáp</p>
            <strong className="block text-xl font-extrabold text-slate-900 dark:text-white leading-none mt-1">{stats.questions_answered || 0}</strong>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">{stats.questions_delta || ''}</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex items-center gap-4 hover:shadow-md transition-all duration-300">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-emerald-50 dark:bg-emerald-950/20 text-emerald-650 dark:text-emerald-400 shrink-0">
            <ShieldIcon size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider">Kiểm duyệt</p>
            <strong className="block text-xl font-extrabold text-slate-900 dark:text-white leading-none mt-1">{stats.moderation_status || 'Ổn định'}</strong>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">{stats.moderation_note || ''}</span>
          </div>
        </div>
      </motion.div>

      {/* ===== MAIN (Feed + Sidebar) ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6 items-start">
        {/* --- Feed Column --- */}
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Bảng tin cộng đồng</h2>
            <div className="flex p-0.5 bg-slate-100 dark:bg-zinc-850 rounded-full border border-slate-200 dark:border-zinc-800/80">
              {FEED_TABS.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`px-4 py-1.5 rounded-full text-xs font-semibold cursor-pointer transition-all duration-200 ${
                    activeTab === tab
                      ? 'bg-white dark:bg-zinc-800 text-slate-900 dark:text-white shadow-sm'
                      : 'text-slate-500 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white'
                  }`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {/* Post Composer */}
          <motion.div
            variants={cardVariants}
            className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center text-white font-bold text-sm shrink-0 shadow-inner">
                NP
              </div>
              <input
                id="community-composer"
                className="flex-1 px-4 py-2.5 rounded-full border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 text-slate-800 dark:text-zinc-200 text-sm outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all duration-200"
                placeholder="Bạn muốn chia sẻ điều gì?"
                value={form.body}
                onChange={(e) => setForm((c) => ({ ...c, body: e.target.value }))}
              />
              <button
                type="button"
                className="px-4.5 py-2 rounded-full text-xs font-semibold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer transition-all duration-200 shadow-md shadow-teal-500/10 active:scale-95"
                onClick={handlePost}
              >
                Đăng bài
              </button>
            </div>
            <div className="flex gap-2 pl-14">
              <button type="button" className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-slate-650 dark:text-zinc-400 bg-slate-50 dark:bg-zinc-850/50 border border-slate-200 dark:border-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors duration-200 cursor-pointer">
                <ImageIcon size={13} className="text-slate-500 dark:text-zinc-400" /> Ảnh
              </button>
              <button type="button" className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-slate-650 dark:text-zinc-400 bg-slate-50 dark:bg-zinc-850/50 border border-slate-200 dark:border-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors duration-200 cursor-pointer">
                <BarChartIcon size={13} className="text-slate-500 dark:text-zinc-400" /> Poll
              </button>
              <button type="button" className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-slate-650 dark:text-zinc-400 bg-slate-50 dark:bg-zinc-850/50 border border-slate-200 dark:border-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors duration-200 cursor-pointer">
                <HashIcon size={13} className="text-slate-500 dark:text-zinc-400" /> Gắn mã (ticker)
              </button>
            </div>
          </motion.div>

          {/* Submit Result */}
          <AnimatePresence>
            {submitResult && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="p-4 rounded-xl border border-teal-200 dark:border-teal-900 bg-teal-50 dark:bg-teal-950/20 text-sm flex flex-col gap-1"
              >
                <strong className="text-teal-700 dark:text-teal-400">Kết quả moderation: {submitResult.moderation_status}</strong>
                {submitResult.moderation_message ? <p className="text-slate-600 dark:text-zinc-400 text-xs">{submitResult.moderation_message}</p> : null}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Demo Posts */}
          {DEMO_POSTS.map((post) => (
            <motion.article
              key={post.id}
              variants={cardVariants}
              className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4 hover:shadow-md hover:border-slate-300 dark:hover:border-zinc-700 transition-all duration-300"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-sm">
                  {post.author[0]}
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">
                    {post.author} <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 ml-1.5 border border-emerald-100 dark:border-emerald-900/30">{post.badge}</span>
                  </span>
                  <small className="text-xs text-slate-400 dark:text-zinc-500">{post.time}</small>
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <h3 className="text-base font-bold text-slate-950 dark:text-white leading-snug">{post.title}</h3>
                <p className="text-sm text-slate-600 dark:text-zinc-300 leading-relaxed">{post.body}</p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {post.tags.map((t) => (
                  <span key={t} className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-50 dark:bg-zinc-850/50 border border-slate-200 dark:border-zinc-800 text-slate-600 dark:text-zinc-400">{t}</span>
                ))}
              </div>
              <div className="flex items-center gap-6 pt-3 border-t border-slate-100 dark:border-zinc-800">
                <button type="button" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white transition-colors cursor-pointer"><ThumbsUpIcon size={14} /> {post.votes}</button>
                <button type="button" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white transition-colors cursor-pointer"><MessageSquareIcon size={14} /> {post.comments}</button>
                <button type="button" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white transition-colors cursor-pointer"><ShareIcon size={14} /> {post.shares}</button>
                <span className="flex-1" />
                <button type="button" className="text-xs font-semibold text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 cursor-pointer">Tham gia thảo luận</button>
              </div>
            </motion.article>
          ))}

          {/* Real Posts from API */}
          {posts.map((post) => (
            <motion.article
              key={post.post_id}
              variants={cardVariants}
              className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4 hover:shadow-md hover:border-slate-300 dark:hover:border-zinc-700 transition-all duration-300"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal-400 to-cyan-505 flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-sm">
                  {(post.user_id || 'U')[0].toUpperCase()}
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">{post.user_id}</span>
                  <small className="text-xs text-slate-400 dark:text-zinc-500">
                    {post.moderation_status} · {new Date(post.created_at).toLocaleDateString('vi-VN')}
                  </small>
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <h3 className="text-base font-bold text-slate-950 dark:text-white leading-snug">{post.title}</h3>
                <p className="text-sm text-slate-650 dark:text-zinc-350 leading-relaxed">{post.body}</p>
              </div>
              {selectedSpace?.is_joined && (
                <div className="flex gap-2 mt-2">
                  <input
                    className="flex-1 px-4 py-2.5 rounded-full border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 text-slate-800 dark:text-zinc-200 text-sm outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all duration-200"
                    value={commentDrafts[draftKey(post.post_id)] || ''}
                    onChange={(e) => setCommentDrafts((c) => ({ ...c, [draftKey(post.post_id)]: e.target.value }))}
                    placeholder="Bình luận..."
                  />
                  <button
                    type="button"
                    className="px-4.5 py-2.5 rounded-full text-xs font-semibold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer transition-all duration-200 active:scale-95"
                    onClick={() => handleComment(post.post_id)}
                  >
                    Gửi
                  </button>
                </div>
              )}
              {post.comments?.length ? (
                <div className="pl-4 mt-2 border-l-2 border-slate-100 dark:border-zinc-800 flex flex-col gap-2">
                  {post.comments.map((c) => (
                    <div key={c.comment_id} className="py-2 text-xs text-slate-600 dark:text-zinc-400">
                      <strong className="text-slate-900 dark:text-white mr-1.5">{c.user_id}</strong>
                      <span>{c.body}</span>
                    </div>
                  ))}
                </div>
              ) : null}
            </motion.article>
          ))}
        </div>

        {/* --- Sidebar --- */}
        <div className="flex flex-col gap-6">
          {/* Trending Topics */}
          <motion.div
            variants={cardVariants}
            className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4"
          >
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Chủ đề nổi bật</h3>
              <button type="button" className="text-xs font-semibold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer border-none bg-none p-0">Xem tất cả</button>
            </div>
            <div className="flex flex-wrap gap-2">
              {trendingTopics.map((t) => (
                <span key={t.topic_id} className="px-3 py-1.5 rounded-full text-xs font-semibold bg-teal-50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/30 text-teal-600 dark:text-teal-400 hover:bg-teal-100 dark:hover:bg-teal-950/30 transition-all duration-200 cursor-pointer">
                  {t.label}
                </span>
              ))}
            </div>
          </motion.div>

          {/* Groups / Clubs */}
          <motion.div
            variants={cardVariants}
            className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4"
          >
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Nhóm có thể quan tâm</h3>
              <button type="button" className="text-xs font-semibold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer border-none bg-none p-0">Xem tất cả</button>
            </div>
            <div className="flex flex-col gap-3">
              {home.spaces.slice(0, 4).map((space) => {
                const Icon = SPACE_ICONS[space.icon_key] || UsersIcon
                return (
                  <div
                    key={space.space_id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-100 dark:border-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-850/80 transition-colors duration-200 cursor-pointer"
                    onClick={() => setSelectedSpaceId(space.space_id)}
                  >
                    <div className="w-9 h-9 rounded-lg bg-teal-50 dark:bg-teal-950/30 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0 border border-teal-100 dark:border-teal-900/20">
                      <Icon size={17} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <strong className="block text-sm font-semibold text-slate-900 dark:text-white truncate">{space.title}</strong>
                      <span className="text-xs text-slate-550 dark:text-zinc-400">{(space.member_count / 1000).toFixed(1)}K thành viên</span>
                    </div>
                    {!space.is_joined && (
                      <button
                        type="button"
                        className="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer ml-auto"
                        onClick={(e) => { e.stopPropagation(); handleJoin(space.space_id) }}
                      >
                        Tham gia
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          </motion.div>

          {/* Leaderboard */}
          <motion.div
            variants={cardVariants}
            className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4"
          >
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Thành viên tích cực</h3>
              <button type="button" className="text-xs font-semibold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer border-none bg-none p-0">Bảng đầy đủ</button>
            </div>
            <div className="flex flex-col gap-3.5">
              {topContributors.map((c) => (
                <div key={c.rank} className="flex items-center gap-3">
                  <div className={`w-6 h-6 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 ${
                    c.rank === 1 ? 'bg-amber-100 text-amber-700' :
                    c.rank === 2 ? 'bg-slate-200 text-slate-700' :
                    c.rank === 3 ? 'bg-orange-100 text-orange-700' : 'bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400'
                  }`}>
                    {c.rank}
                  </div>
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-sm">
                    {c.display_name[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <strong className="block text-xs font-semibold text-slate-900 dark:text-white truncate">{c.display_name}</strong>
                    <span className="text-[10px] text-slate-500 dark:text-zinc-450">{c.role_badge}</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1 shrink-0">
                    <StarIcon size={12} className="text-amber-500 fill-amber-500" /> {c.points.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Guidelines */}
          <motion.div
            variants={cardVariants}
            className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4"
          >
            <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Guidelines</h3>
            <div className="flex flex-col gap-3">
              {home.policy_highlights.map((item, i) => (
                <div key={i} className="flex items-start gap-2.5 text-xs text-slate-600 dark:text-zinc-350 leading-normal">
                  <CheckCircleIcon size={14} className="text-emerald-500 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Events Calendar */}
          {events.length > 0 && (
            <motion.div
              variants={cardVariants}
              className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4"
            >
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Lịch sự kiện</h3>
                <button type="button" className="text-xs font-semibold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer border-none bg-none p-0">Tất cả</button>
              </div>
              <div className="flex flex-col gap-3">
                {events.map((evt) => (
                  <div key={evt.event_id} className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-100 dark:border-zinc-800">
                    <div className="min-w-0">
                      <strong className="block text-xs font-bold text-slate-900 dark:text-white truncate">{evt.title}</strong>
                      <span className="text-[10px] text-slate-500 dark:text-zinc-450">{evt.schedule}</span>
                    </div>
                    <button type="button" className="px-3 py-1.5 rounded-full text-[10px] font-bold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer transition-colors shrink-0">
                      {evt.cta_label}
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Saved Discussions */}
          {savedDiscussions.length > 0 && (
            <motion.div
              variants={cardVariants}
              className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4"
            >
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Đã lưu</h3>
                <button type="button" className="text-xs font-semibold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer border-none bg-none p-0">Tất cả</button>
              </div>
              <div className="flex flex-col gap-3.5">
                {savedDiscussions.map((d) => (
                  <div key={d.discussion_id} className="flex items-start gap-3 pb-3 border-b border-slate-100 dark:border-zinc-800 last:border-none last:pb-0">
                    <BookmarkIcon size={14} className="text-teal-600 shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <strong className="block text-xs font-semibold text-slate-950 dark:text-white truncate">{d.title}</strong>
                      <span className="block text-[11px] text-slate-500 dark:text-zinc-400 truncate">{d.snippet}</span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* ===== Topic Cards (Bottom) ===== */}
      <motion.div
        variants={cardVariants}
        className="flex flex-col gap-4 mt-4"
      >
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Thảo luận theo chủ đề</h2>
          <button type="button" className="text-xs font-semibold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer border-none bg-none p-0">Tất cả chủ đề</button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {TOPIC_ICONS.map((topic) => (
            <div
              key={topic.key}
              className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-2 hover:shadow-md hover:-translate-y-0.5 border-t-4 border-t-teal-500 transition-all duration-300"
            >
              <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0 mb-1 border border-teal-100 dark:border-teal-900/20">
                <topic.Icon size={18} />
              </div>
              <strong className="text-xs font-bold text-slate-900 dark:text-white">{topic.label}</strong>
              <span className="text-[10px] text-slate-500 dark:text-zinc-405 leading-snug">{topic.sub}</span>
              <span className="text-[9px] text-slate-400 dark:text-zinc-500 mt-1 font-semibold">{topic.posts}</span>
            </div>
          ))}
        </div>
      </motion.div>
      </div>
    </motion.section>
  )
}

function draftKey(postId, parentCommentId = '') {
  return `${postId}:${parentCommentId || 'root'}`
}
