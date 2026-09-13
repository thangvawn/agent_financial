/**
 * Northstar Learning Hub Type Definitions & Runtime Contracts
 * Strictly enforces Zero-Leakage security on learning checkpoints.
 */

/**
 * @typedef {Object} CheckpointItem
 * @property {string} [schema_version]
 * @property {string} checkpoint_id
 * @property {string} lesson_id
 * @property {string} prompt
 * @property {string[]} options
 * @property {string} expires_at
 * @property {{ focus_concept?: string, hint?: string }} [socratic_coaching]
 */
export const CheckpointItem = Object.freeze({
  schema_version: '1.0.0',
  checkpoint_id: '',
  lesson_id: '',
  prompt: '',
  options: [],
  expires_at: '',
})

/**
 * @typedef {Object} GradeRequest
 * @property {string} [schema_version]
 * @property {string} checkpoint_id
 * @property {string} response
 */
export const GradeRequest = Object.freeze({
  schema_version: '1.0.0',
  checkpoint_id: '',
  response: '',
})

/**
 * @typedef {Object} GradeResponse
 * @property {string} [schema_version]
 * @property {string} checkpoint_id
 * @property {string} lesson_id
 * @property {boolean} passed
 * @property {number} score
 * @property {string[]} rubric_evidence
 * @property {string[]} misconceptions
 * @property {string} verified_event_id
 */
export const GradeResponse = Object.freeze({
  schema_version: '1.0.0',
  checkpoint_id: '',
  lesson_id: '',
  passed: false,
  score: 0,
  rubric_evidence: [],
  misconceptions: [],
  verified_event_id: '',
})

/**
 * @typedef {Object} CompleteRequest
 * @property {string} [schema_version]
 * @property {string} verified_event_id
 * @property {string} idempotency_key
 * @property {string} [confirmation_id]
 */
export const CompleteRequest = Object.freeze({
  schema_version: '1.0.0',
  verified_event_id: '',
  idempotency_key: '',
  confirmation_id: '',
})

/**
 * @typedef {Object} CompleteResponse
 * @property {string} [schema_version]
 * @property {string} receipt_id
 * @property {string} lesson_id
 * @property {string} status
 * @property {number|null} [quiz_score]
 * @property {string} updated_at
 */
export const CompleteResponse = Object.freeze({
  schema_version: '1.0.0',
  receipt_id: '',
  lesson_id: '',
  status: 'completed',
  quiz_score: null,
  updated_at: '',
})

export const FORBIDDEN_LEAKAGE_KEYS = Object.freeze([
  'correct_answer',
  'answer_key',
  'solution',
  'correctAnswer',
])

/**
 * Validates that a received checkpoint payload strictly satisfies Zero-Leakage
 * and contains no sensitive answer keys.
 * @param {Record<string, unknown>} item
 * @returns {boolean}
 */
export function validateZeroLeakage(item) {
  if (!item || typeof item !== 'object') return false
  return !FORBIDDEN_LEAKAGE_KEYS.some((key) => key in item)
}

/**
 * Validates runtime checkpoint item against the contract.
 * @param {Record<string, unknown>} item
 * @returns {boolean}
 */
export function validateCheckpointItem(item) {
  if (!item || typeof item !== 'object') return false
  if (!validateZeroLeakage(item)) return false
  const required = ['checkpoint_id', 'lesson_id', 'prompt', 'options', 'expires_at']
  return required.every((field) => field in item && item[field] !== undefined)
}
