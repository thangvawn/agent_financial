import './checkpoint.css'

const OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

export default function CheckpointCard({
  checkpointId,
  lessonId,
  prompt,
  options = [],
  expiresAt = null,
  selectedOption = null,
  onSelectOption,
  onSubmit,
  onRequestHint,
  isSubmitting = false,
  disabled = false,
  gradeResult = null,
  // Explicitly ignore any accidental leakage props
  correct_answer: _ca,
  correctAnswer: _ca2,
  ...restProps
}) {
  void expiresAt
  void _ca
  void _ca2
  const isSubmitDisabled = !selectedOption || isSubmitting || disabled

  const handleSubmit = (e) => {
    e?.preventDefault?.()
    if (isSubmitDisabled || !onSubmit) return
    onSubmit({ checkpointId, response: selectedOption })
  }

  const handleRequestHint = (e) => {
    e?.preventDefault?.()
    if (onRequestHint) {
      onRequestHint({ checkpointId, lessonId })
    }
  }

  return (
    <article
      className="lh-checkpoint-card bento-card"
      data-testid="checkpoint-card"
      {...restProps}
    >
      <header className="lh-checkpoint-header">
        <span className="lh-checkpoint-id-badge mono">
          Checkpoint: {checkpointId || 'cp_default'}
        </span>
        {lessonId && (
          <span className="lh-checkpoint-lesson-tag mono" style={{ fontSize: 'var(--fs-xs)', color: 'var(--ink-muted)' }}>
            {lessonId}
          </span>
        )}
      </header>

      <h2 className="lh-checkpoint-prompt">{prompt}</h2>

      <div className="lh-checkpoint-options" role="radiogroup" aria-label="Phương án trắc nghiệm">
        {options.map((option, idx) => {
          const letter = OPTION_LETTERS[idx] || `${idx + 1}`
          const isSelected = selectedOption === option

          return (
            <button
              key={`${checkpointId || 'cp'}-opt-${idx}`}
              type="button"
              role="radio"
              aria-checked={isSelected}
              className={`lh-checkpoint-option ${isSelected ? 'is-selected' : ''}`}
              onClick={() => !disabled && onSelectOption?.(option)}
              disabled={disabled}
            >
              <span className="lh-checkpoint-option-key mono">{letter}</span>
              <span className="lh-checkpoint-option-text">{option}</span>
            </button>
          )
        })}
      </div>

      <footer className="lh-checkpoint-actions">
        <button
          type="button"
          className="lh-btn-secondary"
          onClick={handleRequestHint}
          disabled={disabled}
        >
          <span>💡 Cần gợi ý Socratic</span>
        </button>

        <button
          type="button"
          className="lh-btn-primary"
          onClick={handleSubmit}
          disabled={isSubmitDisabled}
        >
          {isSubmitting ? 'Đang chấm...' : 'Gửi câu trả lời'}
        </button>
      </footer>

      {gradeResult && (
        <div
          className={`lh-checkpoint-feedback ${gradeResult.passed ? 'is-passed' : 'is-failed'}`}
          role="status"
          aria-live="polite"
        >
          <div style={{ fontWeight: 600, marginBottom: 'var(--sp-1)' }}>
            {gradeResult.passed ? `✓ Chính xác (${gradeResult.score || 100} điểm)` : `Chưa chính xác (${gradeResult.score || 0} điểm)`}
          </div>
          {Array.isArray(gradeResult.rubric_evidence) && gradeResult.rubric_evidence.length > 0 && (
            <div style={{ fontSize: 'var(--fs-xs)', opacity: 0.9 }}>
              {gradeResult.rubric_evidence.map((rubric, idx) => (
                <p key={idx} style={{ margin: 'var(--sp-1) 0 0 0' }}>
                  {rubric}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </article>
  )
}
