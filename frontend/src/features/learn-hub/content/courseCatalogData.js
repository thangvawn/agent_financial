/**
 * Learn Hub catalog barrel: courses (YouTube) + books (Archive.org).
 */

import { DEMO_COURSES } from './demoCourses'

export { COURSE_CATEGORIES, DEMO_COURSES } from './demoCourses'
export { DEMO_BOOKS } from './demoBooks'

export function findCourseById(courseId) {
  return DEMO_COURSES.find((c) => c.course_id === courseId) || null
}

export function getAllLessons(course) {
  if (!course) return []
  return course.sections.flatMap((s) => s.lessons)
}

export function findLessonIndex(course, lessonId) {
  return getAllLessons(course).findIndex((l) => l.lesson_id === lessonId)
}

const DIFFICULTY_ORDER = { 'Cơ bản': 0, 'Trung bình': 1, 'Nâng cao': 2 }

export function filterCourses(courses, { category, search }) {
  let result = courses
  if (category && category !== 'all') result = result.filter((c) => c.category === category)
  if (search?.trim()) {
    const q = search.toLowerCase().trim()
    result = result.filter((c) => `${c.title} ${c.description} ${c.instructor} ${c.category}`.toLowerCase().includes(q))
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
