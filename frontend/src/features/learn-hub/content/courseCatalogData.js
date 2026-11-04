import { resolveBookSource } from '../pages/bookSource.js'
/**
 * Learn Hub catalog barrel: courses (YouTube) + books (Archive.org).
 */

import { DEMO_COURSES } from './demoCourses.js'

export { COURSE_CATEGORIES, DEMO_COURSES } from './demoCourses.js'
export { DEMO_BOOKS } from './demoBooks.js'

export function findCourseById(courseId, catalog = DEMO_COURSES) {
  return catalog.find((c) => c.course_id === courseId) || null
}

export function getAllLessons(course) {
  if (!course) return []
  return (course.sections || []).flatMap((s) => s.lessons || [])
}

export function findLessonIndex(course, lessonId) {
  return getAllLessons(course).findIndex((l) => l.lesson_id === lessonId)
}

const DIFFICULTY_ORDER = { 'Cơ bản': 0, 'Trung bình': 1, 'Nâng cao': 2 }

export function filterCourses(courses, { category, search, difficulty }) {
  // Never sort the catalog passed by the caller in place.  The same fallback
  // catalog is used to calculate progress and render cards, so mutating it
  // here can make UI order depend on which filter was opened first.
  let result = [...(courses || [])]
  if (category && category !== 'all') result = result.filter((c) => c.category === category)
  if (difficulty && difficulty !== 'all') result = result.filter((c) => c.difficulty === difficulty)
  if (search?.trim()) {
    const q = search.toLowerCase().trim()
    result = result.filter((c) => `${c.title} ${c.description} ${c.instructor} ${c.category} ${c.difficulty}`.toLowerCase().includes(q))
  }
  return result.sort((a, b) => (DIFFICULTY_ORDER[a.difficulty] ?? 9) - (DIFFICULTY_ORDER[b.difficulty] ?? 9))
}

export function isYouTubeUrl(url) {
  return /youtube\.com|youtu\.be/i.test(String(url || ''))
}

export function toYouTubeEmbed(url) {
  const match = String(url || '').match(/(?:v=|youtu\.be\/)([\w-]{6,})/)
  return match ? `https://www.youtube.com/embed/${match[1]}?rel=0` : ''
}

const DIFFICULTY_MAP = {
  beginner: 'Cơ bản',
  intermediate: 'Trung bình',
  advanced: 'Nâng cao',
  'Cơ bản': 'Cơ bản',
  'Trung bình': 'Trung bình',
  'Nâng cao': 'Nâng cao',
}

const TOPIC_CATEGORY_MAP = {
  macroeconomics: 'analysis',
  inflation: 'analysis',
  financial_statements: 'analysis',
  banking_products: 'finance',
  saving: 'finance',
  valuation: 'investing',
  stocks: 'investing',
  vietnam_market: 'investing',
  technical_analysis: 'investing',
  quantitative_finance: 'tools',
  portfolio_theory: 'tools',
  risk_management: 'tools',
  derivatives: 'tools',
}

export function normalizeDbCourse(row) {
  if (!row) return null
  let durationHours = row.total_duration
  if (row.duration_minutes) {
    if (row.duration_minutes < 60) {
      durationHours = `${row.duration_minutes} phút`
    } else {
      const h = (row.duration_minutes / 60).toFixed(1).replace('.0', '')
      durationHours = `${h} giờ`
    }
  } else if (!durationHours) {
    durationHours = '1,5 giờ'
  }

  const difficulty = DIFFICULTY_MAP[row.level] || DIFFICULTY_MAP[row.difficulty] || 'Cơ bản'
  const instructor = row.instructor || row.provider || 'Giảng viên chuyên môn'
  const provider = row.provider || 'Northstar Academy'
  const thumbnail = row.thumbnail_url || row.thumbnail_image || 'https://img.youtube.com/vi/PHe0bXAIuk0/hqdefault.jpg'

  let videoId = null
  const ytMatch = String(row.url || '').match(/(?:v=|youtu\.be\/)([\w-]{6,})/)
  const thumbMatch = String(thumbnail || '').match(/vi\/([\w-]{6,})\//)
  if (ytMatch) videoId = ytMatch[1]
  else if (thumbMatch) videoId = thumbMatch[1]
  else videoId = 'PHe0bXAIuk0'

  let parsedSections = null
  if (Array.isArray(row.sections) && row.sections.length > 0) {
    parsedSections = row.sections
  } else if (row.sections_json) {
    try {
      const p = typeof row.sections_json === 'string' ? JSON.parse(row.sections_json) : row.sections_json
      if (Array.isArray(p) && p.length > 0) parsedSections = p
    } catch {
      parsedSections = null
    }
  }

  const sections = parsedSections || [
    {
      section_id: `${row.course_id}-s1`,
      title: 'Nội dung bài giảng & Giáo trình',
      lessons: [
        {
          lesson_id: `${row.course_id}-l1`,
          title: `${row.title} - Bài giảng chính`,
          duration: `${Math.min(45, Math.round((row.duration_minutes || 45) / 5))} phút`,
          video_url: row.url || `https://www.youtube.com/watch?v=${videoId}`,
          video_id: videoId,
        },
      ],
    },
  ]

  let topicsList = []
  if (Array.isArray(row.topics)) {
    topicsList = row.topics
  } else if (row.topics_json) {
    try {
      topicsList = typeof row.topics_json === 'string' ? JSON.parse(row.topics_json) : row.topics_json
    } catch {
      topicsList = []
    }
  }

  const primaryTopic = topicsList[0]
  const mappedCategory = (primaryTopic && TOPIC_CATEGORY_MAP[primaryTopic]) || row.category || 'finance'

  return {
    ...row,
    instructor,
    provider,
    difficulty,
    category: mappedCategory,
    total_duration: durationHours,
    lesson_count: sections.reduce((acc, s) => acc + (s.lessons?.length || 0), 0),
    thumbnail_image: thumbnail,
    sections,
  }
}

export function normalizeDbBook(row) {
  if (!row) return null
  const source = resolveBookSource(row)
  return {
    ...row,
    book_id: row.book_id || row.asset_id || source.sourceUrl,
    title: row.title || 'Tài liệu',
    original_title: row.title,
    author: row.author || 'Chưa có thông tin tác giả',
    language: row.language || '',
    category: (row.topics && row.topics[0]) || 'finance',
    pages: row.pages || null,
    read_time: row.read_time || '',
    rating: row.rating || null,
    cover_image: row.cover_url || row.cover_image || '',
    cover_color: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    summary: row.description || row.summary || 'Chưa có mô tả từ nguồn.',
    url: row.url || source.openUrl,
    download_url: row.download_url || '',
    pdf_url: source.kind === 'pdf' ? source.sourceUrl : '',
    file_name: source.sourceUrl.split('/').pop() || '',
    key_takeaways: row.key_takeaways || [row.description || row.summary].filter(Boolean),
  }
}
