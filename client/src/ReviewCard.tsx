import { useState, useMemo } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { decide } from "./api"
import type { Item } from "./api"

export default function ReviewCard({ item, onDone }:{
  item: Item, onDone: (id:string)=>void
}) {
  const [loading, setLoading] = useState<"yes"|"no"|null>(null)
  const [expanded, setExpanded] = useState(false)

  const question = useMemo(() => (item.title ?? "").trim(), [item.title])
  const answer   = useMemo(() => (item.content ?? "").trim(), [item.content])

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
    <div className="card card-full">
      {/* 상단 메타 */}
      <div className="meta">
        <span className="badge">규정집</span>
        <span className="meta-dot">•</span>
        <span className="meta-kv">source_id: {item.source_id ?? "-"}</span>
        {item.created_at && <>
          <span className="meta-dot">•</span>
          <span className="meta-kv">등록일시: {item.created_at}</span>
        </>}
      </div>

      {/* 질문 (위) */}
      <section className="section">
        <div className="section-title">질문</div>
        <div className="md md-wide">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {question || "(질문 없음)"}
          </ReactMarkdown>
        </div>
      </section>

      {/* 답변 (아래, 넓은 폭 + 접기/펼치기) */}
      <section className="section">
        <div className="section-title">답변</div>
        <div className={`md md-wide ${expanded ? "answer-open" : "answer-collapsed"}`}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {answer || "(답변 없음)"}
          </ReactMarkdown>
        </div>
        {answer && answer.length > 300 && (
          <button className="link-btn" onClick={()=>setExpanded(v=>!v)}>
            {expanded ? "접기" : "더 보기"}
          </button>
        )}
      </section>

      {/* 하단 버튼 */}
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
