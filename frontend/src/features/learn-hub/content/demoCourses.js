/** Learn Hub course catalog — Curated thematic masterclasses (IDs verified live). */
import { FOUNDATION_COURSES } from './demoCoursesFoundation.js'
import { APPLIED_COURSES } from './demoCoursesApplied.js'

export const COURSE_CATEGORIES = [
  { id: 'all', label: 'Tất cả' },
  { id: 'finance', label: 'Tài chính cơ bản' },
  { id: 'investing', label: 'Đầu tư' },
  { id: 'analysis', label: 'Phân tích' },
  { id: 'tools', label: 'Công cụ' },
]

export const DEMO_COURSES = [...FOUNDATION_COURSES, ...APPLIED_COURSES]
