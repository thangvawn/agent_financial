import { useEffect, useState } from 'react'

import { useHome } from '../../modules/home-onboarding'
import MarketOverviewPage from './MarketOverviewPage'
import './home.css'

const shellClass = 'home-redesign'
const panelClass = 'home-v2-panel'
const kickerClass = 'home-v2-kicker'
const primaryButtonClass = 'home-v2-button home-v2-button--primary'
const secondaryButtonClass = 'home-v2-button home-v2-button--secondary'

export default function HomePage({
  sessionId,
  refreshKey = 0,
  onOpenFinancialHealth,
  onOpenLearning,
  onOpenGoals,
  onOpenGuidedInvesting,
  onOpenInsights,
  onOpenGlobalTerminal,
  onOpenProLab,
  onOpenOnboarding,
  onSessionInvalid,
}) {
  const { data, isLoading, error } = useHome(sessionId, refreshKey)
  const [marketReady, setMarketReady] = useState(() => hasCompletedMarketOverview(sessionId))

  useEffect(() => {
    setMarketReady(hasCompletedMarketOverview(sessionId))
  }, [sessionId])

  useEffect(() => {
    if (sessionId && isInvalidSessionError(error)) onSessionInvalid?.()
  }, [error, onSessionInvalid, sessionId])

  function unlockMarketModules() {
    markMarketOverviewCompleted(sessionId)
    setMarketReady(true)
  }

  if (isLoading) return <HomeLoadingState />

  if (!sessionId || isHomePreviewError(error)) {
    return (
      <HomeExperience
        data={null}
        sessionId={sessionId || 'guest'}
        marketReady={marketReady}
        onMarketInteracted={unlockMarketModules}
        onOpenFinancialHealth={onOpenFinancialHealth}
        onOpenLearning={onOpenLearning}
        onOpenGoals={onOpenGoals}
        onOpenGuidedInvesting={onOpenGuidedInvesting}
        onOpenInsights={onOpenInsights}
        onOpenGlobalTerminal={onOpenGlobalTerminal}
        onOpenProLab={onOpenProLab}
        onOpenOnboarding={onOpenOnboarding}
      />
    )
  }

  if (error) return <p>{error}</p>
  if (!data) return <p>Chưa có dữ liệu Home.</p>

  return (
    <HomeExperience
      data={data}
      sessionId={sessionId}
      marketReady={marketReady}
      onMarketInteracted={unlockMarketModules}
      onOpenFinancialHealth={onOpenFinancialHealth}
      onOpenLearning={onOpenLearning}
      onOpenGoals={onOpenGoals}
      onOpenGuidedInvesting={onOpenGuidedInvesting}
      onOpenInsights={onOpenInsights}
      onOpenGlobalTerminal={onOpenGlobalTerminal}
      onOpenProLab={onOpenProLab}
      onOpenOnboarding={onOpenOnboarding}
    />
  )
}

function HomeExperience({
  data,
  marketReady,
  onOpenFinancialHealth,
  onOpenLearning,
  onOpenGoals,
  onOpenGuidedInvesting,
  onOpenInsights,
  onOpenGlobalTerminal,
  onOpenProLab,
  onOpenOnboarding,
}) {
  const homeState = buildHomeState(data, marketReady)
  useSparkleMotion()

  return (
    <section className={`${shellClass} sparkle-home`}>
      <SparkleHero
        state={homeState}
        onOpenOnboarding={onOpenOnboarding}
        onOpenInsights={onOpenInsights}
      />

      <SparkleClientStrip />

      <SparkleDemoFlow />

      <SparkleFeatureGrid
        state={homeState}
        onOpenFinancialHealth={onOpenFinancialHealth}
        onOpenGoals={onOpenGoals}
        onOpenGuidedInvesting={onOpenGuidedInvesting}
        onOpenLearning={onOpenLearning}
        onOpenGlobalTerminal={onOpenGlobalTerminal}
      />

      <SparkleAppCta onOpenOnboarding={onOpenOnboarding} onOpenLearning={onOpenLearning} />

      <SparkleTestimonials state={homeState} onOpenInsights={onOpenInsights} />

      <SparklePlans
        proEligible={homeState.proEligible}
        onOpenFinancialHealth={onOpenFinancialHealth}
        onOpenProLab={onOpenProLab}
      />
    </section>
  )
}

