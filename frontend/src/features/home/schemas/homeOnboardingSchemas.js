export const onboardingCompleteShape = {
  session_id: 'string',
  persona_segment: 'string',
  primary_route: 'string',
  guided_investing_eligible: 'boolean',
  pro_eligible: 'boolean',
  trust_message: 'string',
  next_best_action_type: 'string',
  next_best_action_ref: 'string',
}

export const homeResponseShape = {
  session_id: 'string',
  persona_segment: 'string',
  primary_route: 'string',
  next_best_action_type: 'string',
  next_best_action_ref: 'string',
  trust_message: 'string',
  blocks: 'array',
}
