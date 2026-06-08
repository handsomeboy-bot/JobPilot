"""
投递卡片 CRUD
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.application import Application
from app.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("")
async def api_list_applications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    apps = db.query(Application).filter(
        Application.user_id == user.id
    ).order_by(Application.updated_at.desc()).all()

    return {
        "ok": True,
        "data": [{
            "id": a.id, "company": a.company, "position": a.position,
            "location": a.location, "salary_range": a.salary_range,
            "source": a.source, "jd_link": a.jd_link,
            "priority": a.priority, "status": a.status,
            "job_category": a.job_category, "rejection_reason": a.rejection_reason,
            "offer_salary": a.offer_salary, "notes": a.notes,
            "applied_date": a.applied_date.strftime("%Y-%m-%d") if a.applied_date else "",
        } for a in apps]
    }


@router.post("")
async def api_create_application(
    company: str = Form(...),
    position: str = Form(...),
    location: str = Form(""),
    salary_range: str = Form(""),
    source: str = Form("其他"),
    jd_link: str = Form(""),
    priority: int = Form(3),
    job_category: str = Form(""),
    notes: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = Application(
        user_id=user.id, company=company, position=position,
        location=location, salary_range=salary_range,
        source=source, jd_link=jd_link, priority=priority,
        job_category=job_category, notes=notes,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"ok": True, "data": {"id": app.id}}


@router.put("/{app_id}")
async def api_update_application(
    app_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(
        Application.id == app_id, Application.user_id == user.id
    ).first()
    if not app:
        raise HTTPException(404)

    body = await request.json()
    for field in ["company", "position", "location", "salary_range",
                  "source", "jd_link", "priority", "status",
                  "job_category", "rejection_reason", "offer_salary", "notes"]:
        if field in body:
            setattr(app, field, body[field])

    db.commit()
    return {"ok": True}


@router.delete("/{app_id}")
async def api_delete_application(
    app_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(
        Application.id == app_id, Application.user_id == user.id
    ).first()
    if not app:
        raise HTTPException(404)
    db.delete(app)
    db.commit()
    return {"ok": True}
