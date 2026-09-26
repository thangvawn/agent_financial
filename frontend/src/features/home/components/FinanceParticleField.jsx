import { useEffect, useRef } from 'react'

const SPHERE_POINTS = 168
const AMBIENT_POINTS = 44
const MAX_DPR = 1.5

function createSpherePoint(index) {
  const goldenAngle = Math.PI * (3 - Math.sqrt(5))
  const y = 1 - (index / (SPHERE_POINTS - 1)) * 2
  const radius = Math.sqrt(Math.max(0, 1 - y * y))
  const angle = goldenAngle * index
  return {
    x: Math.cos(angle) * radius,
    y,
    z: Math.sin(angle) * radius,
    phase: (index % 13) / 13,
  }
}

function createAmbientPoint(index) {
  const seed = (index * 9301 + 49297) % 233280
  const random = seed / 233280
  return {
    x: random,
    y: ((index * 0.6180339887) % 1),
    depth: 0.28 + ((index * 0.754877666) % 1) * 0.72,
  }
}

function rotatePoint(point, rotation, pointer) {
  const yaw = rotation + pointer.x * 0.16
  const pitch = pointer.y * 0.12
  const cosYaw = Math.cos(yaw)
  const sinYaw = Math.sin(yaw)
  const x = point.x * cosYaw - point.z * sinYaw
  const z = point.x * sinYaw + point.z * cosYaw
  const cosPitch = Math.cos(pitch)
  const sinPitch = Math.sin(pitch)
  return {
    x,
    y: point.y * cosPitch - z * sinPitch,
    z: point.y * sinPitch + z * cosPitch,
    phase: point.phase,
  }
}

