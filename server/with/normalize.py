def normalize(doc: dict) -> dict:
    # 1) 값 추출 (우선순위 + 앞뒤 공백 제거)
    prompt = doc.get("프롬프트") or doc.get("title") or doc.get("질문")
    answer = doc.get("답변") or doc.get("content")

    if isinstance(prompt, str):
        prompt = prompt.strip()
    if isinstance(answer, str):
        answer = answer.strip()

    # 2) 필수값 검증
    if not prompt:
        raise ValueError("missing required field: 프롬프트(→ question)")
    if not answer:
        raise ValueError("missing required field: 답변(→ answer)")

    # 3) 최소 스키마로 반환
    return {
        "question": prompt,
        "answer": answer
    }