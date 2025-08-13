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

  // 백엔드가 분리해서 주는 값 사용, 없으면 호환용 fallback
  const prompt   = useMemo(() => (item.prompt ?? item.title ?? "").trim(), [item.prompt, item.title])
  const question = useMemo(() => (item.question ?? "").trim(), [item.question])
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
      {/* 메타 */}
      <div className="meta">
        <span className="badge">규정집</span>
        <span className="meta-dot">•</span>
        <span className="meta-kv">source_id: {item.source_id ?? "-"}</span>
        {item.created_at && <>
          <span className="meta-dot">•</span>
          <span className="meta-kv">등록일시: {item.created_at}</span>
        </>}
      </div>

      {/* ✅ 프롬프트 카드 */}
      <div className="subcard">
        <div className="subcard-title">프롬프트</div>
        <div className="subcard-body scrollable">
          <div className="md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {prompt || "(프롬프트 없음)"}
            </ReactMarkdown>
          </div>
        </div>
      </div>

      {/* ✅ 질문 카드 */}
      <div className="subcard">
        <div className="subcard-title">질문</div>
        <div className="subcard-body scrollable">
          <div className="md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {question || "(질문 없음)"}
            </ReactMarkdown>
          </div>
        </div>
      </div>

      {/* ✅ 답변 카드 (기본 접힘) */}
      <div className="subcard">
        <div className="subcard-title">답변</div>
        <div className={`subcard-body ${expanded ? "answer-open" : "answer-collapsed"}`}>
          <div className="md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {answer || "(답변 없음)"}
            </ReactMarkdown>
          </div>
        </div>
        {answer && answer.length > 300 && (
          <button className="link-btn" onClick={()=>setExpanded(v=>!v)}>
            {expanded ? "접기" : "더 보기"}
          </button>
        )}
      </div>

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
