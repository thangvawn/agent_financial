import {useEffect,useRef,useState} from 'react'
import {BookOpen} from 'lucide-react'

/** Decorative book sculpture; all reading and editing controls stay in the DOM. */
export default function ReaderDeskScene({enabled=true}) {
  const host=useRef(null)
  const [status,setStatus]=useState('loading')
  useEffect(()=>{
    if(!enabled)return
    let cancelled=false,dispose=()=>{}
    import('./readerDeskEngine').then(({createReaderDeskScene})=>{
      if(cancelled || !host.current)return
      dispose=createReaderDeskScene(host.current,value=>{if(!cancelled)setStatus(value)})
    }).catch(()=>{dispose();if(!cancelled)setStatus('fallback')})
    return()=>{cancelled=true;dispose()}
  },[enabled])
  const current=enabled?status:'off'
  return <div ref={host} className="br-desk-object" data-depth-state={current} aria-hidden="true">
    <div className="br-desk-object__fallback"><BookOpen size={32} strokeWidth={1.3}/></div>
  </div>
}
