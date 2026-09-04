import { useEffect } from 'react'

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

