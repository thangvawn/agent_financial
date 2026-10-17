import { QUANTA_SECTIONS } from './quantaCurriculumData.js'
import { QUANTA_LESSONS_PART1 } from './quantaLessonData1.js'
import { QUANTA_LESSONS_PART2 } from './quantaLessonData2.js'
import { QUANTA_RECIPES_DATA } from './quantaRecipesData.js'

const ALL_LESSON_DETAILS = {
  ...QUANTA_LESSONS_PART1,
  ...QUANTA_LESSONS_PART2,
  ...QUANTA_RECIPES_DATA,
}

export function getQuantaLessonDetail(slug) {
  for (const sec of QUANTA_SECTIONS) {
    for (const l of sec.lessons) {
      if (l.slug === slug || l.id === slug) {
        const detail = ALL_LESSON_DETAILS[l.slug] || ALL_LESSON_DETAILS[l.id] || {}
        return {
          ...l,
          sectionId: sec.id,
          sectionTitle: sec.title,
          checklist: detail.checklist || [],
          demo_code: detail.demo_code || null,
          body: detail.body || l.subtitle,
        }
      }
    }
  }
  return null
}

export function getAdjacentLessons(currentSlug) {
  const flattened = []
  for (const sec of QUANTA_SECTIONS) {
    for (const l of sec.lessons) {
      flattened.push({ slug: l.slug, title: l.title })
    }
  }
  const idx = flattened.findIndex((item) => item.slug === currentSlug)
  if (idx === -1) return { prev: null, next: null }
  return {
    prev: idx > 0 ? flattened[idx - 1] : null,
    next: idx < flattened.length - 1 ? flattened[idx + 1] : null,
  }
}
