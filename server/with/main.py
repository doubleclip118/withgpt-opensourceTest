# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from bson import ObjectId
from datetime import datetime, timezone
import os

from db import raw_col, dst_col
from normalize import normalize

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="Review Queue API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Pydantic Models -----------------
class Item(BaseModel):
    id: str = Field(..., description="raw _id")
    source_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DecideBody(BaseModel):
    id: str
    decision: Literal["yes", "no"]

# ----------------- Helpers -----------------
def _oid(oid_str: str) -> ObjectId:
    try:
        return ObjectId(oid_str)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid id")

def _to_item(doc: dict) -> Item:
    """Mongo raw 문서를 프런트용 Item으로 변환 (프롬프트 우선 제목, 한글키 fallback)"""
    title = doc.get("프롬프트") or doc.get("질문") or doc.get("title")
    content = doc.get("content") or doc.get("답변")
    source_id = doc.get("source_id") or (str(doc.get("no")) if doc.get("no") is not None else None)

    created_at = (doc.get("created_at") or doc.get("등록일시") or None)
    updated_at = (doc.get("updated_at") or None)

    return Item(
        id=str(doc["_id"]),
        source_id=source_id,
        title=title,
        content=content,
        created_at=str(created_at) if created_at else None,
        updated_at=str(updated_at) if updated_at else None,
    )

# 통계/큐 공통 필터: 규정집만
BASE_FILTER = {"봇": "규정집"}

# ----------------- Routes -----------------
@app.get("/api/queue", response_model=List[Item])
def get_queue(limit: int = 20):
    """판정되지 않은(= decision 필드 없음) & 봇=규정집 만 노출"""
    cursor = raw_col.find(
        {
            **BASE_FILTER,
            "decision": {"$exists": False},
        },
        projection={
            # 표준 키
            "source_id": 1, "title": 1, "content": 1, "created_at": 1, "updated_at": 1,
            # 한글 키 fallback
            "질문": 1, "답변": 1, "프롬프트": 1, "등록일시": 1, "no": 1,
            # 확인용
            "봇": 1
        }
    ).sort("_id", 1).limit(max(1, min(limit, 100)))
    return [_to_item(d) for d in cursor]

@app.post("/api/decide")
def decide(body: DecideBody):
    """Yes/No 판정. Yes면 normalize 후 Rmx에 insert, 공통으로 RAW에 decision/decided_at 기록"""
    _id = _oid(body.id)
    raw = raw_col.find_one({"_id": _id})
    if not raw:
        raise HTTPException(status_code=404, detail="not found")

    # 중복 처리 방지
    if raw.get("decision") in ("yes", "no"):
        return {"ok": True, "message": f"already decided: {raw.get('decision')}"}

    # YES → Rmx 저장(question/answer 만)
    if body.decision == "yes":
        try:
            doc = normalize(raw)  # {"question": ..., "answer": ...}
            dst_col.insert_one(doc)
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=f"normalize failed: {str(ve)}")

    # RAW에 판정 기록 (공통)
    raw_col.update_one(
        {"_id": _id},
        {"$set": {"decision": body.decision, "decided_at": datetime.now(timezone.utc)}}
    )
    return {"ok": True, "decision": body.decision}

@app.get("/api/stats")
def stats():
    """규정집 기준 통계"""
    total      = raw_col.count_documents({**BASE_FILTER})
    undecided  = raw_col.count_documents({**BASE_FILTER, "decision": {"$exists": False}})
    yes_cnt    = raw_col.count_documents({**BASE_FILTER, "decision": "yes"})
    no_cnt     = raw_col.count_documents({**BASE_FILTER, "decision": "no"})
    # Rmx는 규정집만 Yes로 들어간다고 가정. (혹시 혼재 가능성 있으면 question/answer 존재 여부로 필터 가능)
    dst_cnt    = dst_col.estimated_document_count()

    return {
        "raw_total": total,
        "raw_undecided": undecided,
        "raw_yes": yes_cnt,
        "raw_no": no_cnt,
        "rmx_total": dst_cnt,
    }
