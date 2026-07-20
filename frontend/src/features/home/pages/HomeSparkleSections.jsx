import { useEffect } from 'react'

export function SparkleAppCta({ actions }) {
  return (
    <section className="sparkle-app-cta sparkle-reveal" aria-label="Bắt đầu Northstar">
      <div>
        <h2>Một lab tài chính thông minh — không chỉ dashboard.</h2>
        <p>*Tập trung trải nghiệm, giải thích, dữ liệu và an toàn người học.</p>
        <div className="sparkle-hero-actions" style={{ justifyContent: 'flex-start', marginTop: 20 }}>
          <button type="button" className="sparkle-button sparkle-button--light" onClick={actions.primary}>
            {actions.primaryLabel}
          </button>
          <button type="button" className="sparkle-button sparkle-button--dark" onClick={actions.onOpenLearning}>
            Learn Hub
          </button>
        </div>
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

export function SparkleHighlights() {
  const quotes = [
    ['Learn Hub', 'Thư viện video, sách và tài liệu làm gốc kiến thức trước khi thực hành.'],
    ['News & Intelligence', 'Lọc tin, gắn mã và đọc nguồn — nối sang bài học khi cần.'],
    ['BCTC Analysis', 'Đọc báo cáo, so sánh peer và để AI giải thích chỉ số.'],
    ['Simulation Lab', 'Backtest, tua lịch sử và đo kỷ luật rủi ro trên dữ liệu quá khứ.'],
  ]
  const images = [
    'https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e719b9_duncan%20(1).jpg',
    'https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e71979_Screenshot_8%20(1).jpg',
    'https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e7197c_pexels-nishant-kumar-10939146.jpg',
    'https://cdn.prod.website-files.com/69f02d3c4b3f5ee193e718bd/69f02d3e4b3f5ee193e7197d_Screenshot_9.jpg',
  ]

  return (
    <section className="sparkle-testimonials sparkle-reveal" aria-label="Điểm nổi bật">
      <h2>Dự án có gì nổi bật?</h2>
      <div className="sparkle-testimonial-grid">
        {quotes.map(([name, quote], index) => (
          <article
            key={name}
            className="sparkle-testimonial-card sparkle-reveal"
            style={{ '--delay': `${index * 90}ms` }}
          >
            <img src={images[index]} alt="" />
            <strong>{name}</strong>
            <p>{quote}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

export function SparklePlans({ onOpen }) {
  return (
    <section className="sparkle-plans sparkle-reveal" aria-label="Hai lớp trải nghiệm">
      <div className="sparkle-section-heading">
        <h2>Hai lớp trải nghiệm trong lab.</h2>
        <p>Học & quan sát cho mọi người; Simulation Lab cho thực hành sâu hơn.</p>
      </div>
      <div className="sparkle-plan-grid">
        <article className="sparkle-plan-card">
          <span>Core</span>
          <h3>Learn & Observe</h3>
          <p>Onboarding, Learn Hub, News, BCTC và Market giấy cho người mới.</p>
          <ul>
            <li>Onboarding</li>
            <li>Learn Hub</li>
            <li>Market & News</li>
          </ul>
          <button type="button" className="sparkle-button sparkle-button--dark" onClick={onOpen.onOpenLearning}>
            Mở Learn Hub
          </button>
        </article>
        <article className="sparkle-plan-card sparkle-plan-card--dark">
          <span>Practice</span>
          <h3>Simulation Lab</h3>
          <p>Strategy builder, time skip / bar replay, kịch bản lịch sử và analytics.</p>
          <ul>
            <li>Backtest</li>
            <li>Scenarios</li>
            <li>Risk metrics</li>
          </ul>
          <button type="button" className="sparkle-button sparkle-button--light" onClick={onOpen.onOpenProLab}>
            Mở Simulation Lab
          </button>
        </article>
      </div>
    </section>
  )
}

export function useSparkleMotion() {
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
