"""
面经库 CRUD
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview
from app.models.interview_note import InterviewNote
from app.models.application import Application
from app.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["notes"])


@router.post("/notes/{note_id}/publish")
async def api_publish_note(
    note_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """将私有面经发布到论坛"""
    note = db.query(InterviewNote).join(
        Interview, InterviewNote.interview_id == Interview.id
    ).join(
        Application, Interview.application_id == Application.id
    ).filter(
        InterviewNote.id == note_id,
        Application.user_id == user.id,
    ).first()
    if not note:
        raise HTTPException(404)

    body = await request.json()
    is_anonymous = body.get("is_anonymous", 0)

    title = f"{note.interview.application.company} — {note.interview.application.position} 面经"

    qa_text = ""
    try:
        import json as _json
        qa_list = _json.loads(note.questions_answers or "[]")
        qa_lines = []
        for qa in qa_list:
            q = qa.get("q", "")
            a = qa.get("a", "")
            qa_lines.append(f"Q: {q}\nA: {a}")
        qa_text = "\n\n".join(qa_lines)
    except Exception:
        qa_text = note.questions_answers or ""

    content_parts = []
    if qa_text:
        content_parts.append(f"## 面试问答\n\n{qa_text}")
    if note.reflection:
        content_parts.append(f"## 复盘反思\n\n{note.reflection}")

    content = "\n\n".join(content_parts) if content_parts else (qa_text or "（无内容）")

    from app.models.forum import ForumPost
    post = ForumPost(
        author_id=user.id,
        title=title,
        content=content,
        tags=note.tags or "",
        is_anonymous=is_anonymous,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"ok": True, "data": {"id": post.id}}


@router.get("/notes")
async def api_list_notes(
    tag: str = None,
    search: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(InterviewNote).join(
        Interview, InterviewNote.interview_id == Interview.id
    ).join(
        Application, Interview.application_id == Application.id
    ).filter(Application.user_id == user.id)

    if tag:
        query = query.filter(InterviewNote.tags.contains(tag))
    if search:
        query = query.filter(
            InterviewNote.questions_answers.contains(search) |
            InterviewNote.reflection.contains(search)
        )

    notes = query.order_by(InterviewNote.created_at.desc()).all()
    return {
        "ok": True,
        "data": [{
            "id": n.id,
            "interview_id": n.interview_id,
            "application_id": n.application_id,
            "company": n.interview.application.company,
            "position": n.interview.application.position,
            "round": n.interview.round,
            "questions_answers": n.questions_answers,
            "reflection": n.reflection,
            "tags": n.tags,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M") if n.created_at else "",
        } for n in notes]
    }


@router.post("/interviews/{interview_id}/notes")
async def api_create_note(
    interview_id: int,
    questions_answers: str = Form("[]"),
    reflection: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    iv = db.query(Interview).join(
        Application, Interview.application_id == Application.id
    ).filter(
        Interview.id == interview_id,
        Application.user_id == user.id,
    ).first()
    if not iv:
        raise HTTPException(404)

    note = InterviewNote(
        interview_id=interview_id,
        application_id=iv.application_id,
        questions_answers=questions_answers,
        reflection=reflection,
        tags=tags,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"ok": True, "data": {"id": note.id}}


@router.put("/notes/{note_id}")
async def api_update_note(
    note_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.query(InterviewNote).join(
        Interview, InterviewNote.interview_id == Interview.id
    ).join(
        Application, Interview.application_id == Application.id
    ).filter(
        InterviewNote.id == note_id,
        Application.user_id == user.id,
    ).first()
    if not note:
        raise HTTPException(404)

    body = await request.json()
    for field in ["questions_answers", "reflection", "tags"]:
        if field in body:
            setattr(note, field, body[field])
    db.commit()
    return {"ok": True}


@router.delete("/notes/{note_id}")
async def api_delete_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.query(InterviewNote).join(
        Interview, InterviewNote.interview_id == Interview.id
    ).join(
        Application, Interview.application_id == Application.id
    ).filter(
        InterviewNote.id == note_id,
        Application.user_id == user.id,
    ).first()
    if not note:
        raise HTTPException(404)
    db.delete(note)
    db.commit()
    return {"ok": True}
