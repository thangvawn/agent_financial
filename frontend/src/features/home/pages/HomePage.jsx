import {
  SparkleAppCta,
  SparkleHighlights,
  SparklePlans,
} from './HomeSparkleSections'
import { useSparkleMotion } from '../hooks/useSparkleMotion'
import FinanceParticleField from '../components/FinanceParticleField'
import './home.css'

const KICKER = 'home-v2-kicker'

export default function HomePage({
  sessionId,
  onOpenLearning,
  onOpenGuidedInvesting,
  onOpenGlobalTerminal,
  onOpenNews,
  onOpenProLab,
  onOpenOnboarding,
}) {
  const actions = {
    onOpenLearning,
    onOpenGuidedInvesting: () => onOpenGuidedInvesting?.('overview'),
    onOpenGlobalTerminal,
    onOpenNews,
    onOpenProLab,
    onOpenOnboarding,
    primary: sessionId ? onOpenLearning : onOpenOnboarding,
    primaryLabel: sessionId ? 'Vào Learn Hub' : 'Bắt đầu onboarding',
  }

  useSparkleMotion()

  return (
    <section className="home-redesign sparkle-home" aria-label="Northstar Finance Lab">
      <SparkleHero actions={actions} />
      <SparkleModuleStrip onOpen={actions} />
      <SparkleDemoFlow />
      <SparkleFeatureGrid />
      <SparkleAppCta actions={actions} />
      <SparkleHighlights />
      <SparklePlans onOpen={actions} />
    </section>
  )
}

function SparkleHero({ actions }) {
  return (
    <section className="sparkle-hero" aria-label="Northstar Finance hero">
      <FinanceParticleField />
      <div className="sparkle-hero-meta" aria-hidden="true">
        <span>Northstar / 01</span>
        <span>Financial intelligence lab</span>
        <span>26.09.26 / Vietnam</span>
      </div>
      <div className="sparkle-hero-side-label" aria-hidden="true">
        <strong>N.</strong>
        <span>Site of the day / Learn before you act</span>
      </div>
      <div className="sparkle-hero-copy">
        <p className={KICKER}>Northstar Finance Lab</p>
        <h1>Học cách đọc thị trường trước khi thị trường đọc bạn.</h1>
        <p>
          Nền tảng cho sinh viên Việt Nam: Learn Hub làm gốc kiến thức, Market & Portfolio, News,
          BCTC và Simulation Lab là nơi quan sát và luyện tập, không phải khuyến nghị mua bán.
        </p>
        <div className="sparkle-hero-actions">
          <button type="button" className="sparkle-button sparkle-button--light" onClick={actions.primary}>
            {actions.primaryLabel}
          </button>
          <button type="button" className="sparkle-button sparkle-button--dark" onClick={actions.onOpenGlobalTerminal}>
            Xem Market
          </button>
        </div>
      </div>
    </section>
  )
}

function SparkleModuleStrip({ onOpen }) {
  const brands = [
    { label: 'Market & Portfolio', run: onOpen.onOpenGlobalTerminal },
    { label: 'Learn Hub', run: onOpen.onOpenLearning },
    { label: 'BCTC Analysis', run: onOpen.onOpenGuidedInvesting },
    { label: 'News', run: onOpen.onOpenNews },
    { label: 'Simulation Lab', run: onOpen.onOpenProLab },
  ]
  return (
    <section className="sparkle-client-strip sparkle-reveal" aria-label="Các module chính">
      {brands.map((brand, index) => (
        <button
          key={brand.label}
          type="button"
          className="sparkle-client-logo"
          style={{ '--delay': `${index * 80}ms` }}
          onClick={() => brand.run?.()}
        >
          {brand.label}
        </button>
      ))}
    </section>
  )
}

