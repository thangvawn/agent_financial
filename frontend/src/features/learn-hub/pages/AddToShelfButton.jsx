import {useState} from 'react'
import {resolveBookSource} from './bookSource'

export default function AddToShelfButton({book,library}) {
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  if(!library)return null
  const source=resolveBookSource(book)
  const saved=library.items.some(item=>item.source_url===source.sourceUrl || item.id===book.library_id)
  async function save() {
    setBusy(true);setError('')
    try{await library.add(book)}catch(cause){setError(cause.message)}finally{setBusy(false)}
  }
  return <><button className="lhc-btn lhc-btn--outline" type="button" disabled={busy || saved || !source.sourceUrl} onClick={save}>{saved?'Đã có trên kệ':busy?'Đang thêm…':'Thêm vào kệ'}</button>{error && <span role="alert" className="pl-error">{error}</span>}</>
}
