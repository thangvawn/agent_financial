import * as THREE from 'three'
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js'

// Isolated lazy-loaded engine; no perpetual render loop or React frame updates.
export function createReaderDeskScene(container,setStatus) {
let cancelled=false,dispose=()=>{}
const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'})
let frame=0,lost=false
const scene=new THREE.Scene()
const camera=new THREE.PerspectiveCamera(32,1,.1,30)
camera.position.set(4.5,4.2,6.6);camera.lookAt(0,.2,0)
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1,1.5))
renderer.outputColorSpace=THREE.SRGBColorSpace
renderer.toneMapping=THREE.ACESFilmicToneMapping
renderer.toneMappingExposure=1.35
renderer.shadowMap.enabled=true
renderer.shadowMap.type=THREE.PCFSoftShadowMap
const canvas=renderer.domElement
canvas.setAttribute('aria-hidden','true')
container.appendChild(canvas)
scene.add(new THREE.HemisphereLight(0xe9fff7,0x163c37,2.3))
const light=new THREE.DirectionalLight(0xffffff,4)
light.position.set(-3,6,4);light.castShadow=true
light.shadow.mapSize.set(512,512)
light.shadow.camera.left=-4;light.shadow.camera.right=4
light.shadow.camera.top=4;light.shadow.camera.bottom=-4
light.shadow.bias=-.001
scene.add(light)
const rim=new THREE.DirectionalLight(0x84cbb8,2)
rim.position.set(4,2,-3);scene.add(rim)
const books=new THREE.Group();scene.add(books)
function box(parent,size,position,color,roughness=.65) {
  const mesh=new THREE.Mesh(new RoundedBoxGeometry(...size,2,.035),new THREE.MeshStandardMaterial({color,roughness,metalness:.08}))
  mesh.position.set(...position);mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh)
  return mesh
}
function book(y,angle,cover) {
  const group=new THREE.Group();group.position.y=y;group.rotation.y=angle;books.add(group)
  box(group,[2.7,.055,1.8],[0,0,0],cover)
  box(group,[2.57,.23,1.67],[.015,.14,0],0xe8e9df)
  box(group,[2.7,.065,1.8],[0,.29,0],cover)
  box(group,[.1,.3,1.8],[-1.3,.14,0],cover)
  for(let i=0;i<5;i++)box(group,[2.5,.006,.014],[.02,.06+i*.035,.839],0xb7c4bc)
  box(group,[1.08,.009,.065],[-.25,.327,-.25],0xc8dfd2)
  box(group,[.73,.009,.035],[-.42,.327,-.07],0xc8dfd2)
  box(group,[.22,.016,.55],[.75,.33,.65],0xd9e6d7)
}
book(-.16,.15,0x1d5751);book(.2,-.22,0x548f80)
const ground=new THREE.Mesh(new THREE.PlaneGeometry(12,12),new THREE.ShadowMaterial({opacity:.3}))
ground.rotation.x=-Math.PI/2;ground.position.y=-.2;ground.receiveShadow=true;scene.add(ground)
const motion=window.matchMedia('(prefers-reduced-motion: reduce)')
let targetX=0,targetY=.1
books.rotation.y=targetY
function render() {
  frame=0
  if(cancelled || lost || document.hidden)return
  const reduced=motion.matches
  books.rotation.x += ((reduced?0:targetX)-books.rotation.x)*.12
  books.rotation.y += ((reduced ? .1 : targetY)-books.rotation.y)*.12
  renderer.render(scene,camera)
  if(!reduced && Math.abs(books.rotation.x-targetX)+Math.abs(books.rotation.y-targetY)>.001)frame=requestAnimationFrame(render)
}
function schedule(){if(!frame && !cancelled && !lost && !document.hidden)frame=requestAnimationFrame(render)}
function resize(){const {width,height}=container.getBoundingClientRect();if(!width || !height)return;renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();schedule()}
const header=container.closest('header')
function pointer(event){if(motion.matches)return;const rect=header.getBoundingClientRect();targetY=.1+((event.clientX-rect.left)/rect.width-.5)*.4;targetX=((event.clientY-rect.top)/rect.height-.5)*.12;schedule()}
function leave(){targetX=0;targetY=.1;schedule()}
function visibility(){if(document.hidden){cancelAnimationFrame(frame);frame=0}else schedule()}
function lostContext(event){event.preventDefault();lost=true;cancelAnimationFrame(frame);frame=0;canvas.style.visibility='hidden';setStatus('fallback')}
function restoredContext(){lost=false;canvas.style.visibility='';setStatus('ready');schedule()}
const observer=new ResizeObserver(resize);observer.observe(container)
header?.addEventListener('pointermove',pointer,{passive:true})
header?.addEventListener('pointerleave',leave)
document.addEventListener('visibilitychange',visibility)
motion.addEventListener('change',schedule)
canvas.addEventListener('webglcontextlost',lostContext)
canvas.addEventListener('webglcontextrestored',restoredContext)
dispose=()=>{
  cancelled=true;
  cancelAnimationFrame(frame);observer.disconnect()
  header?.removeEventListener('pointermove',pointer);header?.removeEventListener('pointerleave',leave)
  document.removeEventListener('visibilitychange',visibility);motion.removeEventListener('change',schedule)
  canvas.removeEventListener('webglcontextlost',lostContext);canvas.removeEventListener('webglcontextrestored',restoredContext)
  const geometries=new Set(),materials=new Set()
  scene.traverse(object=>{if(object.geometry)geometries.add(object.geometry);if(object.material)materials.add(object.material)})
  geometries.forEach(geometry=>geometry.dispose());materials.forEach(material=>material.dispose())
  light.shadow.map?.dispose();renderer.dispose();renderer.forceContextLoss();canvas.remove()
}
resize();setStatus('ready')
return dispose
}
