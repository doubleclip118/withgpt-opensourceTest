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

def _oid(oid_str: str) -> ObjectId:
    try:
        return ObjectId(oid_str)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid id")

def _to_item(doc: dict) -> Item:
    # title/content/source_id가 없을 때 한글 키로 fallback
    title = doc.get("title") or doc.get("질문") or doc.get("프롬프트")
    content = doc.get("content") or doc.get("답변")
    source_id = doc.get("source_id") or (str(doc.get("no")) if doc.get("no") is not None else None)

    # created_at도 등록일시를 fallback
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

@app.get("/api/queue", response_model=List[Item])
def get_queue(limit: int = 20):
    cursor = raw_col.find(
        {"decision": {"$exists": False}},
        projection={
            # 표준 키
            "source_id": 1, "title": 1, "content": 1, "created_at": 1, "updated_at": 1,
            # 한글 키 fallback
            "질문": 1, "답변": 1, "프롬프트": 1, "등록일시": 1, "no": 1,
        }
    ).sort("_id", 1).limit(max(1, min(limit, 100)))
    return [_to_item(d) for d in cursor]

@app.post("/api/decide")
def decide(body: DecideBody):
    _id = _oid(body.id)
    raw = raw_col.find_one({"_id": _id})
    if not raw:
        raise HTTPException(status_code=404, detail="not found")

    if raw.get("decision") in ("yes", "no"):
        return {"ok": True, "message": f"already decided: {raw.get('decision')}"}

    if body.decision == "yes":
        try:
            doc = normalize(raw)
            dst_col.insert_one(doc)
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=f"normalize failed: {str(ve)}")

    raw_col.update_one(
        {"_id": _id},
        {"$set": {"decision": body.decision, "decided_at": datetime.now(timezone.utc)}}
    )
    return {"ok": True, "decision": body.decision}

@app.get("/api/stats")
def stats():
    total = raw_col.estimated_document_count()
    undecided = raw_col.count_documents({"decision": {"$exists": False}})
    yes_cnt = raw_col.count_documents({"decision": "yes"})
    no_cnt = raw_col.count_documents({"decision": "no"})
    dst_cnt = dst_col.estimated_document_count()
    return {
        "raw_total": total,
        "raw_undecided": undecided,
        "raw_yes": yes_cnt,
        "raw_no": no_cnt,
        "rmx_total": dst_cnt,
    }
