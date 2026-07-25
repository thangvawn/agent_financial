import {
  SparkleAppCta,
  SparkleHighlights,
  SparklePlans,
  useSparkleMotion,
} from './HomeSparkleSections'
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
      <div className="sparkle-hero-copy">
        <p className={KICKER}>Northstar Finance Lab</p>
        <h1>Học và thực hành tài chính có kiểm soát.</h1>
        <p>
          Nền tảng cho sinh viên Việt Nam: Learn Hub làm gốc kiến thức, Market & Portfolio, News,
          BCTC và Simulation Lab là nơi quan sát và luyện tập — không phải khuyến nghị mua bán.
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
      <div className="sparkle-dashboard-stage sparkle-reveal" aria-label="Financial dashboard preview">
        <img
          className="sparkle-dashboard-image"
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719b3_Main%20Dashh.png"
          alt="Northstar finance dashboard preview"
        />
        <img
          className="sparkle-floating-card sparkle-floating-card--left"
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e71995_div.png"
          alt=""
        />
        <img
          className="sparkle-floating-card sparkle-floating-card--right"
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e71994_div.png"
          alt=""
        />
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
      description: 'Vài câu hỏi để hiểu trình độ và mục tiêu học — không phải tư vấn đầu tư.',
    },
    {
      number: '02',
      title: 'Learn Hub',
      description: 'Thư viện video, sách và tài liệu là gốc kiến thức trước khi nhìn thị trường.',
    },
    {
      number: '03',
      title: 'Quan sát dữ liệu',
      description: 'News và BCTC giúp đọc bối cảnh; AI giải thích chỉ số, không phím hàng.',
    },
    {
      number: '04',
      title: 'Thực hành an toàn',
      description: 'Market lệnh ảo và Simulation Lab để luyện kỷ luật rủi ro trên dữ liệu lịch sử.',
    },
  ]
  return (
    <section className="sparkle-demo-flow sparkle-reveal" aria-label="Luồng sản phẩm">
      <div className="sparkle-section-heading">
        <h2>Một hành trình học có thứ tự.</h2>
        <p>Từ hiểu bản thân → học → đọc dữ liệu → thực hành có kiểm soát.</p>
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
        <h2>Learn Hub là gốc. Các module còn lại để thực hành.</h2>
        <p>
          Mỗi không gian một nhiệm vụ: học, theo dõi thị trường, đọc tin, phân tích BCTC,
          hoặc tua kịch bản lịch sử trong Simulation Lab.
        </p>
      </div>
      <div className="sparkle-feature-visual sparkle-feature-visual--one sparkle-reveal">
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719a8_639d70c4406f2f93d788cb0f_div-2-min.png"
          alt="Market analytics preview"
        />
      </div>
      <div className="sparkle-feature-visual sparkle-feature-visual--two sparkle-reveal">
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719a7_639d70c47a191caa80cab6f5_div-1-min.png"
          alt="Learning preview"
        />
      </div>
      <div className="sparkle-feature-copy sparkle-reveal">
        <h2>AI để giải thích — không để ra lệnh mua bán.</h2>
        <p>
          Trợ lý định hướng sang bài học, chỉ số BCTC hoặc tin tức. Guardrail ưu tiên giáo dục
          và cảnh báo rủi ro.
        </p>
        <div className="sparkle-check-list">
          <span>Learning path theo trình độ</span>
          <span>Phân tích BCTC và peer</span>
          <span>Thị trường + lệnh giấy</span>
        </div>
      </div>
      <div className="sparkle-feature-copy sparkle-reveal">
        <h2>An toàn, giải thích được, có dữ liệu.</h2>
        <p>Tập trung học và quan sát — không biến Home thành feed tín hiệu.</p>
      </div>
      <div className="sparkle-feature-visual sparkle-feature-visual--three sparkle-reveal">
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719ab_639d70c46affc08126525de0_div-min.png"
          alt="Portfolio practice preview"
        />
      </div>
    </section>
  )
}
