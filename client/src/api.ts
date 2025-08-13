const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000"

export type Item = {
  id: string
  source_id?: string
  title?: string
  content?: string
  prompt?: string      // ✅ 추가
  question?: string    // ✅ 추가
  created_at?: string
  updated_at?: string
}


export async function fetchQueue(limit = 20): Promise<Item[]> {
  const res = await fetch(`${BASE}/api/queue?limit=${limit}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function decide(id: string, decision: "yes" | "no") {
  const res = await fetch(`${BASE}/api/decide`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, decision })
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function fetchStats() {
  const res = await fetch(`${BASE}/api/stats`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
