export const financialHealthResponseShape = {
  session_id: 'string',
  health_score: 'number',
  score_band: 'string',
  guided_investing_eligible: 'boolean',
  subscores: 'array',
  flags: 'array',
  actions: 'array',
  educational_links: 'array',
  transparency_note: 'string',
  compliance_note: 'string',
}
