import { useEffect, useRef } from 'react'
import * as THREE from 'three'

/**
 * Interactive 3D Canvas Stage that morphs between 4 sleek financial 3D objects 
 * based on the active showcase tab (`market_terminal`, `bctc_lab`, `backtest_studio`, `news_radar`).
 */
export default function Auth3DObjectCanvas({ activeTab = 'market_terminal' }) {
  const containerRef = useRef(null)
  const groupsRef = useRef({})
  const activeTabRef = useRef(activeTab)

  // Keep activeTabRef in sync
  useEffect(() => {
    activeTabRef.current = activeTab
  }, [activeTab])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return undefined

    const width = container.clientWidth || 500
    const height = container.clientHeight || 600

    // Scene setup
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
    camera.position.set(0, 0, 5)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setClearColor(0x000000, 0)
    container.appendChild(renderer.domElement)

    // Lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.6))
    
    const cyanLight = new THREE.PointLight(0x2dd4bf, 3, 20)
    cyanLight.position.set(3, 4, 5)
    scene.add(cyanLight)

    const indigoLight = new THREE.PointLight(0x818cf8, 2.5, 20)
    indigoLight.position.set(-4, -3, 3)
    scene.add(indigoLight)

    const topDirLight = new THREE.DirectionalLight(0xffffff, 1)
    topDirLight.position.set(0, 5, 5)
    scene.add(topDirLight)

    // Main Stage Root
    const stageRoot = new THREE.Group()
    scene.add(stageRoot)

    // -------------------------------------------------------------
    // Object 01: Market Terminal (Glass Globe + Dual Torus Rings)
    // -------------------------------------------------------------
    const marketGroup = new THREE.Group()
    
    const globeGeo = new THREE.IcosahedronGeometry(1.2, 2)
    const globeMat = new THREE.MeshStandardMaterial({
      color: 0x0f766e,
      emissive: 0x115e59,
      emissiveIntensity: 0.6,
      wireframe: true,
      transparent: true,
      opacity: 0.85,
    })
    const marketGlobe = new THREE.Mesh(globeGeo, globeMat)
    marketGroup.add(marketGlobe)

    const ring1Geo = new THREE.TorusGeometry(1.8, 0.02, 16, 100)
    const ring1Mat = new THREE.MeshStandardMaterial({
      color: 0x2dd4bf,
      emissive: 0x0d9488,
      emissiveIntensity: 0.8,
      roughness: 0.2,
    })
    const marketRing1 = new THREE.Mesh(ring1Geo, ring1Mat)
    marketRing1.rotation.x = Math.PI / 3
    marketGroup.add(marketRing1)

    const ring2Geo = new THREE.TorusGeometry(2.2, 0.015, 16, 100)
    const ring2Mat = new THREE.MeshStandardMaterial({
      color: 0x818cf8,
      emissive: 0x4f46e5,
      emissiveIntensity: 0.7,
      roughness: 0.2,
    })
    const marketRing2 = new THREE.Mesh(ring2Geo, ring2Mat)
    marketRing2.rotation.x = -Math.PI / 4
    marketRing2.rotation.y = Math.PI / 6
    marketGroup.add(marketRing2)

    stageRoot.add(marketGroup)
    groupsRef.current.market_terminal = marketGroup

    // -------------------------------------------------------------
    // Object 02: BCTC Lab (Hexagonal Financial Column Stack)
    // -------------------------------------------------------------
    const bctcGroup = new THREE.Group()
    
    const hexCount = 7
    for (let i = 0; i < hexCount; i++) {
      const angle = (i / hexCount) * Math.PI * 2
      const radius = i === 0 ? 0 : 0.95
      const h = i === 0 ? 1.8 : 0.6 + Math.abs(Math.sin(i * 1.5)) * 0.9
      const hexGeo = new THREE.CylinderGeometry(0.35, 0.35, h, 6)
      const hexMat = new THREE.MeshStandardMaterial({
        color: i === 0 ? 0x2dd4bf : 0x3b82f6,
        emissive: i === 0 ? 0x0f766e : 0x1e3a8a,
        emissiveIntensity: 0.5,
        roughness: 0.2,
        metalness: 0.7,
      })
      const hexMesh = new THREE.Mesh(hexGeo, hexMat)
      const x = i === 0 ? 0 : Math.cos(angle) * radius
      const z = i === 0 ? 0 : Math.sin(angle) * radius
      hexMesh.position.set(x, (h / 2) - 0.9, z)
      bctcGroup.add(hexMesh)
    }

    stageRoot.add(bctcGroup)
    groupsRef.current.bctc_lab = bctcGroup

    // -------------------------------------------------------------
    // Object 03: Backtest Studio (Double-Helix Quantum Wave)
    // -------------------------------------------------------------
    const backtestGroup = new THREE.Group()
    
    const helixPoints = []
    const numHelix = 80
    for (let i = 0; i < numHelix; i++) {
      const t = (i / numHelix) * Math.PI * 4
      const x = Math.sin(t) * 1.1
      const y = (i / numHelix) * 3 - 1.5
      const z = Math.cos(t) * 1.1
      helixPoints.push(new THREE.Vector3(x, y, z))
    }

    const helixCurve = new THREE.CatmullRomCurve3(helixPoints)
    const helixTubeGeo = new THREE.TubeGeometry(helixCurve, 64, 0.04, 8, false)
    const helixTubeMat = new THREE.MeshStandardMaterial({
      color: 0x818cf8,
      emissive: 0x6366f1,
      emissiveIntensity: 0.9,
      roughness: 0.1,
      metalness: 0.8,
    })
    const helixMesh = new THREE.Mesh(helixTubeGeo, helixTubeMat)
    backtestGroup.add(helixMesh)

    // Monte Carlo Node Spheres
    const nodeGeo = new THREE.SphereGeometry(0.07, 12, 12)
    const nodeMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
    helixPoints.forEach((pt, idx) => {
      if (idx % 6 === 0) {
        const sphere = new THREE.Mesh(nodeGeo, nodeMat)
        sphere.position.copy(pt)
        backtestGroup.add(sphere)
      }
    })

    stageRoot.add(backtestGroup)
    groupsRef.current.backtest_studio = backtestGroup

    // -------------------------------------------------------------
    // Object 04: AI News Radar (Holographic Core & Concentric Beacons)
    // -------------------------------------------------------------
    const radarGroup = new THREE.Group()

    const coreSphereGeo = new THREE.SphereGeometry(0.7, 24, 24)
    const coreSphereMat = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      emissive: 0xd97706,
      emissiveIntensity: 0.8,
      roughness: 0.1,
    })
    const radarCore = new THREE.Mesh(coreSphereGeo, coreSphereMat)
    radarGroup.add(radarCore)

    // Concentric Wave Rings
    for (let r = 1; r <= 3; r++) {
      const waveGeo = new THREE.RingGeometry(r * 0.7, r * 0.7 + 0.04, 32)
      const waveMat = new THREE.MeshBasicMaterial({
        color: 0xfbbf24,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.5 - r * 0.1,
      })
      const waveMesh = new THREE.Mesh(waveGeo, waveMat)
      waveMesh.rotation.x = Math.PI / 2
      radarGroup.add(waveMesh)
    }

    stageRoot.add(radarGroup)
    groupsRef.current.news_radar = radarGroup

    // -------------------------------------------------------------
    // Floating Background Particle Cloud
    // -------------------------------------------------------------
    const particleCount = 140
    const particleGeo = new THREE.BufferGeometry()
    const particlePos = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePos[i] = (Math.random() - 0.5) * 8
      particlePos[i + 1] = (Math.random() - 0.5) * 6
      particlePos[i + 2] = (Math.random() - 0.5) * 6
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3))

    const particleMat = new THREE.PointsMaterial({
      color: 0x5eead4,
      size: 0.03,
      transparent: true,
      opacity: 0.45,
    })
    const particleCloud = new THREE.Points(particleGeo, particleMat)
    scene.add(particleCloud)

    // Initial opacity settings
    Object.keys(groupsRef.current).forEach((key) => {
      const g = groupsRef.current[key]
      g.visible = true
      g.scale.setScalar(key === activeTabRef.current ? 1 : 0.001)
    })

    // Mouse Parallax Interaction
    let mouseX = 0
    let mouseY = 0
    let targetX = 0
    let targetY = 0

    function handleMouseMove(e) {
      const rect = container.getBoundingClientRect()
      targetX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.35
      targetY = ((e.clientY - rect.top) / rect.height - 0.5) * 0.25
    }
    container.addEventListener('mousemove', handleMouseMove)

    // Animation Loop
    let animationFrameId
    const clock = new THREE.Clock()

    function animateLoop() {
      animationFrameId = requestAnimationFrame(animateLoop)
      const elapsedTime = clock.getElapsedTime()
      const currentTab = activeTabRef.current

      // Lerp mouse smooth
      mouseX += (targetX - mouseX) * 0.05
      mouseY += (targetY - mouseY) * 0.05

      stageRoot.rotation.y = elapsedTime * 0.25 + mouseX
      stageRoot.rotation.x = 0.15 + mouseY

      // Morph scale lerp between active and inactive 3D objects
      Object.keys(groupsRef.current).forEach((key) => {
        const group = groupsRef.current[key]
        const isTarget = key === currentTab
        const targetScale = isTarget ? 1 : 0.001
        
        group.scale.x += (targetScale - group.scale.x) * 0.08
        group.scale.y += (targetScale - group.scale.y) * 0.08
        group.scale.z += (targetScale - group.scale.z) * 0.08

        // Specific sub-animations
        if (key === 'market_terminal') {
          marketRing1.rotation.z = elapsedTime * 0.4
          marketRing2.rotation.z = -elapsedTime * 0.3
        } else if (key === 'bctc_lab') {
          bctcGroup.children.forEach((child, idx) => {
            child.position.y = (child.geometry.parameters.height / 2) - 0.9 + Math.sin(elapsedTime * 2 + idx) * 0.06
          })
        } else if (key === 'backtest_studio') {
          backtestGroup.rotation.y = elapsedTime * 0.3
        } else if (key === 'news_radar') {
          radarCore.rotation.y = elapsedTime * 0.5
        }
      })

      particleCloud.rotation.y = elapsedTime * 0.04

      renderer.render(scene, camera)
    }

    animateLoop()

    // Resize listener
    function handleResize() {
      if (!container) return
      const w = container.clientWidth
      const h = container.clientHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(animationFrameId)
      container.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('resize', handleResize)
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className="w-full h-full min-h-[300px] relative cursor-grab active:cursor-grabbing flex items-center justify-center pointer-events-auto"
      aria-label="Interactive 3D Stage"
    />
  )
}
