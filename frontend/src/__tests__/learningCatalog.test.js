import { describe, it } from 'node:test'
import assert from 'node:assert/strict'

import { DEMO_COURSES } from '../features/learn-hub/content/demoCourses.js'

describe('Learn Hub fallback catalog', () => {
  it('keeps the displayed lesson count aligned with the rendered lessons', () => {
    for (const course of DEMO_COURSES) {
      const lessonCount = (course.sections || []).reduce(
        (total, section) => total + (section.lessons || []).length,
        0,
      )
      assert.equal(
        course.lesson_count,
        lessonCount,
        `${course.course_id} lesson_count must match its fallback lessons`,
      )
    }
  })

  it('keeps the BCTC course discoverable by the financial-statement practice lab', () => {
    const course = DEMO_COURSES.find((item) => item.course_id === 'bctc-301')
    assert.ok(course, 'BCTC course must remain in the fallback catalog')
    assert.equal(course.category, 'analysis')
    assert.match(course.description, /tư duy tài chính/i)
  })
})
