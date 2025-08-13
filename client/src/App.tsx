import { useEffect, useMemo, useState } from "react"
import { fetchQueue, fetchStats } from "./api"
import type { Item } from "./api"
import ReviewCard from "./ReviewCard"

export default function App() {
  const [items, setItems] = useState<Item[]>([])
  const [stats, setStats] = useState<any>(null)
  const [limit, setLimit] = useState(10)
  const [loading, setLoading] = useState(false)
  const empty = useMemo(()=>items.length === 0, [items])

  const load = async () => {
    setLoading(true)
    try {
      const [q, s] = await Promise.all([fetchQueue(limit), fetchStats()])
      setItems(q)
      setStats(s)
    } catch (e: any) {
      alert(`로드 실패: ${e?.message ?? e}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(()=>{ load() }, [limit])

  const handleDone = (id:string) => {
    setItems(prev => prev.filter(x => x.id !== id))
  }

  return (
    <div className="container">
      <div className="header">
        <h2 style={{margin:0}}>검수 큐</h2>
        <button className="btn" onClick={load} disabled={loading}>
          {loading ? "새로고침..." : "새로고침"}
        </button>
      </div>

      <div className="toolbar">
        <label>가져올 개수</label>
        <select value={limit} onChange={e=>setLimit(parseInt(e.target.value))}>
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
        </select>
        {stats && (
          <div className="stat">
            RAW 총 {stats.raw_total} / 미판정 {stats.raw_undecided} / YES {stats.raw_yes} / NO {stats.raw_no} / Rmx {stats.rmx_total}
          </div>
        )}
      </div>

      {empty ? (
        <div className="card">미판정 문서가 없습니다.</div>
      ) : (
        <div className="grid">
          {items.map(it => (
            <ReviewCard key={it.id} item={it} onDone={handleDone}/>
          ))}
        </div>
      )}
    </div>
  )
}
