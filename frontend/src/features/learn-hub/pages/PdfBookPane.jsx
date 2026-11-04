import {useEffect,useState} from 'react'
import {loadBookDocument,rememberBookLoadFailure} from '../services/bookAvailability'

export function PdfBookPane({source,title,onReady,initialPage=1}) {
  return <DocumentFilePane source={{...source,kind:'pdf'}} title={title} onReady={onReady} initialPage={initialPage} />
}
export function DocumentFilePane({source,title,onReady,initialPage=1}) {
  const [nonce,setNonce]=useState(0)
  const scope=`${source.viewUrl}:${source.kind}:${nonce}`
  const [loaded,setLoaded]=useState(null)
  useEffect(()=>{
    const controller=new AbortController();let objectUrl=''
    loadBookDocument({viewUrl:source.viewUrl,kind:source.kind},{signal:controller.signal}).then(result=>{
      if(controller.signal.aborted)return
      if(result.blob)objectUrl=URL.createObjectURL(result.blob)
      setLoaded({scope,url:objectUrl,text:result.text})
      onReady?.()
    }).catch(error=>{if(!controller.signal.aborted){rememberBookLoadFailure({openUrl:source.openUrl,sourceUrl:source.sourceUrl},error);setLoaded({scope,error:error.message})}})
    return ()=>{controller.abort();if(objectUrl)URL.revokeObjectURL(objectUrl)}
  },[scope,source.viewUrl,source.kind,source.openUrl,source.sourceUrl,onReady])
  const current=loaded?.scope===scope ? loaded : null
  const error=current?.error
  const csp="default-src 'none'; style-src 'unsafe-inline'; img-src data:;"
  return <div className="br-doc">
    {!current && <div className="br-source-state" role="status"><p>Đang tải và kiểm tra nội dung…</p><p className="br-doc__meta">Bạn có thể tiếp tục ghi chú trong lúc chờ.</p></div>}
    {error && <div className="br-source-state" role="alert"><h3>Chưa mở được tài liệu</h3><p>{error}</p><div className="br-source-actions"><button className="br-btn br-btn--solid" onClick={()=>setNonce(n=>n+1)}>Thử tải lại</button></div></div>}
    {current && !error && (source.kind==='pdf' ? <iframe className="br-doc__frame" src={`${current.url}#page=${initialPage}&view=FitH&navpanes=0`} title={title} />
      :source.kind==='html' ? <iframe className="br-doc__frame br-doc__frame--html" title={title} sandbox="" referrerPolicy="no-referrer" srcDoc={`<!doctype html><meta http-equiv="Content-Security-Policy" content="${csp}">${current.text}`} />
        :<article className="br-doc__article"><h2>{title}</h2><pre className="br-doc__content">{current.text}</pre></article>)}
    <div className="br-doc__actions">{source.openUrl && <a className="br-btn br-btn--ghost" href={source.openUrl} target="_blank" rel="noreferrer">Mở tại nguồn</a>}</div>
  </div>
}
