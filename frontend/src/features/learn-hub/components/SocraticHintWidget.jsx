import React, { useState } from 'react'
import './checkpoint.css'

const DEFAULT_STEP_TITLES = [
  'Nguyên lý cốt lõi',
  'Mối quan hệ biến số',
  'Câu hỏi định hướng',
]

export default function SocraticHintWidget({
  checkpointId,
  lessonId,
  socraticCoaching,
  steps,
  currentLevel = 1,
  onUnlockNextHint,
  isUnlocking = false,
  // Strictly prevent any leakage
  correct_answer: _ca,
  correctAnswer: _ca2,
  ...restProps
}) {
  void checkpointId
  void lessonId
  void _ca
  void _ca2
  const [internalLevel, setInternalLevel] = useState(currentLevel)
  const activeLevel = Math.max(currentLevel, internalLevel)

  // Construct structured 3-step Socratic pedagogy if not explicitly passed
  const pedagogicalSteps = steps || [
    {
      level: 1,
      title: DEFAULT_STEP_TITLES[0],
      content: socraticCoaching?.focus_concept
        ? `Trọng tâm: ${socraticCoaching.focus_concept}. Hãy xuất phát từ định nghĩa nguyên lý cốt lõi.`
        : 'Hãy xem lại nguyên lý lý thuyết cơ sở liên quan đến câu hỏi.',
    },
    {
      level: 2,
      title: DEFAULT_STEP_TITLES[1],
      content: socraticCoaching?.hint
        ? socraticCoaching.hint
        : 'Phân tích kỹ lưỡng mối tương quan giữa các biến số độc lập và biến số phụ thuộc trong công thức.',
    },
    {
      level: 3,
      title: DEFAULT_STEP_TITLES[2],
      content: 'Soi chiếu lại các lựa chọn: Phương án nào phản ánh chính xác bản chất định lượng vừa phân tích?',
    },
  ]

  const totalLevels = pedagogicalSteps.length
  const canUnlockNext = activeLevel < totalLevels

  const handleNextStep = () => {
    const nextLvl = activeLevel + 1
    setInternalLevel(nextLvl)
    if (onUnlockNextHint) {
      onUnlockNextHint(nextLvl)
    }
  }

  return (
    <div
      className="lh-socratic-widget hint-widget bento-card"
      data-testid="socratic-hint-widget"
      {...restProps}
    >
      <header className="lh-socratic-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
          <span className="lh-socratic-badge mono">Socratic Coach</span>
          <span style={{ fontWeight: 600, fontSize: 'var(--fs-sm)' }}>
            Gợi ý định hướng tư duy
          </span>
        </div>
        <span className="mono" style={{ fontSize: 'var(--fs-xs)', color: 'var(--ink-muted)' }}>
          Mức {Math.min(activeLevel, totalLevels)} / {totalLevels}
        </span>
      </header>

      <div className="lh-socratic-stepper stepper" role="region" aria-label="Các bước gợi ý">
        {pedagogicalSteps.map((step) => {
          const isUnlocked = activeLevel >= step.level
          return (
            <div
              key={`socratic-step-${step.level}`}
              className={`lh-socratic-step step ${isUnlocked ? 'is-active' : 'is-collapsed'}`}
              data-step-level={step.level}
            >
              <div className="lh-socratic-step-header">
                <span className="lh-socratic-step-num mono">
                  {step.level < 10 ? `0${step.level}` : step.level}
                </span>
                <span style={{ flex: 1 }}>{step.title}</span>
                {!isUnlocked && (
                  <span className="mono" style={{ fontSize: 'var(--fs-xs)', opacity: 0.7 }}>
                    🔒 Đang khóa
                  </span>
                )}
              </div>

              {isUnlocked && (
                <div className="lh-socratic-step-content">
                  {step.content}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {canUnlockNext && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: 'var(--sp-2)' }}>
          <button
            type="button"
            className="lh-btn-primary"
            onClick={handleNextStep}
            disabled={isUnlocking}
          >
            {isUnlocking ? 'Đang mở...' : `Xem gợi ý tiếp theo (Mức ${activeLevel + 1})`}
          </button>
        </div>
      )}
    </div>
  )
}
