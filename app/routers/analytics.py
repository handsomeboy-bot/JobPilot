"""
数据分析 API
"""
import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.services.analytics_engine import (
    get_funnel, get_channels, get_timeline, get_companies, get_summary, get_stats,
    get_categories, get_rejection_reasons, get_salary_comparison,
)
from app.services.ai_insight import get_ai_insights, get_ai_prediction

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/stats")
def api_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """基础统计（兼容旧版 /api/stats）"""
    data = get_stats(user.id, db)
    return {"ok": True, **data}


@router.get("/funnel")
def api_funnel(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """转化漏斗"""
    data = get_funnel(user.id, db)
    return {"ok": True, "data": data}


@router.get("/channels")
def api_channels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """渠道效率分析"""
    data = get_channels(user.id, db)
    return {"ok": True, "data": data}


@router.get("/timeline")
def api_timeline(
    granularity: str = Query("month", pattern="^(month|week)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """时间趋势"""
    data = get_timeline(user.id, db, granularity)
    return {"ok": True, "data": data, "granularity": granularity}


@router.get("/companies")
def api_companies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """公司维度分析"""
    data = get_companies(user.id, db)
    return {"ok": True, "data": data}


@router.get("/summary")
def api_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """综合洞察"""
    data = get_summary(user.id, db)
    return {"ok": True, "data": data}


@router.get("/categories")
def api_categories(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """岗位类别分布"""
    data = get_categories(user.id, db)
    return {"ok": True, "data": data}


@router.get("/rejection-reasons")
def api_rejection_reasons(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """挂因统计"""
    data = get_rejection_reasons(user.id, db)
    return {"ok": True, "data": data}


@router.get("/salary-comparison")
def api_salary_comparison(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """薪资对比"""
    data = get_salary_comparison(user.id, db)
    return {"ok": True, "data": data}


@router.get("/ai-insights")
def api_ai_insights(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """AI 深度洞察"""
    stats = get_stats(user.id, db)
    funnel = get_funnel(user.id, db)
    channels = get_channels(user.id, db)
    categories = get_categories(user.id, db)
    rejections = get_rejection_reasons(user.id, db)
    timeline = get_timeline(user.id, db, "month")
    companies = get_companies(user.id, db)

    insights = get_ai_insights(stats, funnel, channels, categories, rejections, timeline, companies)
    if insights is None:
        return {"ok": True, "data": [], "msg": "AI 未配置或不支持", "ai_enabled": False}

    return {"ok": True, "data": insights, "ai_enabled": True}


@router.get("/ai-prediction")
def api_ai_prediction(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """AI 预测"""
    stats = get_stats(user.id, db)
    timeline = get_timeline(user.id, db, "month")

    prediction = get_ai_prediction(stats, timeline)
    if prediction is None:
        return {"ok": True, "data": "", "msg": "AI 未配置或数据不足", "ai_enabled": False}

    return {"ok": True, "data": prediction, "ai_enabled": True}


@router.get("/export")
def api_export(
    format: str = Query("csv", pattern="^(csv)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导出投递数据为 CSV"""
    from app.models.application import Application
    apps = db.query(Application).filter(
        Application.user_id == user.id
    ).order_by(Application.applied_date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["公司", "岗位", "城市", "薪资范围", "渠道", "优先级",
                      "状态", "岗位类别", "挂因", "Offer薪资", "投递日期", "备注", "JD链接"])
    for a in apps:
        writer.writerow([
            a.company, a.position, a.location, a.salary_range, a.source,
            a.priority, a.status, a.job_category, a.rejection_reason,
            a.offer_salary,
            a.applied_date.strftime("%Y-%m-%d") if a.applied_date else "",
            a.notes, a.jd_link,
        ])

    output.seek(0)
    content = output.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        io.BytesIO(content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jobpilot_export.csv"},
    )
