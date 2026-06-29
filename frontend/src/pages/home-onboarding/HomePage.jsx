import { useEffect, useState } from 'react'

import { useHome } from '../../modules/home-onboarding'
import './home.css'

const shellClass = 'home-redesign'
const panelClass = 'home-v2-panel'
const kickerClass = 'home-v2-kicker'

export default function HomePage({
  sessionId,
  refreshKey = 0,
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

  if (isLoading) return <HomeLoadingState />

  if (!sessionId || isHomePreviewError(error)) {
    return (
      <HomeExperience
        data={null}
        sessionId={sessionId || 'guest'}
        marketReady={marketReady}
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
    />
  )
}

function HomeExperience({
  data,
  marketReady,
}) {
  const homeState = buildHomeState(data, marketReady)
  useSparkleMotion()

  return (
    <section className={`${shellClass} sparkle-home`}>
      <SparkleHero state={homeState} />

      <SparkleClientStrip />

      <SparkleDemoFlow />

      <SparkleFeatureGrid state={homeState} />

      <SparkleAppCta />

      <SparkleTestimonials state={homeState} />

      <SparklePlans proEligible={homeState.proEligible} />
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
      description: 'Onboarding và Learn Hub tạo bối cảnh trước khi hệ thống đưa ra bước tiếp theo.',
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

function SparkleHero({ state }) {
  return (
    <section className="sparkle-hero" aria-label="Northstar Finance hero">
      <div className="sparkle-hero-copy">
        <p className={kickerClass}>Northstar Finance Demo</p>
        <h1>AI Agent tài chính cho người dùng Việt Nam.</h1>
        <p>
          Một nền tảng demo kết hợp onboarding, học tập, phân tích BCTC, tin tức và dữ liệu thị trường để giúp người dùng hiểu tiền tốt hơn trước khi ra quyết định.
        </p>
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
  const brands = ['AI Assistant', 'Learn Hub', 'Global Terminal', 'BCTC Analysis', 'Pro Lab']
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
}) {
  return (
    <section className="sparkle-features" aria-label="Northstar features">
      <div className="sparkle-feature-copy sparkle-reveal">
        <h2>Một demo end-to-end cho hành trình tài chính cá nhân.</h2>
        <p>
          Người dùng đi từ hiểu bản thân, đặt mục tiêu, học kiến thức nền, đọc bối cảnh thị trường, đến phân tích doanh nghiệp theo cách có kiểm soát rủi ro.
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
          alt="Financial health preview"
        />
      </div>
      <div className="sparkle-feature-copy sparkle-reveal">
        <h2>AI không chỉ chat, mà điều phối nhiều module.</h2>
        <p>
          Trợ lý có thể định tuyến câu hỏi sang financial coach, learning tutor, market analyst hoặc BCTC analyst. Luồng hiện tại: {state.healthReady ? 'đã có baseline để cá nhân hóa' : 'bắt đầu bằng baseline để cá nhân hóa'}.
        </p>
        <div className="sparkle-check-list">
          <span>Learning path theo trình độ</span>
          <span>Phân tích BCTC và peer</span>
          <span>Dữ liệu thị trường có ngữ cảnh</span>
        </div>
      </div>
      <div className="sparkle-feature-copy sparkle-reveal">
        <h2>Điểm nổi bật: an toàn, giải thích được, có dữ liệu.</h2>
        <p>
          Dự án ưu tiên giải thích và giáo dục tài chính, không phím hàng. Các quyết định được hỗ trợ bằng dữ liệu, guardrails và luồng kiểm tra phù hợp từng mức độ người dùng.
        </p>
      </div>
      <div className="sparkle-feature-visual sparkle-feature-visual--three sparkle-reveal">
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719ab_639d70c46affc08126525de0_div-min.png"
          alt="Portfolio review preview"
        />
      </div>
    </section>
  )
}

function SparkleAppCta() {
  return (
    <section className="sparkle-app-cta sparkle-reveal" aria-label="Start Northstar">
      <div>
        <h2>Demo một sản phẩm tài chính thông minh, không chỉ là dashboard.</h2>
        <p>*Tập trung vào trải nghiệm, giải thích, dữ liệu và an toàn người dùng.</p>
      </div>
      <div className="sparkle-phone-preview">
        <img
          src="https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719ac_639d70c3406f2fc42c88caee_Frame%203868-min.png"
          alt="Learning app preview"
        />
      </div>
    </section>
  )
}

function SparkleTestimonials({ state }) {
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
          <article key={name} className="sparkle-testimonial-card sparkle-reveal" style={{ '--delay': `${index * 90}ms` }}>
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
          </article>
        ))}
      </div>
    </section>
  )
}

function SparklePlans({ proEligible }) {
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
          <p>Onboarding, learning, assistant và market explanation cho người dùng phổ thông.</p>
          <ul>
            <li>Onboarding</li>
            <li>Learn Hub</li>
            <li>Market Explanation</li>
          </ul>
        </article>
        <article className="sparkle-plan-card sparkle-plan-card--dark">
          <span>{proEligible ? 'Unlocked' : 'Advanced'}</span>
          <h3>Research Lab</h3>
          <p>Backtest, scenario, blueprint, experiment log và không gian nghiên cứu tách khỏi luồng public.</p>
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
  const community = data?.community_snapshot
  const alerts = buildFriendlyAlerts(data, marketReady)

  return {
    isPersonalized: Boolean(data),
    marketReady,
    healthReady: Boolean(health),
    proEligible: Boolean(data?.pro_eligible),
    alertCount: alerts.length,
    personalLabel: data ? 'Home đã cá nhân hóa' : 'Chế độ khám phá',
    personalMessage: data
      ? 'Bạn có thể nối Learn và Market để xem bước phù hợp tiếp theo.'
      : 'Hoàn tất onboarding để mở gợi ý học tập phù hợp hơn.',
    healthStatus: health ? 'Đã có baseline' : 'Chưa có đánh giá',
    healthDescription: health?.summary || 'Cần vài câu hỏi để hiểu dòng tiền, dự phòng và sức chịu rủi ro.',
    healthAction: health ? 'Xem lại baseline' : 'Trả lời 5 câu hỏi',
    healthSummary: health?.summary || '',
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
      description: 'Chưa có đủ dữ liệu onboarding nên Home chưa nên cá nhân hóa sâu.',
      action: 'Hoàn tất hồ sơ',
    })
  }
  if (!marketReady) {
    alerts.push({
      description: 'Bạn chưa tương tác với chart thị trường trong Home.',
      action: 'Xem bối cảnh thị trường',
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

function marketOverviewStorageKey(sessionId) {
  return `public-beta.market_overview_completed.${sessionId}`
}

function hasCompletedMarketOverview(sessionId) {
  if (!sessionId) return false
  return window.localStorage.getItem(marketOverviewStorageKey(sessionId)) === '1'
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
