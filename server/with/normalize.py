# normalize.py
from datetime import datetime, timezone
from dateutil import parser as dtparser

REQUIRED_FIELDS = ["source_id", "title", "content"]
OPTIONAL_DATE_FIELDS = ["created_at", "updated_at"]

def _parse_dt(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.astimezone(timezone.utc)
    try:
        return dtparser.parse(str(val)).astimezone(timezone.utc)
    except Exception:
        return None

def normalize(doc: dict) -> dict:
    """
    raw → Rmx 스키마 정규화/검증
    한글키(질문/답변/등록일시/no/프롬프트 등)를 표준키로 맵핑
    """
    # 1) 원본에서 표준키로 변환(우선순위 fallback)
    source_id = (
        doc.get("source_id")
        or (str(doc.get("no")) if doc.get("no") is not None else None)
        or str(doc.get("_id"))
    )
    title = doc.get("title") or doc.get("질문") or doc.get("프롬프트")
    content = doc.get("content") or doc.get("답변")

    created_at = (
        _parse_dt(doc.get("created_at"))
        or _parse_dt(doc.get("등록일시"))
    )
    updated_at = _parse_dt(doc.get("updated_at"))

    # 2) 필수 필드 체크
    if not source_id:
        raise ValueError("missing required field: source_id")
    if not title:
        raise ValueError("missing required field: title (e.g., '질문'/'프롬프트')")
    if not content:
        raise ValueError("missing required field: content (e.g., '답변')")

    # 3) 결과 구성
    norm = {
        "source_id": source_id,
        "title": title,
        "content": content,
        "created_at": created_at,
        "updated_at": updated_at,
        "ingested_at": datetime.now(timezone.utc),
        "source_raw_id": str(doc.get("_id")),
        # 필요하면 원본 메타를 보존
        "meta": {
            "프롬프트": doc.get("프롬프트"),
            "봇": doc.get("봇"),
            "이름": doc.get("이름"),
            "사번": doc.get("사번"),
            "모델": doc.get("모델"),
            "질문토큰": doc.get("질문토큰"),
            "답변토큰": doc.get("답변토큰"),
            "등록일시": doc.get("등록일시"),
            "no": doc.get("no"),
        },
    }
    return norm
