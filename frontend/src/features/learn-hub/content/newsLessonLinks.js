import { DEMO_COURSES } from './demoCourses'

const CONCEPT_LESSONS = {
  risk_on_off: ['macro-401', 'macro-l4'],
  fx_impact: ['macro-401', 'macro-l1'],
  rate_equity: ['macro-401', 'macro-l3'],
  oil_inflation: ['macro-401', 'macro-l2'],
  cpi_explained: ['macro-401', 'macro-l2'],
  bond_yield: ['bond-601', 'bond-l3'],
  crypto_liquidity: ['fintech-801', 'fintech-l1'],
  earnings_reading: ['bctc-301', 'bctc-l1'],
  geopolitics_market: ['quant-501', 'quant-l1'],
}

function target(courseId, lessonId) {
  const course = DEMO_COURSES.find(item => item.course_id === courseId)
  const lesson = course?.sections.flatMap(section => section.lessons).find(item => item.lesson_id === lessonId)
  return course && lesson ? { course, lesson } : null
}

export function newsLessonLink(conceptId) {
  const ids = CONCEPT_LESSONS[conceptId]
  const result = ids ? target(...ids) : null
  if (!result) return null
  const base = (import.meta.env?.BASE_URL || '/dashboard-static/').replace(/\/$/, '')
  const query = new URLSearchParams({ course: result.course.course_id, lesson: result.lesson.lesson_id })
  return { ...result, url: `${base}/learn?${query}`, label: result.lesson.title }
}

export function resolveLearningTarget(search) {
  const params = new URLSearchParams(search)
  if (params.has('course') || params.has('lesson')) return target(params.get('course'), params.get('lesson'))
  return newsLessonLink(params.get('concept'))
}