function SparkleDemoFlow() {
  const steps = [
    {
      number: '01',
      title: 'Onboarding nhẹ',
      description: 'Vài câu hỏi để hiểu trình độ và mục tiêu học, không phải tư vấn đầu tư.',
    },
    {
      number: '02',
      title: 'Learn Hub',
      description: 'Thư viện video, sách và tài liệu là gốc kiến thức trước khi nhìn thị trường.',
    },
    {
      number: '03',
      title: 'Quan sát dữ liệu',
      description: 'News và BCTC giúp đọc bối cảnh. AI giải thích chỉ số, không phím hàng.',
    },
    {
      number: '04',
      title: 'Thực hành an toàn',
      description: 'Market lệnh ảo và Simulation Lab để luyện kỷ luật trên dữ liệu lịch sử.',
    },
  ]
  return (
    <section className="sparkle-demo-flow sparkle-reveal" aria-label="Luồng sản phẩm">
      <div className="sparkle-section-heading">
        <p className="northstar-eyebrow">The path / four chapters</p>
        <h2>Một hành trình học có thứ tự.</h2>
        <p>Từ hiểu bản thân, học, đọc dữ liệu đến thực hành có kiểm soát.</p>
      </div>
      <div className="sparkle-demo-flow-grid">
        {steps.map((step, index) => (
          <article
            className="sparkle-demo-flow-card sparkle-reveal"
            style={{ '--delay': `${index * 80}ms` }}
            key={step.number}
          >
            <span>{step.number}</span>
            <h3>{step.title}</h3>
            <p>{step.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function SparkleFeatureGrid() {
  return (
    <section className="sparkle-features" aria-label="Tính năng nổi bật">
      <div className="sparkle-feature-copy sparkle-reveal">
        <p className="northstar-eyebrow">01 / Learn before action</p>
        <h2>Learn Hub là gốc của mọi quyết định tốt.</h2>
        <p>
          Lộ trình học, tài liệu và checkpoint giúp bạn biết mình đang hiểu gì trước khi mở một chart.
        </p>
        <div className="sparkle-check-list">
          <span>Learning path theo trình độ</span>
          <span>Checkpoint không lộ đáp án</span>
          <span>Gợi ý Socratic theo từng bước</span>
        </div>
      </div>
      <div className="sparkle-feature-visual sparkle-feature-visual--one sparkle-reveal">
        <div className="northstar-product-window northstar-product-window--lesson" aria-label="Learn Hub preview">
          <div className="northstar-product-window__bar"><i /><i /><i /><span>learn / checkpoint-03</span></div>
          <div className="northstar-lesson-preview"><span>03 / Risk basics</span><strong>Biên an toàn nói gì về một doanh nghiệp?</strong><div><b>Đang học</b><em>62%</em></div><i /></div>
        </div>
      </div>
      <div className="sparkle-feature-visual sparkle-feature-visual--two sparkle-reveal">
        <div className="northstar-product-window northstar-product-window--market" aria-label="Market preview">
          <div className="northstar-product-window__bar"><i /><i /><i /><span>market / breadth</span></div>
          <div className="northstar-market-preview"><span>VN-Index / 30 sessions</span><strong>1,284.32 <em>+0.84%</em></strong><div className="northstar-market-preview__chart">{[28, 36, 31, 46, 40, 54, 50, 66, 58, 78, 73, 88].map((height, index) => <i key={index} style={{ height: `${height}%` }} />)}</div><small>Quan sát dữ liệu trước khi diễn giải.</small></div>
        </div>
      </div>
      <div className="sparkle-feature-copy sparkle-reveal">
        <p className="northstar-eyebrow">02 / Explain the signal</p>
        <h2>AI để giải thích, không để ra lệnh.</h2>
        <p>
          Trợ lý định hướng sang bài học, chỉ số BCTC hoặc tin tức. Guardrail ưu tiên giáo dục và cảnh báo rủi ro.
        </p>
        <div className="sparkle-check-list">
          <span>Evidence trước kết luận</span>
          <span>Phân tích BCTC và peer</span>
          <span>Thị trường và lệnh giấy</span>
        </div>
      </div>
      <div className="sparkle-feature-copy sparkle-reveal">
        <p className="northstar-eyebrow">03 / Practice with context</p>
        <h2>Thực hành với bối cảnh, không với ảo tưởng.</h2>
        <p>Simulation Lab đưa bạn về dữ liệu lịch sử để đo kỷ luật, drawdown và thói quen ra quyết định.</p>
      </div>
      <div className="sparkle-feature-visual sparkle-feature-visual--three sparkle-reveal">
        <div className="northstar-product-window northstar-product-window--simulation" aria-label="Simulation Lab preview">
          <div className="northstar-product-window__bar"><i /><i /><i /><span>simulation / replay</span></div>
          <div className="northstar-simulation-preview"><div><span>Replay date</span><strong>14.06.2023</strong></div><div><span>Max drawdown</span><strong>-8.42%</strong></div><div className="northstar-simulation-preview__timeline"><i /><i /><i /><i /><i /><i /><i /></div><small>Time skip / bar replay / risk review</small></div>
        </div>
      </div>
    </section>
  )
}
