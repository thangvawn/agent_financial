import { useEffect, useRef } from 'react'

const PARTICLE_COUNT = 92
const MAX_DPR = 1.5

function createParticle(index) {
  const seed = (index * 9301 + 49297) % 233280
  const random = seed / 233280
  return {
    x: (random - 0.5) * 2.2,
    y: ((index * 0.6180339887) % 1 - 0.5) * 1.35,
    z: 0.15 + ((index * 0.754877666) % 1) * 1.35,
    drift: ((index % 7) - 3) * 0.00012,
  }
}

export default function FinanceParticleField() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const container = canvas?.parentElement
    if (!canvas || !container) return undefined

    const context = canvas.getContext('2d', { alpha: true })
    if (!context) return undefined

    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const particles = Array.from({ length: PARTICLE_COUNT }, (_, index) => createParticle(index))
    const pointer = { x: 0, y: 0 }
    let width = 1
    let height = 1
    let frameId = 0
    let visible = true

    function resize() {
      const rect = container.getBoundingClientRect()
      const dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR)
      width = Math.max(1, rect.width)
      height = Math.max(1, rect.height)
      canvas.width = Math.round(width * dpr)
      canvas.height = Math.round(height * dpr)
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
      context.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    function draw() {
      context.clearRect(0, 0, width, height)
      const projected = particles.map((particle) => {
        const depth = 1 / particle.z
        return {
          x: width * 0.52 + (particle.x + pointer.x * 0.04) * width * 0.28 * depth,
          y: height * 0.5 + (particle.y + pointer.y * 0.04) * height * 0.44 * depth,
          radius: Math.max(0.65, 1.8 * depth),
          depth,
        }
      })

      projected.forEach((point, index) => {
        const nearest = projected[(index + 7) % projected.length]
        const distance = Math.hypot(point.x - nearest.x, point.y - nearest.y)
        if (distance < 82) {
          context.strokeStyle = `rgba(139, 233, 221, ${Math.max(0, 0.14 - distance / 700)})`
          context.lineWidth = 0.7
          context.beginPath()
          context.moveTo(point.x, point.y)
          context.lineTo(nearest.x, nearest.y)
          context.stroke()
        }

        const glow = context.createRadialGradient(point.x, point.y, 0, point.x, point.y, point.radius * 4)
        glow.addColorStop(0, `rgba(219, 255, 247, ${0.72 * point.depth})`)
        glow.addColorStop(1, 'rgba(52, 211, 191, 0)')
        context.fillStyle = glow
        context.beginPath()
        context.arc(point.x, point.y, point.radius * 4, 0, Math.PI * 2)
        context.fill()
        context.fillStyle = `rgba(226, 255, 249, ${Math.min(0.86, 0.28 + point.depth * 0.35)})`
        context.beginPath()
        context.arc(point.x, point.y, point.radius, 0, Math.PI * 2)
        context.fill()
      })
    }

    function animate() {
      if (!visible) return
      particles.forEach((particle) => {
        particle.z += particle.drift
        if (particle.z > 1.5 || particle.z < 0.12) particle.drift *= -1
      })
      draw()
      frameId = window.requestAnimationFrame(animate)
    }

    function handlePointerMove(event) {
      const rect = container.getBoundingClientRect()
      pointer.x = ((event.clientX - rect.left) / rect.width - 0.5) * 2
      pointer.y = ((event.clientY - rect.top) / rect.height - 0.5) * 2
    }

    const resizeObserver = new ResizeObserver(resize)
    const visibilityObserver = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting
      if (visible && !reducedMotion) {
        window.cancelAnimationFrame(frameId)
        frameId = window.requestAnimationFrame(animate)
      }
    }, { threshold: 0.02 })

    resizeObserver.observe(container)
    visibilityObserver.observe(container)
    container.addEventListener('pointermove', handlePointerMove, { passive: true })
    resize()
    draw()
    if (!reducedMotion) frameId = window.requestAnimationFrame(animate)

    return () => {
      window.cancelAnimationFrame(frameId)
      resizeObserver.disconnect()
      visibilityObserver.disconnect()
      container.removeEventListener('pointermove', handlePointerMove)
    }
  }, [])

  return <canvas ref={canvasRef} className="finance-particle-field" aria-hidden="true" />
}
