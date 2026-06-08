"""
面试日程 CRUD
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview
from app.models.application import Application
from app.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["interviews"])


@router.get("/interviews")
async def api_list_interviews(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interviews = db.query(Interview).join(
        Application, Interview.application_id == Application.id
    ).filter(
        Application.user_id == user.id
    ).order_by(Interview.scheduled_time.asc().nullslast()).all()

    return {
        "ok": True,
        "data": [{
            "id": iv.id,
            "application_id": iv.application_id,
            "company": iv.application.company,
            "position": iv.application.position,
            "round": iv.round,
            "scheduled_time": iv.scheduled_time.strftime("%Y-%m-%dT%H:%M") if iv.scheduled_time else None,
            "interviewer": iv.interviewer,
            "interview_type": iv.interview_type,
            "interview_status": iv.interview_status,
            "notes": iv.notes,
        } for iv in interviews]
    }


@router.get("/interviews/upcoming")
async def api_upcoming_interviews(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    interviews = db.query(Interview).join(
        Application, Interview.application_id == Application.id
    ).filter(
        Application.user_id == user.id,
        Interview.scheduled_time >= now,
        Interview.interview_status == "scheduled",
    ).order_by(Interview.scheduled_time.asc()).limit(10).all()

    return {
        "ok": True,
        "data": [{
            "id": iv.id,
            "company": iv.application.company,
            "position": iv.application.position,
            "round": iv.round,
            "scheduled_time": iv.scheduled_time.strftime("%Y-%m-%dT%H:%M") if iv.scheduled_time else None,
            "interviewer": iv.interviewer,
            "interview_type": iv.interview_type,
        } for iv in interviews]
    }


@router.post("/applications/{app_id}/interviews")
async def api_create_interview(
    app_id: int,
    round: str = Form("一面"),
    scheduled_time: str = Form(None),
    interviewer: str = Form(""),
    interview_type: str = Form("技术面"),
    notes: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(
        Application.id == app_id, Application.user_id == user.id
    ).first()
    if not app:
        raise HTTPException(404)

    dt = None
    if scheduled_time:
        try:
            dt = datetime.fromisoformat(scheduled_time)
        except ValueError:
            pass

    iv = Interview(
        application_id=app_id,
        round=round,
        scheduled_time=dt,
        interviewer=interviewer,
        interview_type=interview_type,
        notes=notes,
    )
    db.add(iv)
    if app.status in ("applied", "assessment"):
        app.status = "interview"
    db.commit()
    db.refresh(iv)
    return {"ok": True, "data": {"id": iv.id}}


@router.put("/interviews/{interview_id}")
async def api_update_interview(
    interview_id: int,
    request: Request,
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

    body = await request.json()
    for field in ["round", "interviewer", "interview_type", "interview_status", "notes"]:
        if field in body:
            setattr(iv, field, body[field])
    if "scheduled_time" in body and body["scheduled_time"]:
        try:
            iv.scheduled_time = datetime.fromisoformat(body["scheduled_time"])
        except ValueError:
            pass

    db.commit()
    return {"ok": True}


@router.delete("/interviews/{interview_id}")
async def api_delete_interview(
    interview_id: int,
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
    db.delete(iv)
    db.commit()
    return {"ok": True}