function drawDataCard(context, centerX, centerY, radius, rotation, opacity) {
  const cardWidth = radius * 1.72
  const cardHeight = radius * 1.05
  const tilt = -0.16 + rotation * 0.08
  const halfWidth = cardWidth / 2
  const halfHeight = cardHeight / 2

  context.save()
  context.translate(centerX + radius * 0.03, centerY - radius * 0.02)
  context.rotate(tilt)
  context.globalAlpha = opacity
  context.shadowColor = 'rgba(0, 0, 0, 0.52)'
  context.shadowBlur = radius * 0.18
  context.shadowOffsetY = radius * 0.06

  const cardGradient = context.createLinearGradient(-halfWidth, -halfHeight, halfWidth, halfHeight)
  cardGradient.addColorStop(0, '#eef8f4')
  cardGradient.addColorStop(0.42, '#9fbdb7')
  cardGradient.addColorStop(0.7, '#476b68')
  cardGradient.addColorStop(1, '#183b3d')
  context.fillStyle = cardGradient
  context.beginPath()
  context.roundRect(-halfWidth, -halfHeight, cardWidth, cardHeight, radius * 0.06)
  context.fill()

  context.shadowBlur = 0
  context.strokeStyle = 'rgba(239, 255, 249, 0.62)'
  context.lineWidth = 1
  context.stroke()

  context.save()
  context.beginPath()
  context.roundRect(-halfWidth, -halfHeight, cardWidth, cardHeight, radius * 0.06)
  context.clip()
  const light = context.createLinearGradient(-halfWidth, halfHeight, halfWidth, -halfHeight)
  light.addColorStop(0, 'rgba(255, 255, 255, 0)')
  light.addColorStop(0.48, 'rgba(230, 255, 247, 0.12)')
  light.addColorStop(0.56, 'rgba(255, 255, 255, 0.5)')
  light.addColorStop(0.64, 'rgba(255, 255, 255, 0)')
  context.fillStyle = light
  context.fillRect(-halfWidth, -halfHeight, cardWidth, cardHeight)
  context.restore()

  context.fillStyle = 'rgba(7, 29, 31, 0.76)'
  context.font = `600 ${Math.max(9, radius * 0.085)}px ui-monospace, SFMono-Regular, Menlo, monospace`
  context.fillText('NORTHSTAR / 01', -halfWidth + radius * 0.14, -halfHeight + radius * 0.2)
  context.font = `500 ${Math.max(8, radius * 0.065)}px ui-monospace, SFMono-Regular, Menlo, monospace`
  context.fillText('EDUCATIONAL MODE', -halfWidth + radius * 0.14, halfHeight - radius * 0.14)

  context.fillStyle = 'rgba(8, 35, 36, 0.8)'
  context.beginPath()
  context.roundRect(-halfWidth + radius * 0.14, -radius * 0.04, radius * 0.38, radius * 0.24, radius * 0.025)
  context.fill()

  context.fillStyle = 'rgba(236, 255, 247, 0.92)'
  context.font = `700 ${Math.max(12, radius * 0.14)}px ui-sans-serif, system-ui, sans-serif`
  context.fillText('1,284.32', -halfWidth + radius * 0.14, radius * 0.27)
  context.restore()
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
    const sphere = Array.from({ length: SPHERE_POINTS }, (_, index) => createSpherePoint(index))
    const ambient = Array.from({ length: AMBIENT_POINTS }, (_, index) => createAmbientPoint(index))
    const pointer = { x: 0, y: 0 }
    let width = 1
    let height = 1
    let frameId = 0
    let visible = true
    let startTime = performance.now()

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

    function draw(timestamp = startTime) {
      const elapsed = (timestamp - startTime) / 1000
      context.clearRect(0, 0, width, height)

      ambient.forEach((point, index) => {
        const x = point.x * width
        const y = point.y * height
        const pulse = 0.5 + Math.sin(elapsed * 0.7 + index) * 0.5
        context.fillStyle = `rgba(157, 245, 231, ${0.06 + pulse * 0.08 * point.depth})`
        context.beginPath()
        context.arc(x, y, 0.7 + point.depth * 1.2, 0, Math.PI * 2)
        context.fill()
      })

      const centerX = width * (width < 720 ? 0.72 : 0.74) + pointer.x * width * 0.018
      const mobileStage = width < 720
      const centerY = height * (mobileStage ? 0.31 : 0.52) + pointer.y * height * 0.018
      const sphereRadius = Math.min(width * (mobileStage ? 0.3 : 0.25), height * (mobileStage ? 0.58 : 0.46))

      const aura = context.createRadialGradient(centerX, centerY, 0, centerX, centerY, sphereRadius * 1.25)
      aura.addColorStop(0, 'rgba(55, 224, 201, 0.16)')
      aura.addColorStop(0.52, 'rgba(25, 154, 147, 0.08)')
      aura.addColorStop(1, 'rgba(7, 20, 25, 0)')
      context.fillStyle = aura
      context.beginPath()
      context.arc(centerX, centerY, sphereRadius * 1.25, 0, Math.PI * 2)
      context.fill()

      const rotation = reducedMotion ? 0.24 : elapsed * 0.14
      const projected = sphere.map((point) => {
        const rotated = rotatePoint(point, rotation, pointer)
        const depth = 1.12 / (1.9 - rotated.z)
        return {
          x: centerX + rotated.x * sphereRadius * depth,
          y: centerY + rotated.y * sphereRadius * depth,
          z: rotated.z,
          depth,
          phase: rotated.phase,
        }
      }).sort((first, second) => first.z - second.z)

      context.save()
      context.beginPath()
      context.arc(centerX, centerY, sphereRadius * 1.03, 0, Math.PI * 2)
      context.clip()

      projected.forEach((point, index) => {
        const next = projected[(index + 9) % projected.length]
        const distance = Math.hypot(point.x - next.x, point.y - next.y)
        if (distance < sphereRadius * 0.22 && point.z > -0.4) {
          const alpha = Math.max(0.015, 0.13 * (point.z + 0.65))
          context.strokeStyle = `rgba(139, 239, 225, ${alpha})`
          context.lineWidth = 0.65 + point.depth * 0.35
          context.beginPath()
          context.moveTo(point.x, point.y)
          context.lineTo(next.x, next.y)
          context.stroke()
        }
      })

      projected.forEach((point, index) => {
        const pulse = 0.5 + Math.sin(elapsed * 1.35 + point.phase * Math.PI * 2 + index) * 0.5
        const radius = Math.max(0.7, (1.1 + pulse * 1.25) * point.depth)
        context.fillStyle = `rgba(218, 255, 248, ${Math.min(0.96, 0.38 + point.depth * 0.54)})`
        context.beginPath()
        context.arc(point.x, point.y, radius, 0, Math.PI * 2)
        context.fill()
      })
      context.restore()

      context.save()
      context.translate(centerX, centerY)
      context.rotate(rotation * 0.45 + pointer.x * 0.08)
      context.strokeStyle = 'rgba(130, 240, 224, 0.42)'
      context.lineWidth = 1.15
      context.setLineDash([3, 9])
      context.beginPath()
      context.ellipse(0, 0, sphereRadius * 1.07, sphereRadius * 0.34, 0, 0, Math.PI * 2)
      context.stroke()
      context.setLineDash([])
      context.strokeStyle = 'rgba(137, 247, 231, 0.28)'
      context.lineWidth = 0.8
      context.beginPath()
      context.arc(0, 0, sphereRadius * 0.98, 0, Math.PI * 2)
      context.stroke()
      context.beginPath()
      context.ellipse(0, 0, sphereRadius * 0.46, sphereRadius * 0.98, 0, 0, Math.PI * 2)
      context.stroke()
      context.beginPath()
      context.ellipse(0, 0, sphereRadius * 0.76, sphereRadius * 0.98, 0, 0, Math.PI * 2)
      context.stroke()
      context.rotate(Math.PI / 3)
      context.strokeStyle = 'rgba(130, 240, 224, 0.22)'
      context.beginPath()
      context.ellipse(0, 0, sphereRadius * 1.02, sphereRadius * 0.3, 0, 0, Math.PI * 2)
      context.stroke()
      context.restore()

      context.strokeStyle = 'rgba(222, 255, 248, 0.34)'
      context.lineWidth = 0.7
      context.beginPath()
      context.moveTo(centerX - sphereRadius * 0.14, centerY)
      context.lineTo(centerX + sphereRadius * 0.14, centerY)
      context.moveTo(centerX, centerY - sphereRadius * 0.14)
      context.lineTo(centerX, centerY + sphereRadius * 0.14)
      context.stroke()
      context.fillStyle = 'rgba(218, 255, 248, 0.96)'
      context.beginPath()
      context.arc(centerX, centerY, 2.6, 0, Math.PI * 2)
      context.fill()

      const signalAngle = elapsed * 0.65
      const signalX = centerX + Math.cos(signalAngle) * sphereRadius * 1.12
      const signalY = centerY + Math.sin(signalAngle) * sphereRadius * 0.36
      context.fillStyle = 'rgba(255, 231, 154, 0.96)'
      context.shadowColor = 'rgba(255, 221, 130, 0.9)'
      context.shadowBlur = 14
      context.beginPath()
      context.arc(signalX, signalY, 2.4, 0, Math.PI * 2)
      context.fill()
      context.shadowBlur = 0

      context.strokeStyle = 'rgba(167, 241, 228, 0.44)'
      context.lineWidth = 1.15
      context.beginPath()
      context.arc(centerX, centerY, sphereRadius * 0.94, -0.52, 0.32)
      context.stroke()

      // A premium card-like data object sits in front of the particle globe,
      // echoing Moto's singular 3D product object without copying its asset.
      drawDataCard(context, centerX, centerY, sphereRadius, rotation, reducedMotion ? 0.76 : 0.82)
    }

    function animate(timestamp) {
      if (!visible) return
      draw(timestamp)
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
        startTime = performance.now()
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