function SparkleDemoFlow() {
  const steps = [
    {
      number: '01',
      title: 'Hiểu người dùng',
      description: 'Onboarding phân loại nhu cầu: học tài chính, quản lý tiền, bắt đầu đầu tư hoặc nghiên cứu sâu.',
    },
    {
      number: '02',
      title: 'Xây baseline',
      description: 'Financial Health và Goals tạo bối cảnh cá nhân trước khi hệ thống đưa ra bước tiếp theo.',
    },
    {
      number: '03',
      title: 'Giải thích bằng AI',
      description: 'Assistant trả lời theo vai trò: coach, tutor, analyst; luôn ưu tiên giải thích và cảnh báo rủi ro.',
    },
    {
      number: '04',
      title: 'Đào sâu có kiểm soát',
      description: 'Guided Investing, Market Intelligence và Pro Lab phục vụ phân tích dữ liệu, không biến thành phím hàng.',
    },
  ]

  return (
    <section className="sparkle-demo-flow sparkle-reveal" aria-label="Demo flow">
      <div className="sparkle-section-heading">
        <h2>Luồng demo được thiết kế như một sản phẩm thật.</h2>
        <p>Từ người mới đến người dùng nâng cao, mỗi bước đều có mục đích rõ ràng.</p>
      </div>
      <div className="sparkle-demo-flow-grid">
        {steps.map((step, index) => (
          <article className="sparkle-demo-flow-card sparkle-reveal" style={{ '--delay': `${index * 80}ms` }} key={step.number}>
            <span>{step.number}</span>
            <h3>{step.title}</h3>
            <p>{step.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function SparkleHero({ state, onOpenOnboarding, onOpenInsights }) {
  return (
    <section className="sparkle-hero" aria-label="Northstar Finance hero">
      <div className="sparkle-hero-copy">
        <p className={kickerClass}>Northstar Finance Demo</p>
        <h1>AI Agent tài chính cho người dùng Việt Nam.</h1>
        <p>
          Một nền tảng demo kết hợp onboarding, financial health, mục tiêu, học tập, phân tích BCTC, tin tức và dữ liệu thị trường để giúp người dùng hiểu tiền tốt hơn trước khi ra quyết định.
        </p>
        <div className="sparkle-hero-actions">
          <button type="button" className="sparkle-button sparkle-button--dark" onClick={onOpenOnboarding}>
            {state.isPersonalized ? 'Cập nhật hồ sơ' : 'Trải nghiệm demo'}
            <span aria-hidden="true">→</span>
          </button>
          <button type="button" className="sparkle-button sparkle-button--light" onClick={onOpenInsights}>
            Xem năng lực phân tích
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

function SparkleClientStrip() {
  const brands = ['AI Assistant', 'Financial Health', 'Goals', 'BCTC Analysis', 'Pro Lab']
  return (
    <section className="sparkle-client-strip sparkle-reveal" aria-label="Northstar modules">
      {brands.map((brand, index) => (
        <div key={brand} className="sparkle-client-logo" style={{ '--delay': `${index * 80}ms` }}>{brand}</div>
      ))}
    </section>
  )
}

function SparkleFeatureGrid({
  state,
  onOpenFinancialHealth,
  onOpenGoals,
  onOpenGuidedInvesting,
  onOpenLearning,
  onOpenGlobalTerminal,
}) {
  return (
    <section className="sparkle-features" aria-label="Northstar features">
      <div className="sparkle-feature-copy sparkle-reveal">
        <h2>Một demo end-to-end cho hành trình tài chính cá nhân.</h2>
        <p>
          Người dùng đi từ hiểu bản thân, đặt mục tiêu, học kiến thức nền, đọc bối cảnh thị trường, đến phân tích doanh nghiệp theo cách có kiểm soát rủi ro.
        </p>
      </div>
      <button type="button" className="sparkle-feature-visual sparkle-feature-visual--one sparkle-reveal" onClick={onOpenGlobalTerminal}>
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719a8_639d70c4406f2f93d788cb0f_div-2-min.png"
          alt="Market analytics preview"
        />
      </button>
      <button type="button" className="sparkle-feature-visual sparkle-feature-visual--two sparkle-reveal" onClick={onOpenFinancialHealth}>
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719a7_639d70c47a191caa80cab6f5_div-1-min.png"
          alt="Financial health preview"
        />
      </button>
      <div className="sparkle-feature-copy sparkle-reveal">
        <h2>AI không chỉ chat, mà điều phối nhiều module.</h2>
        <p>
          Trợ lý có thể định tuyến câu hỏi sang financial coach, learning tutor, market analyst hoặc BCTC analyst. Luồng hiện tại: {state.healthReady ? 'đã có baseline để cá nhân hóa' : 'bắt đầu bằng baseline để cá nhân hóa'}.
        </p>
        <div className="sparkle-check-list">
          <button type="button" onClick={onOpenGoals}>Goal planner theo tiến độ</button>
          <button type="button" onClick={onOpenLearning}>Learning path theo trình độ</button>
          <button type="button" onClick={onOpenGuidedInvesting}>Phân tích BCTC và peer</button>
        </div>
      </div>
      <div className="sparkle-feature-copy sparkle-reveal">
        <h2>Điểm nổi bật: an toàn, giải thích được, có dữ liệu.</h2>
        <p>
          Dự án ưu tiên giải thích và giáo dục tài chính, không phím hàng. Các quyết định được hỗ trợ bằng dữ liệu, guardrails và luồng kiểm tra phù hợp từng mức độ người dùng.
        </p>
      </div>
      <button type="button" className="sparkle-feature-visual sparkle-feature-visual--three sparkle-reveal" onClick={onOpenGuidedInvesting}>
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719ab_639d70c46affc08126525de0_div-min.png"
          alt="Portfolio review preview"
        />
      </button>
    </section>
  )
}

function SparkleAppCta({ onOpenOnboarding, onOpenLearning }) {
  return (
    <section className="sparkle-app-cta sparkle-reveal" aria-label="Start Northstar">
      <div>
        <h2>Demo một sản phẩm tài chính thông minh, không chỉ là dashboard.</h2>
        <button type="button" className="sparkle-button sparkle-button--dark" onClick={onOpenOnboarding}>
          Bắt đầu luồng demo <span aria-hidden="true">→</span>
        </button>
        <p>*Tập trung vào trải nghiệm, giải thích, dữ liệu và an toàn người dùng.</p>
      </div>
      <button type="button" className="sparkle-phone-preview" onClick={onOpenLearning}>
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719ac_639d70c3406f2fc42c88caee_Frame%203868-min.png"
          alt="Learning app preview"
        />
      </button>
    </section>
  )
}

function SparkleTestimonials({ state, onOpenInsights }) {
  const quotes = [
    ['Onboarding thông minh', state.healthReady ? 'Hồ sơ đã có baseline để hệ thống đề xuất bước tiếp theo.' : 'Demo bắt đầu bằng vài câu hỏi để phân nhóm nhu cầu người dùng.'],
    ['Market Intelligence', 'Tóm tắt tin tức, driver và rủi ro thị trường bằng ngôn ngữ dễ hiểu.'],
    ['Guided Investing', 'Phân tích BCTC, peer comparison và thesis coverage trước khi đi sâu hơn.'],
    ['Trust & Safety', 'Có guardrails để tránh nội dung phím hàng, chắc thắng hoặc khuyến nghị cá nhân hóa sai ngữ cảnh.'],
  ]

  return (
    <section className="sparkle-testimonials sparkle-reveal" aria-label="Demo highlights">
      <h2>Dự án có gì nổi bật?</h2>
      <div className="sparkle-testimonial-grid">
        {quotes.map(([name, quote], index) => (
          <button key={name} type="button" className="sparkle-testimonial-card sparkle-reveal" style={{ '--delay': `${index * 90}ms` }} onClick={onOpenInsights}>
            <img
              src={[
                'https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719b9_duncan%20(1).jpg',
                'https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e71979_Screenshot_8%20(1).jpg',
                'https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e7197c_pexels-nishant-kumar-10939146.jpg',
                'https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e7197d_Screenshot_9.jpg',
              ][index]}
              alt=""
            />
            <strong>{name}</strong>
            <p>{quote}</p>
          </button>
        ))}
      </div>
    </section>
  )
}

function SparklePlans({ proEligible, onOpenFinancialHealth, onOpenProLab }) {
  return (
    <section className="sparkle-plans sparkle-reveal" aria-label="Ready to get started">
      <div className="sparkle-section-heading">
        <h2>Hai lớp trải nghiệm trong demo.</h2>
        <p>Public dành cho người dùng phổ thông, Pro Lab dành cho phân tích và nghiên cứu sâu.</p>
      </div>
      <div className="sparkle-plan-grid">
        <article className="sparkle-plan-card">
          <span>Public</span>
          <h3>Retail Experience</h3>
          <p>Onboarding, financial health, goals, learning, assistant và market explanation cho người dùng phổ thông.</p>
          <button type="button" className="sparkle-button sparkle-button--dark" onClick={onOpenFinancialHealth}>Xem Public Demo</button>
          <ul>
            <li>Onboarding</li>
            <li>Financial Health</li>
            <li>Goals & Learn</li>
          </ul>
        </article>
        <article className="sparkle-plan-card sparkle-plan-card--dark">
          <span>{proEligible ? 'Unlocked' : 'Advanced'}</span>
          <h3>Research Lab</h3>
          <p>Backtest, scenario, blueprint, experiment log và không gian nghiên cứu tách khỏi luồng public.</p>
          <button type="button" className="sparkle-button sparkle-button--light" onClick={onOpenProLab}>Mở Pro Lab</button>
          <ul>
            <li>Backtest</li>
            <li>Scenario</li>
            <li>Research Audit</li>
          </ul>
        </article>
      </div>
    </section>
  )
}

function useSparkleMotion() {
  useEffect(() => {
    const root = document.querySelector('.sparkle-home')
    const hero = document.querySelector('.sparkle-hero')
    if (!root || !hero) return undefined

    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) {
      root.querySelectorAll('.sparkle-reveal').forEach((item) => item.classList.add('is-visible'))
      return undefined
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.16, rootMargin: '0px 0px -8% 0px' },
    )

    root.querySelectorAll('.sparkle-reveal').forEach((item) => observer.observe(item))

    function handlePointerMove(event) {
      const rect = hero.getBoundingClientRect()
      const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2
      const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2
      hero.style.setProperty('--hero-x', x.toFixed(3))
      hero.style.setProperty('--hero-y', y.toFixed(3))
    }

    hero.addEventListener('pointermove', handlePointerMove)

    return () => {
      observer.disconnect()
      hero.removeEventListener('pointermove', handlePointerMove)
    }
  }, [])
}

function PathChooser({ onOpenFinancialHealth, onOpenGuidedInvesting, onOpenInsights }) {
  const paths = [
    {
      label: 'Tôi muốn quản lý tiền tốt hơn',
      title: 'Start with your baseline',
      description: 'Hiểu dòng tiền, quỹ dự phòng và sức chịu rủi ro trước khi đi xa hơn.',
      action: onOpenFinancialHealth,
    },
    {
      label: 'Tôi muốn bắt đầu đầu tư',
      title: 'Check readiness first',
      description: 'Đọc vị thế tài chính của bạn trước khi nhìn danh mục hoặc thị trường.',
      action: onOpenGuidedInvesting,
    },
    {
      label: 'Tôi muốn hiểu thị trường',
      title: 'Read market as context',
      description: 'Hiểu xu hướng và rủi ro bằng ngôn ngữ đơn giản, không phải lệnh mua/bán.',
      action: onOpenInsights,
    },
  ]

  return (
    <section className="home-v2-path-chooser" aria-label="Choose your starting path">
      <div>
        <p className={kickerClass}>Start here</p>
        <h2>Chọn đường đi phù hợp với bạn.</h2>
      </div>
      <div className="home-v2-path-grid">
        {paths.map((path) => (
          <button key={path.label} type="button" className="home-v2-path-card" onClick={path.action}>
            <span>{path.label}</span>
            <strong>{path.title}</strong>
            <p>{path.description}</p>
          </button>
        ))}
      </div>
    </section>
  )
}

function WhyDifferent() {
  const points = [
    'Không phím hàng',
    'Không đẩy lệnh mua bán',
    'Giải thích trước, hành động sau',
    'Học đi cùng dữ liệu thật',
  ]

  return (
    <section className="home-v2-trust-strip" aria-label="Why Northstar is different">
      <p className={kickerClass}>Why this is different</p>
      <div>
        {points.map((point) => (
          <span key={point}>{point}</span>
        ))}
      </div>
    </section>
  )
}

function FinanceSolutionGrid({
  onOpenFinancialHealth,
  onOpenGoals,
  onOpenGuidedInvesting,
  onOpenLearning,
  onOpenGlobalTerminal,
  onOpenProLab,
}) {
  const solutions = [
    {
      eyebrow: 'Personal OS',
      title: 'Financial Health & Goals',
      description: 'Thiết lập baseline, quỹ dự phòng và mục tiêu trước khi ra quyết định đầu tư.',
      cta: 'Build my baseline',
      action: onOpenFinancialHealth,
      secondary: 'Open goals',
      secondaryAction: onOpenGoals,
      metric: '5 phút',
    },
    {
      eyebrow: 'Market OS',
      title: 'Market context without noise',
      description: 'Đọc thị trường bằng context, driver và rủi ro — không biến thành tín hiệu mua bán.',
      cta: 'Open terminal',
      action: onOpenGlobalTerminal,
      secondary: 'Review BCTC',
      secondaryAction: onOpenGuidedInvesting,
      metric: 'Live',
    },
    {
      eyebrow: 'Learning OS',
      title: 'Learn before action',
      description: 'Bài học ngắn nối với dữ liệu thật để hiểu rủi ro, dòng tiền và hành vi đầu tư.',
      cta: 'Start learning',
      action: onOpenLearning,
      secondary: 'Ask AI',
      secondaryAction: onOpenLearning,
      metric: '3 phút',
    },
    {
      eyebrow: 'Research OS',
      title: 'Pro Lab for deeper research',
      description: 'Không dành cho người mới bắt đầu: backtest, blueprint và scenario trong môi trường tách biệt.',
      cta: 'Open Pro Lab',
      action: onOpenProLab,
      secondary: 'Market first',
      secondaryAction: onOpenGlobalTerminal,
      metric: 'Pro',
    },
  ]

  return (
    <section className="home-do-solutions" aria-label="Northstar financial product architecture">
      <div className="home-do-section-copy">
        <p className={kickerClass}>One financial workspace</p>
        <h2>Kiến trúc giống cloud platform, nhưng dành cho quyết định tài chính.</h2>
        <p>
          Mỗi module là một product surface rõ ràng: cá nhân, thị trường, học tập và nghiên cứu chuyên sâu.
        </p>
      </div>
      <div className="home-do-solution-grid">
        {solutions.map((solution) => (
          <article className="home-do-solution-card" key={solution.title}>
            <div className="home-do-card-topline">
              <span>{solution.eyebrow}</span>
              <strong>{solution.metric}</strong>
            </div>
            <h3>{solution.title}</h3>
            <p>{solution.description}</p>
            <div className="home-do-card-actions">
              <button type="button" className={primaryButtonClass} onClick={solution.action}>
                {solution.cta}
              </button>
              <button type="button" className={secondaryButtonClass} onClick={solution.secondaryAction}>
                {solution.secondary}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function RecommendedForYou({ state, onOpenFinancialHealth, onOpenLearning, onOpenInsights, onOpenGlobalTerminal }) {
  const features = [
    {
      type: 'Recommended first',
      title: state.healthReady ? 'Read risk through your own baseline' : 'Answer the first 5 money questions',
      description: state.healthReady
        ? 'Một guide ngắn nối dòng tiền, quỹ dự phòng và mức chịu rủi ro trước khi đọc thị trường.'
        : 'Mở baseline tài chính trong vài phút để app hiểu bạn đang ở đâu.',
      cta: state.healthReady ? 'Open Learn Hub' : 'Start baseline',
      action: state.healthReady ? onOpenLearning : onOpenFinancialHealth,
      accent: 'book',
    },
    {
      type: 'Today matters',
      title: 'What changed today?',
      description: 'Tóm tắt tin và driver thị trường bằng ngôn ngữ đơn giản, không biến thành tín hiệu mua bán.',
      cta: 'Read brief',
      action: onOpenInsights,
      accent: 'news',
    },
    {
      type: 'Live board',
      title: 'Signals when you need depth',
      description: 'Mở terminal khi cần chart, cross-asset context và dữ liệu chi tiết hơn.',
      cta: 'Open Terminal',
      action: onOpenGlobalTerminal,
      accent: 'terminal',
    },
  ]

  return (
    <section className="home-v2-feature-shelf" aria-label="Featured financial intelligence">
      <div className="home-v2-feature-copy">
        <p className={kickerClass}>Recommended for you</p>
        <h2>Hôm nay nên làm gì tiếp?</h2>
        <p>
          Home ưu tiên việc có ích nhất ngay bây giờ: tạo baseline, đọc brief dễ hiểu, hoặc mở terminal khi bạn cần đào sâu.
        </p>
      </div>
      <div className="home-v2-feature-stack">
        {features.map((feature, index) => (
          <button
            key={feature.title}
            type="button"
            className={`home-v2-feature-card home-v2-feature-card--${feature.accent} ${index === 0 ? 'home-v2-feature-card--primary' : ''}`}
            onClick={feature.action}
          >
            <span>{feature.type}</span>
            <strong>{feature.title}</strong>
            <p>{feature.description}</p>
            <small>{feature.cta}</small>
          </button>
        ))}
      </div>
    </section>
  )
}

function HomeHeroRow({ state, onOpenOnboarding, onOpenLearning, onOpenInsights }) {
  return (
    <section className="home-v2-hero" aria-label="Home overview">
      <PersonalStateCard
        state={state}
        onOpenOnboarding={onOpenOnboarding}
        onOpenLearning={onOpenLearning}
        onOpenInsights={onOpenInsights}
      />
      <div className="home-v2-hero-side">
        <TodaySnapshotGrid state={state} />
        <AICompanionCard onOpenLearning={onOpenLearning} onOpenInsights={onOpenInsights} />
      </div>
    </section>
  )
}

function PersonalStateCard({ state, onOpenOnboarding, onOpenLearning, onOpenInsights }) {
  return (
    <article className="home-v2-command-card">
      <div className="home-v2-orbit" />
      <p className={kickerClass}>Northstar Finance</p>
      <h1>
        <span>Hiểu tài chính của bạn trước.</span>
        <span>Đầu tư sau.</span>
      </h1>
      <p className="home-v2-lede">
        {state.isPersonalized
          ? 'Northstar nối baseline, goals, học tập và bối cảnh thị trường để bạn biết bước tiếp theo phù hợp với mình.'
          : 'Một AI companion giúp bạn học, hiểu và hành động an toàn hơn với tiền, kể cả khi bạn chưa biết bắt đầu từ đâu.'}
      </p>
      <div className="home-v2-signal-strip">
        <HeroSignal label="Health" value={state.healthReady ? 'Ready' : 'Baseline'} tone={state.healthReady ? 'good' : 'neutral'} />
        <HeroSignal label="Goals" value={state.goalReady ? 'Tracking' : 'Unset'} tone={state.goalReady ? 'good' : 'warn'} />
        <HeroSignal label="Market" value={state.marketReady ? 'Context on' : 'Watchlist'} tone={state.marketReady ? 'good' : 'neutral'} />
      </div>
      <div className="home-v2-actions">
        <button type="button" className={primaryButtonClass} onClick={onOpenOnboarding}>
          {state.isPersonalized ? 'Update financial baseline' : 'Bắt đầu baseline'}
        </button>
        <button type="button" className={secondaryButtonClass} onClick={onOpenLearning}>
          Hỏi AI tôi nên bắt đầu từ đâu
        </button>
        <button type="button" className={secondaryButtonClass} onClick={onOpenInsights}>
          Xem market pulse
        </button>
      </div>
    </article>
  )
}

function HeroSignal({ label, value, tone }) {
  const toneClass = tone === 'good' ? 'home-v2-mini-signal--good' : tone === 'warn' ? 'home-v2-mini-signal--warn' : 'home-v2-mini-signal--neutral'
  return (
    <div className={`home-v2-mini-signal ${toneClass}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function TodaySnapshotGrid({ state }) {
  const snapshots = [
    {
      label: 'Health',
      status: state.healthStatus,
      description: state.healthDescription,
      action: state.healthAction,
      tone: state.healthReady ? 'good' : 'warn',
    },
    {
      label: 'Goals',
      status: state.goalStatus,
      description: state.goalDescription,
      action: state.goalAction,
      tone: state.goalReady ? 'good' : 'warn',
    },
    {
      label: 'Market',
      status: state.marketStatus,
      description: state.marketDescription,
      action: state.marketAction,
      tone: state.marketReady ? 'good' : 'neutral',
    },
    {
      label: 'Alerts',
      status: state.alertStatus,
      description: state.alertDescription,
      action: state.alertAction,
      tone: state.alertCount > 0 ? 'warn' : 'good',
    },
  ]

  return (
    <div className="home-v2-snapshot-grid" aria-label="Today snapshot">
      {snapshots.map((snapshot) => (
        <SnapshotCard key={snapshot.label} {...snapshot} />
      ))}
    </div>
  )
}

function SnapshotCard({ label, status, description, action, tone = 'neutral' }) {
  const toneClass = tone === 'good'
    ? 'home-v2-snapshot-card--good'
    : tone === 'warn'
      ? 'home-v2-snapshot-card--attention'
      : 'home-v2-snapshot-card--neutral'
  return (
    <article className={`home-v2-snapshot-card ${toneClass}`}>
      <span>{label}</span>
      <strong>{status}</strong>
      <p>{description}</p>
      <small>{action}</small>
    </article>
  )
}

function AICompanionCard({ onOpenLearning, onOpenInsights }) {
  return (
    <article className="home-v2-ai-card">
      <div>
        <p className={kickerClass}>AI Companion</p>
        <h2>Bạn chưa biết bắt đầu từ đâu?</h2>
        <p>
                    Hỏi AI trước khi hành động. Tutor giải thích khái niệm, Analyst tóm tắt rủi ro, Coach gợi ý bước nhỏ.
        </p>
      </div>
      <div className="home-v2-prompt-list" aria-label="Gợi ý câu hỏi">
        <span>Tôi nên bắt đầu từ đâu?</span>
        <span>Tôi có nên lo về rủi ro hôm nay không?</span>
        <span>Nếu chưa có nhiều tiền, tôi nên học gì trước?</span>
      </div>
      <div className="home-v2-actions">
        <button type="button" className={primaryButtonClass} onClick={onOpenLearning}>Mở Tutor</button>
        <button type="button" className={secondaryButtonClass} onClick={onOpenInsights}>Hỏi về thị trường</button>
      </div>
    </article>
  )
}

function NextBestActions({ state, onOpenFinancialHealth, onOpenLearning, onOpenInsights }) {
  const actions = [
    {
      title: 'Build your baseline',
      description: 'Làm xong bước này để mở Health score, goal plan và gợi ý học phù hợp.',
      time: '2 phút',
      cta: state.healthReady ? 'Xem lại hồ sơ' : 'Bắt đầu',
      onClick: onOpenFinancialHealth,
    },
    {
      title: 'Learn the next concept',
      description: 'Một bài học ngắn giúp bạn hiểu tiền và rủi ro trước khi xem market sâu hơn.',
      time: '3-5 phút',
      cta: 'Học ngay',
      onClick: onOpenLearning,
    },
    {
      title: 'Read the market pulse',
      description: 'Một market pulse rất gọn: trạng thái, ý nghĩa với người mới, và nút xem sâu hơn.',
      time: '2 phút',
      cta: 'Xem insight',
      onClick: onOpenInsights,
    },
  ]

  return (
    <section className="home-v2-action-rail" aria-label="Next best actions">
      {actions.map((action) => (
        <ActionCard key={action.title} {...action} />
      ))}
    </section>
  )
}

function ActionCard({ title, description, time, cta, onClick }) {
  return (
    <article className="home-v2-action-card">
      <div>
        <span>{time}</span>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <button type="button" className={primaryButtonClass} onClick={onClick}>{cta}</button>
    </article>
  )
}

function HealthGoalsRow({ state, onOpenFinancialHealth, onOpenGoals }) {
  return (
    <section className="home-v2-split-row" aria-label="Financial health and goals">
      <HealthEmptyStateCard state={state} onOpenFinancialHealth={onOpenFinancialHealth} />
      <GoalsEmptyStateCard state={state} onOpenGoals={onOpenGoals} />
    </section>
  )
}

function HealthEmptyStateCard({ state, onOpenFinancialHealth }) {
  return (
    <article className={panelClass}>
      <p className={kickerClass}>Financial Health</p>
      <h2>{state.healthReady ? 'Financial baseline is ready' : 'Financial baseline missing'}</h2>
      <p>
        {state.healthReady
          ? state.healthSummary
          : 'Trả lời 5 câu hỏi để mở phân tích cá nhân hóa về dòng tiền, quỹ dự phòng và sức chịu rủi ro.'}
      </p>
      <div className="home-v2-chip-row">
        <RiskPostureBadge label={state.healthReady ? 'Có thể cá nhân hóa' : 'Cần baseline'} tone={state.healthReady ? 'good' : 'warn'} />
        <span>{state.healthReady ? 'Sẵn sàng nối với Goals' : 'Không cần nhập dữ liệu quá nhiều'}</span>
      </div>
      <button type="button" className={primaryButtonClass} onClick={onOpenFinancialHealth}>
        {state.healthReady ? 'Xem Financial Health' : 'Bắt đầu đánh giá'}
      </button>
    </article>
  )
}

function GoalsEmptyStateCard({ state, onOpenGoals }) {
  return (
    <article className={panelClass}>
      <p className={kickerClass}>Goals</p>
      <h2>{state.goalReady ? 'Goals are being tracked' : 'No active goals yet'}</h2>
      <p>
        {state.goalReady
          ? state.goalSummary
          : 'Bắt đầu với quỹ khẩn cấp, mua nhà, học tập, đầu tư dài hạn hoặc hỗ trợ gia đình.'}
      </p>
      <div className="home-v2-chip-row">
        {['Quỹ khẩn cấp', 'Mua nhà', 'Hỗ trợ gia đình'].map((goal) => (
          <span key={goal}>{goal}</span>
        ))}
      </div>
      <button type="button" className={primaryButtonClass} onClick={onOpenGoals}>
        {state.goalReady ? 'Xem Goals' : 'Tạo goal đầu tiên'}
      </button>
    </article>
  )
}

function LearnMarketRow({ state, onOpenLearning, onOpenInsights, onOpenGuidedInvesting }) {
  return (
    <section className="home-v2-split-row home-v2-split-row--learning" aria-label="Learning and market explanation">
      <LearnRecommendationCard state={state} onOpenLearning={onOpenLearning} />
      <MarketExplainedCard
        state={state}
        onOpenInsights={onOpenInsights}
        onOpenGuidedInvesting={onOpenGuidedInvesting}
      />
    </section>
  )
}

function LearnRecommendationCard({ state, onOpenLearning }) {
  return (
    <article className={panelClass}>
      <p className={kickerClass}>Learn Hub hôm nay</p>
      <h2>{state.learningTitle}</h2>
      <p>{state.learningReason}</p>
      <div className="home-v2-flow-tags">
        <span>Nền tảng tài chính</span>
        <i />
        <span>Hiểu rủi ro</span>
        <i />
        <span>Ứng dụng vào mục tiêu</span>
      </div>
      <button type="button" className={primaryButtonClass} onClick={onOpenLearning}>Học bài 3 phút</button>
    </article>
  )
}

function MarketExplainedCard({ state, onOpenInsights, onOpenGuidedInvesting }) {
  return (
    <article className={panelClass}>
      <div className="home-v2-panel-head">
        <p className={kickerClass}>Market explained</p>
        <DataFreshnessBadge fresh={state.marketReady} />
      </div>
      <h2>{state.marketHeadline}</h2>
      <p>{state.marketPlainSummary}</p>
      <div className="home-v2-explainer-list">
        <span>Vì sao quan trọng: bối cảnh thị trường ảnh hưởng cách bạn đọc rủi ro, không phải lý do để mua/bán ngay.</span>
        <span>Người mới nên hiểu: biến động là tín hiệu cần giải thích, không phải mệnh lệnh hành động.</span>
      </div>
      <div className="home-v2-actions">
        <button type="button" className={primaryButtonClass} onClick={onOpenInsights}>Xem insight chi tiết</button>
        <button type="button" className={secondaryButtonClass} onClick={onOpenGuidedInvesting}>Review exposure</button>
      </div>
    </article>
  )
}

function ChartInsightSection({ sessionId, marketReady, state, onMarketInteracted, onOpenLearning, onOpenGlobalTerminal }) {
  return (
    <section className="home-v2-chart-panel" aria-label="Deeper market insight">
      <InsightNarrativeHeader state={state} onOpenLearning={onOpenLearning} onOpenGlobalTerminal={onOpenGlobalTerminal} />
      <MarketOverviewPage
        sessionId={sessionId}
        embedded
        minimal
        hasInteracted={marketReady}
        onInteracted={onMarketInteracted}
      />
    </section>
  )
}

function InsightNarrativeHeader({ state, onOpenLearning, onOpenGlobalTerminal }) {
  return (
    <div className="home-v2-insight-header">
      <div>
        <p className={kickerClass}>Đào sâu thêm</p>
        <h2>Chart thị trường và risk score</h2>
        <p>
          Chart nằm ở phần phân tích sâu hơn. Hãy dùng nó để hiểu bối cảnh và độ nhạy rủi ro, không biến nó thành tín hiệu chắc chắn.
        </p>
      </div>
      <div className="home-v2-insight-actions">
        <DataFreshnessBadge fresh={state.marketReady} />
        <RiskPostureBadge label={state.marketReady ? 'Risk context available' : 'Cần tương tác chart'} tone={state.marketReady ? 'good' : 'warn'} />
        <button type="button" className={secondaryButtonClass} onClick={onOpenLearning}>Muốn hiểu chart này? Học bài 3 phút</button>
        <button type="button" className={secondaryButtonClass} onClick={onOpenGlobalTerminal}>Mở Global Terminal</button>
      </div>
    </div>
  )
}

function DataFreshnessBadge({ fresh }) {
  return (
    <span className={fresh ? 'home-v2-badge home-v2-badge--good' : 'home-v2-badge home-v2-badge--warn'}>
      {fresh ? 'Dữ liệu mới' : 'Cần kiểm tra dữ liệu'}
    </span>
  )
}

function RiskPostureBadge({ label, tone = 'neutral' }) {
  const toneClass = tone === 'good'
    ? 'home-v2-badge--good'
    : tone === 'warn'
      ? 'home-v2-badge--warn'
      : 'home-v2-badge--neutral'
  return <span className={`home-v2-badge ${toneClass}`}>{label}</span>
}

function ProLabLowPriority({ proEligible, onOpenProLab }) {
  return (
    <section className="home-v2-pro-strip" aria-label="Pro Lab secondary entry">
      <div>
        <p className={kickerClass}>Pro Lab</p>
        <h2>Research sandbox, không phải điểm bắt đầu của public Home.</h2>
      </div>
      <p>
        {proEligible
          ? 'Dùng cho blueprint, scenario, backtest và experiment log. Tách khỏi hành trình người mới để sản phẩm không bị hiểu nhầm là nơi phát tín hiệu.'
          : 'Được giữ ở mức nhỏ. Người dùng public nên bắt đầu từ hồ sơ tài chính, mục tiêu, học tập và market explanation trước.'}
      </p>
      <button type="button" className={secondaryButtonClass} onClick={onOpenProLab}>Mở Pro Lab</button>
    </section>
  )
}

function HomeLoadingState() {
  return (
    <section className={shellClass}>
      <article className={panelClass}>
        <p className={kickerClass}>Northstar Companion</p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">Đang chuẩn bị Home...</h1>
        <p className="mt-2 text-sm text-slate-600">Hệ thống đang tải trạng thái tài chính, mục tiêu, học tập và dữ liệu thị trường.</p>
      </article>
    </section>
  )
}

function buildHomeState(data, marketReady) {
  const health = data?.health_snapshot
  const goal = data?.goal_snapshot
  const community = data?.community_snapshot
  const alerts = buildFriendlyAlerts(data, marketReady)

  return {
    isPersonalized: Boolean(data),
    marketReady,
    healthReady: Boolean(health),
    goalReady: Boolean(goal),
    proEligible: Boolean(data?.pro_eligible),
    alertCount: alerts.length,
    personalLabel: data ? 'Home đã cá nhân hóa' : 'Chế độ khám phá',
    personalMessage: data
      ? 'Bạn có thể nối Health, Goals, Learn và Market để xem bước phù hợp tiếp theo.'
      : 'Hoàn tất onboarding để mở Health, Goals và gợi ý học tập phù hợp hơn.',
    healthStatus: health ? 'Đã có baseline' : 'Chưa có đánh giá',
    healthDescription: health?.summary || 'Cần vài câu hỏi để hiểu dòng tiền, dự phòng và sức chịu rủi ro.',
    healthAction: health ? 'Xem lại baseline' : 'Trả lời 5 câu hỏi',
    healthSummary: health?.summary || '',
    goalStatus: goal ? goalStatusLabel(goal.reminder_status) : 'Bạn chưa có mục tiêu nào',
    goalDescription: goal?.summary || 'Chọn một mục tiêu gần nhất để hệ thống giúp bạn theo dõi tiến độ.',
    goalAction: goal ? 'Xem tiến độ' : 'Tạo goal đầu tiên',
    goalSummary: goal?.summary || '',
    marketStatus: marketReady ? 'Đã có bối cảnh' : 'Có thể xem ngay',
    marketDescription: marketReady
      ? 'Bạn đã tương tác với chart, có thể đọc các phần giải thích sâu hơn.'
      : 'Bắt đầu bằng bản tóm tắt dễ hiểu trước khi nhìn chart chi tiết.',
    marketAction: marketReady ? 'Đọc insight tiếp' : 'Xem thị trường dễ hiểu',
    alertStatus: alerts.length ? `${alerts.length} điểm cần xem` : 'Không có cảnh báo nổi bật',
    alertDescription: alerts[0]?.description || 'Tiếp tục theo dõi dữ liệu và mục tiêu định kỳ.',
    alertAction: alerts.length ? alerts[0].action : 'Tiếp tục theo dõi',
    learningTitle: health ? 'Hiểu rủi ro theo sức khỏe tài chính của bạn' : 'Bài đầu tiên: nền tảng tài chính cá nhân',
    learningReason: health
      ? 'Vì Home đã có một phần bối cảnh cá nhân, bài học nên nối trực tiếp với cách bạn đọc rủi ro và mục tiêu.'
      : 'Vì bạn chưa có baseline, bài học đầu tiên nên giúp hiểu quỹ dự phòng, dòng tiền và rủi ro trước.',
    marketHeadline: marketReady ? 'Thị trường đã có bối cảnh để giải thích' : 'Thị trường nên được đọc như bối cảnh, không phải tín hiệu',
    marketPlainSummary: marketReady
      ? 'Bạn đã xem chart. Bước tiếp theo là hiểu điều gì đang thay đổi, vì sao nó quan trọng và nó liên quan thế nào tới mục tiêu của bạn.'
      : 'Trước khi đi vào danh mục hoặc kế hoạch, hãy đọc thị trường bằng ngôn ngữ đơn giản: xu hướng, biến động và mức rủi ro hiện tại.',
    communityReminder: community?.active_notification_count || 0,
  }
}

function buildFriendlyAlerts(data, marketReady) {
  const alerts = []
  if (!data?.health_snapshot) {
    alerts.push({
      description: 'Chưa có Financial Health nên Home chưa nên cá nhân hóa sâu.',
      action: 'Hoàn tất hồ sơ',
    })
  }
  if (!data?.goal_snapshot) {
    alerts.push({
      description: 'Chưa có mục tiêu nên các gợi ý hành động còn chung.',
      action: 'Tạo goal đầu tiên',
    })
  }
  if (!marketReady) {
    alerts.push({
      description: 'Bạn chưa tương tác với chart thị trường trong Home.',
      action: 'Xem bối cảnh thị trường',
    })
  }
  if (data?.goal_snapshot?.reminder_status === 'off_track') {
    alerts.push({
      description: 'Một mục tiêu đang lệch nhịp so với kế hoạch.',
      action: 'Xem lại Goals',
    })
  }
  if (data?.community_snapshot?.active_notification_count) {
    alerts.push({
      description: `${data.community_snapshot.active_notification_count} reminder từ Community đang chờ.`,
      action: 'Xem reminder',
    })
  }
  return alerts
}

function goalStatusLabel(status) {
  if (status === 'due_soon') return 'Sắp đến hạn'
  if (status === 'off_track') return 'Đang lệch nhịp'
  return 'Đang theo dõi'
}

function marketOverviewStorageKey(sessionId) {
  return `public-beta.market_overview_completed.${sessionId}`
}

function hasCompletedMarketOverview(sessionId) {
  if (!sessionId) return false
  return window.localStorage.getItem(marketOverviewStorageKey(sessionId)) === '1'
}

function markMarketOverviewCompleted(sessionId) {
  if (!sessionId) return
  window.localStorage.setItem(marketOverviewStorageKey(sessionId), '1')
}

function isOnboardingIncompleteError(error) {
  return String(error || '').toLowerCase().includes('home is unavailable before onboarding')
}

function isInvalidSessionError(error) {
  const normalized = String(error || '').toLowerCase()
  return normalized.includes('unknown user session') || normalized.includes('not found') || normalized.includes('404')
}

function isHomePreviewError(error) {
  return isOnboardingIncompleteError(error) || isInvalidSessionError(error)
}
