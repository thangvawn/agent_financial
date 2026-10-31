import {useEffect,useMemo,useState} from 'react'
import {bookSourceKey,cachedBookCheck,checkBookSource} from '../services/bookAvailability'

export function useBookAvailability(book) {
  const key=bookSourceKey(book)
  const [retryKey,setRetryKey]=useState(0)
  const scope=`${key}:${retryKey}`
  const [state,setState]=useState(()=>({scope,result:cachedBookCheck(key)}))
  const sourceInput=useMemo(()=>({url:book.url,pdf_url:book.pdf_url,download_url:book.download_url,book_id:book.book_id,content_role:book.content_role}),[book.url,book.pdf_url,book.download_url,book.book_id,book.content_role])
  useEffect(()=>{
    const controller=new AbortController()
    checkBookSource(sourceInput,{signal:controller.signal,force:retryKey>0}).then(result=>{
      if(!controller.signal.aborted)setState({scope,result})
    }).catch(()=>{})
    return ()=>controller.abort()
  },[scope,sourceInput,retryKey])
  return {state:state.scope===scope && state.result ? state.result : {status:'checking'},retry:()=>setRetryKey(value=>value+1)}
}
export function useLibrarySourceChecks(books,{enabled=true,force=false,runKey=0}={}) {
  const [checks,setChecks]=useState({})
  const tasks=JSON.stringify(books.map(({url,pdf_url,download_url,book_id,content_role})=>({url,pdf_url,download_url,book_id,content_role})))
  useEffect(()=>{
    if(!enabled)return
    const controller=new AbortController();let index=0
    const queue=JSON.parse(tasks)
    async function worker() {
      while(index<queue.length && !controller.signal.aborted) {
        const book=queue[index++],key=bookSourceKey(book)
        try {
          const result=await checkBookSource(book,{signal:controller.signal,force})
          if(!controller.signal.aborted)setChecks(previous=>previous[key]===result?previous:{...previous,[key]:result})
        } catch { /* cleanup cancels queued checks */ }
      }
    }
    for(let i=0;i<3;i++)worker()
    return ()=>controller.abort()
  },[tasks,enabled,force,runKey])
  return checks
}
