import { decide } from "./api"
import type { Item } from "./api"
import { useState } from "react"

export default function ReviewCard({ item, onDone }:{
  item: Item, onDone: (id:string)=>void
}) {
  const [loading, setLoading] = useState<"yes"|"no"|null>(null)

  const tryDecide = async (d:"yes"|"no") => {
    try {
      setLoading(d)
      await decide(item.id, d)
      onDone(item.id)
    } catch (e:any) {
      alert(`처리 실패: ${e?.message ?? e}`)
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="card">
      <h3>{item.title ?? "(제목 없음)"}</h3>
      <div style={{fontSize:12, opacity:0.8, marginBottom:8}}>
        source_id: {item.source_id ?? "-"}
      </div>
      <pre>{item.content ?? "(내용 없음)"}</pre>
      <div className="actions">
        <button className="btn yes" disabled={!!loading} onClick={()=>tryDecide("yes")}>
          {loading==="yes" ? "저장 중..." : "Yes → Rmx 저장"}
        </button>
        <button className="btn no" disabled={!!loading} onClick={()=>tryDecide("no")}>
          {loading==="no" ? "처리 중..." : "No → 숨기기"}
        </button>
      </div>
    </div>
  )
}
