"""
数据分析引擎
纯 SQLAlchemy 查询，展示 JOIN + GROUP BY + 子查询能力
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case

from app.models.application import Application
from app.models.interview import Interview
from app.models.interview_note import InterviewNote

STATUS_ORDER = ["applied", "assessment", "interview", "waiting", "offer", "rejected"]
STATUS_LABELS = {
    "applied": "已投递",
    "assessment": "测评/笔试",
    "interview": "面试中",
    "waiting": "等结果",
    "offer": "Offer",
    "rejected": "已挂",
}


def get_funnel(user_id: int, db: Session) -> list[dict]:
    """
    转化漏斗：统计每个阶段的数量和转化率
    applied → assessment → interview → waiting → offer
    """
    apps = db.query(Application).filter(Application.user_id == user_id).all()
    total = len(apps) or 1  # 避免除零

    by_status = {}
    for a in apps:
        by_status[a.status] = by_status.get(a.status, 0) + 1

    funnel_stages = ["applied", "assessment", "interview", "waiting", "offer"]
    result = []
    for stage in funnel_stages:
        count = by_status.get(stage, 0)
        result.append({
            "stage": stage,
            "label": STATUS_LABELS.get(stage, stage),
            "count": count,
            "rate": round(count / total * 100, 1),
        })
    return result


def get_channels(user_id: int, db: Session) -> list[dict]:
    """
    渠道效率分析：每个渠道的投递数、面试率、Offer率
    """
    apps = db.query(Application).filter(Application.user_id == user_id).all()

    # 按渠道分组
    channels = {}
    for a in apps:
        s = a.source or "其他"
        if s not in channels:
            channels[s] = {"total": 0, "interview": 0, "offer": 0}
        channels[s]["total"] += 1
        if a.status == "interview":
            channels[s]["interview"] += 1
        if a.status == "offer":
            channels[s]["offer"] += 1

    result = []
    for name, stats in channels.items():
        t = stats["total"]
        result.append({
            "channel": name,
            "total": t,
            "interview_count": stats["interview"],
            "offer_count": stats["offer"],
            "interview_rate": round(stats["interview"] / t * 100, 1),
            "offer_rate": round(stats["offer"] / t * 100, 1),
        })
    result.sort(key=lambda x: x["interview_rate"], reverse=True)
    return result


def get_timeline(user_id: int, db: Session, granularity: str = "month") -> list[dict]:
    """
    时间趋势：按月或周统计投递和面试数量
    """
    apps = db.query(Application).filter(Application.user_id == user_id).all()

    # timeline 汇总
    timeline = {}
    for a in apps:
        if not a.applied_date:
            continue
        if granularity == "month":
            key = a.applied_date.strftime("%Y-%m")
        else:
            key = a.applied_date.strftime("%Y-W%W")

        if key not in timeline:
            timeline[key] = {"applications": 0, "interviews": 0}
        timeline[key]["applications"] += 1

    # 把面试也加进去
    interviews = db.query(Interview).join(Application).filter(
        Application.user_id == user_id,
        Interview.scheduled_time.isnot(None),
    ).all()
    for iv in interviews:
        if not iv.scheduled_time:
            continue
        if granularity == "month":
            key = iv.scheduled_time.strftime("%Y-%m")
        else:
            key = iv.scheduled_time.strftime("%Y-W%W")

        if key not in timeline:
            timeline[key] = {"applications": 0, "interviews": 0}
        timeline[key]["interviews"] += 1

    result = [{"period": k, **v} for k, v in sorted(timeline.items())]
    return result


def get_companies(user_id: int, db: Session) -> list[dict]:
    """
    公司维度分析：对每家公司投递了多少次，最终走到了哪个阶段
    """
    apps = db.query(Application).filter(Application.user_id == user_id).order_by(
        Application.updated_at.desc()
    ).all()

    companies = {}
    for a in apps:
        c = a.company
        if c not in companies:
            companies[c] = {
                "company": c,
                "total_applications": 0,
                "latest_status": a.status,
                "positions": [],
                "interview_rounds": 0,
            }
        companies[c]["total_applications"] += 1
        companies[c]["positions"].append(a.position)

    # 算面试轮次
    interviews = db.query(Interview).join(Application).filter(
        Application.user_id == user_id
    ).all()
    for iv in interviews:
        c = iv.application.company
        if c in companies:
            companies[c]["interview_rounds"] += 1

    result = sorted(companies.values(), key=lambda x: x["total_applications"], reverse=True)
    for item in result:
        item["positions"] = list(set(item["positions"]))
        item["status_label"] = STATUS_LABELS.get(item["latest_status"], item["latest_status"])

    return result


def get_summary(user_id: int, db: Session) -> dict:
    """
    综合洞察：把上面的数据整合成可读的文字总结
    """
    funnel = get_funnel(user_id, db)
    channels = get_channels(user_id, db)
    companies = get_companies(user_id, db)
    timeline = get_timeline(user_id, db, "month")

    total = funnel[0]["count"] if funnel else 0
    offer_count = db.query(Application).filter(
        Application.user_id == user_id,
        Application.status == "offer",
    ).count()
    interview_count = db.query(Application).filter(
        Application.user_id == user_id,
        Application.status.in_(["interview", "waiting", "offer"]),
    ).count()

    # 转化率
    interview_rate = round(interview_count / total * 100, 1) if total > 0 else 0
    offer_rate = round(offer_count / total * 100, 1) if total > 0 else 0

    # 最佳渠道
    best_channel = channels[0] if channels else None
    worst_channel = channels[-1] if len(channels) > 1 else None

    # 最多的公司
    top_company = companies[0] if companies else None

    # 面试总数
    total_interviews = db.query(Interview).join(Application).filter(
        Application.user_id == user_id
    ).count()

    # 新增维度
    categories = get_categories(user_id, db)
    rejections = get_rejection_reasons(user_id, db)
    salary_data = get_salary_comparison(user_id, db)

    # 生成洞察文本
    insights = []
    insights.append(f"你共投递了 {total} 份简历，其中 {interview_count} 份进入了面试阶段，面试转化率为 {interview_rate}%。")
    if offer_count > 0:
        insights.append(f"最终斩获 {offer_count} 个 Offer，Offer转化率 {offer_rate}%。")
    else:
        insights.append("暂未拿到 Offer，继续加油！")

    if best_channel and best_channel["total"] > 0:
        insights.append(f"最佳投递渠道是「{best_channel['channel']}」，面试率 {best_channel['interview_rate']}%。")
    if top_company:
        insights.append(f"投递最多的公司是「{top_company['company']}」，共投递 {top_company['total_applications']} 次。")

    if total_interviews > 0:
        insights.append(f"你一共参加了 {total_interviews} 场面试。")

    # 岗位类别分布
    if categories:
        best_cat = categories[0]
        insights.append(f"投递最多的岗位类别是「{best_cat['category']}」，投递了 {best_cat['total']} 次，面试率 {best_cat['interview_rate']}%。")

    # 挂因分析
    if rejections:
        top_reason = rejections[0]
        insights.append(f"最常见的挂因是「{top_reason['reason']}」，共 {top_reason['count']} 次，需要针对性提升。")

    # 薪资对比
    if salary_data["offer_count"] > 0:
        insights.append(f"已记录 {salary_data['offer_count']} 个 Offer 薪资，可在薪资对比中查看。")

    return {
        "total": total,
        "offer_count": offer_count,
        "interview_rate": interview_rate,
        "offer_rate": offer_rate,
        "best_channel": best_channel["channel"] if best_channel else None,
        "top_company": top_company["company"] if top_company else None,
        "total_interviews": total_interviews,
        "categories": categories,
        "rejection_reasons": rejections,
        "salary_comparison": salary_data,
        "insights": insights,
    }


def get_categories(user_id: int, db: Session) -> list[dict]:
    """岗位类别分布"""
    apps = db.query(Application).filter(Application.user_id == user_id).all()
    cats = {}
    for a in apps:
        cat = a.job_category or "未分类"
        if cat not in cats:
            cats[cat] = {"total": 0, "interview": 0, "offer": 0}
        cats[cat]["total"] += 1
        if a.status == "interview":
            cats[cat]["interview"] += 1
        if a.status == "offer":
            cats[cat]["offer"] += 1
    result = []
    for name, stats in cats.items():
        t = stats["total"]
        result.append({
            "category": name,
            "total": t,
            "interview_count": stats["interview"],
            "offer_count": stats["offer"],
            "interview_rate": round(stats["interview"] / t * 100, 1),
        })
    result.sort(key=lambda x: x["total"], reverse=True)
    return result


def get_rejection_reasons(user_id: int, db: Session) -> list[dict]:
    """挂因统计"""
    apps = db.query(Application).filter(
        Application.user_id == user_id,
        Application.status == "rejected",
    ).all()
    reasons = {}
    for a in apps:
        reason = a.rejection_reason or "未标记"
        reasons[reason] = reasons.get(reason, 0) + 1
    result = [{"reason": k, "count": v} for k, v in sorted(reasons.items(), key=lambda x: x[1], reverse=True)]
    return result


def get_salary_comparison(user_id: int, db: Session) -> dict:
    """薪资对比：期望 vs Offer"""
    apps = db.query(Application).filter(
        Application.user_id == user_id,
        Application.salary_range != "",
    ).all()
    candidates = []
    offers = []
    for a in apps:
        if a.salary_range:
            candidates.append(a.salary_range)
        if a.offer_salary:
            offers.append(a.offer_salary)
    return {
        "expected_salaries": candidates[:10],
        "offer_salaries": offers[:10],
        "offer_count": len(offers),
    }


def get_stats(user_id: int, db: Session) -> dict:
    """统计面板数据（兼容旧 /api/stats）"""
    apps = db.query(Application).filter(Application.user_id == user_id).all()
    total = len(apps)
    by_status = {}
    for a in apps:
        by_status[a.status] = by_status.get(a.status, 0) + 1
    by_source = {}
    for a in apps:
        by_source[a.source] = by_source.get(a.source, 0) + 1
    return {
        "total": total,
        "by_status": by_status,
        "by_source": by_source,
    }
