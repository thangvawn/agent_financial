import {useCallback,useEffect,useRef,useState} from 'react'
import {catalogDocument,deleteLibraryItem,fetchLibraryItem,fetchPersonalLibrary,openLibraryItem,saveCatalogDocument,updateLibraryItem,uploadLibraryDocument} from '../services/personalLibraryApi'

export function usePersonalLibrary(sessionId) {
  const [state,setState]=useState({sessionId,items:[],loading:true,error:''})
  const scope=useRef(sessionId)
  const version=useRef(0)
  useEffect(()=>{scope.current=sessionId},[sessionId])
  const accept=useCallback(item=>{
    if(scope.current!==sessionId)return item
    version.current++
    setState(previous=>({...previous,sessionId,loading:false,error:'',items:[item,...(previous.sessionId===sessionId?previous.items:[]).filter(row=>row.id!==item.id)]}))
    return item
  },[sessionId])
  const refresh=useCallback(async function refreshCurrent(signal){
    const started=version.current
    if(!sessionId)return
    try {
      const result=await fetchPersonalLibrary(sessionId,signal)
      if(scope.current!==sessionId || signal?.aborted)return
      if(started!==version.current)return refreshCurrent(signal)
      setState({sessionId,items:result.items,loading:false,error:''})
    }catch(error){if(scope.current===sessionId && !signal?.aborted)setState(previous=>({...previous,sessionId,loading:false,error:error.message}))}
  },[sessionId])
  useEffect(()=>{const controller=new AbortController();refresh(controller.signal);return()=>controller.abort()},[refresh])
  const add=useCallback(async book=>accept(book.library_id?await fetchLibraryItem(sessionId,book.library_id):await saveCatalogDocument(sessionId,catalogDocument(book))),[accept,sessionId])
  const upload=useCallback(async(file,metadata)=>accept(await uploadLibraryDocument(sessionId,file,metadata)),[accept,sessionId])
  const update=useCallback(async(id,patch)=>accept(await updateLibraryItem(sessionId,id,patch)),[accept,sessionId])
  const recordOpen=useCallback(async(book,eventId)=>{
    const item=book.library_id?{id:book.library_id}:await saveCatalogDocument(sessionId,catalogDocument(book))
    return accept(await openLibraryItem(sessionId,item.id,eventId))
  },[accept,sessionId])
  const remove=useCallback(async id=>{
    await deleteLibraryItem(sessionId,id)
    if(scope.current===sessionId){version.current++;setState(previous=>({...previous,items:previous.items.filter(item=>item.id!==id)}))}
  },[sessionId])
  return {items:state.sessionId===sessionId?state.items:[],loading:state.sessionId!==sessionId || state.loading,
    error:state.sessionId===sessionId?state.error:'',add,upload,update,remove,recordOpen,refresh}
}
