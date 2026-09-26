function ModuleGlyph({ type }) {
  if (type === 'learn') return <span className="northstar-module-glyph northstar-module-glyph--learn" aria-hidden="true"><i /><i /><i /></span>
  if (type === 'market') return <span className="northstar-module-glyph northstar-module-glyph--market" aria-hidden="true"><i /><i /><i /><i /></span>
  if (type === 'report') return <span className="northstar-module-glyph northstar-module-glyph--report" aria-hidden="true"><i /><i /></span>
  return <span className="northstar-module-glyph northstar-module-glyph--simulation" aria-hidden="true"><i /><i /><i /><i /><i /></span>
}

export function SparkleAppCta({ actions }) {
  return (
    <section className="sparkle-app-cta sparkle-reveal" aria-label="Bắt đầu Northstar">
      <div className="northstar-cta-copy">
        <p className="northstar-eyebrow">Northstar / start here</p>
        <h2>Một lab tài chính được xây cho những quyết định chậm hơn.</h2>
        <p>Học trước. Quan sát kỹ. Thực hành với rủi ro có thể nhìn thấy.</p>
        <div className="sparkle-hero-actions">
          <button type="button" className="sparkle-button sparkle-button--light" onClick={actions.primary}>
            {actions.primaryLabel}
          </button>
          <button type="button" className="sparkle-button sparkle-button--dark" onClick={actions.onOpenLearning}>
            Khám phá Learn Hub
          </button>
        </div>
      </div>
      <div className="northstar-cta-visual" aria-hidden="true">
        <div className="northstar-cta-visual__ring northstar-cta-visual__ring--one" />
        <div className="northstar-cta-visual__ring northstar-cta-visual__ring--two" />
        <div className="northstar-cta-visual__core">
          <span>NS</span>
          <strong>01</strong>
        </div>
      </div>
    </section>
  )
}

export function SparkleHighlights() {
  const modules = [
    ['learn', 'Learn Hub', 'Học kiến thức nền với lộ trình, bài đọc và checkpoint rõ ràng.'],
    ['market', 'Market & Portfolio', 'Quan sát giá, breadth và vị thế trên một mặt phẳng dữ liệu sạch.'],
    ['report', 'BCTC Analysis', 'Đọc báo cáo, so sánh peer và truy nguyên con số về nguồn.'],
    ['simulation', 'Simulation Lab', 'Tua dữ liệu lịch sử để luyện kỷ luật trước khi dùng tiền thật.'],
  ]

  return (
    <section className="sparkle-testimonials sparkle-reveal" aria-label="Các module chính">
      <div className="northstar-section-intro">
        <p className="northstar-eyebrow">The system / four surfaces</p>
        <h2>Một hệ thống. Bốn cách nhìn thị trường.</h2>
        <p>Mỗi module có một nhiệm vụ rõ ràng, cùng chung một nguyên tắc: giải thích trước khi hành động.</p>
      </div>
      <div className="northstar-module-list">
        {modules.map(([type, name, description], index) => (
          <article className="northstar-module-row" key={name}>
            <span className="northstar-module-index">0{index + 1}</span>
            <ModuleGlyph type={type} />
            <div>
              <h3>{name}</h3>
              <p>{description}</p>
            </div>
            <span className="northstar-module-arrow" aria-hidden="true">↗</span>
          </article>
        ))}
      </div>
    </section>
  )
}

export function SparklePlans({ onOpen }) {
  return (
    <section className="sparkle-plans sparkle-reveal" aria-label="Hai lớp trải nghiệm">
      <div className="northstar-section-intro northstar-section-intro--split">
        <div>
          <p className="northstar-eyebrow">Choose your pace</p>
          <h2>Đi từ hiểu đến làm.</h2>
        </div>
        <p>Không cần nhảy thẳng vào chart. Northstar mở đúng không gian khi bạn đã sẵn sàng.</p>
      </div>
      <div className="sparkle-plan-grid">
        <article className="sparkle-plan-card">
          <div className="northstar-plan-topline"><span>01 / CORE</span><span>OPEN</span></div>
          <h3>Learn & Observe</h3>
          <p>Không gian mặc định cho việc học, đọc tin, phân tích BCTC và theo dõi thị trường.</p>
          <ul>
            <li>Onboarding theo trình độ</li>
            <li>Learn Hub và checkpoint</li>
            <li>Market, News và BCTC</li>
          </ul>
          <button type="button" className="sparkle-button sparkle-button--dark" onClick={onOpen.onOpenLearning}>
            Mở Learn Hub
          </button>
        </article>
        <article className="sparkle-plan-card sparkle-plan-card--dark">
          <div className="northstar-plan-topline"><span>02 / PRACTICE</span><span>DEEP MODE</span></div>
          <h3>Simulation Lab</h3>
          <p>Thực hành strategy, replay và risk metrics trên dữ liệu quá khứ trước khi ra quyết định thật.</p>
          <ul>
            <li>Backtest và time skip</li>
            <li>Scenario builder</li>
            <li>Risk metrics có giải thích</li>
          </ul>
          <button type="button" className="sparkle-button sparkle-button--light" onClick={onOpen.onOpenProLab}>
            Mở Simulation Lab
          </button>
        </article>
      </div>
    </section>
  )
}
