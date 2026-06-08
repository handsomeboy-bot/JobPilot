"""
AI 深度洞察 — DeepSeek API
"""
import json
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL


def _call_deepseek(prompt: str) -> str:
    """调用 DeepSeek Chat API"""
    if not DEEPSEEK_API_KEY:
        return None

    try:
        import urllib.request
        import urllib.error

        body = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个求职数据分析专家，擅长从数据中发现问题和机会。用简短有力的中文给出分析，每条不超过60字，3-5条。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }).encode("utf-8")

        req = urllib.request.Request(DEEPSEEK_BASE_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        })

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[AI洞察] DeepSeek 调用失败: {e}")
        return None


def get_ai_insights(stats: dict, funnel: list[dict], channels: list[dict],
                    categories: list[dict], rejections: list[dict],
                    timeline: list[dict], companies: list[dict]) -> list[str]:
    """
    综合所有数据，调用 AI 生成深度洞察
    返回洞察文本列表，失败返回 None 则降级用模板
    """
    if not DEEPSEEK_API_KEY:
        return None

    # 构建数据摘要
    summary_data = {
        "总投递": stats.get("total", 0),
        "面试转化率": f"{stats.get('interview_rate', 0)}%",
        "Offer率": f"{stats.get('offer_rate', 0)}%",
    }

    funnel_data = [{"阶段": f["label"], "数量": f["count"], "转化率": f"{f['rate']}%"} for f in funnel]

    channel_data = [{"渠道": c["channel"], "投递数": c["total"], "面试率": f"{c['interview_rate']}%", "Offer率": f"{c['offer_rate']}%"} for c in channels[:5]]

    category_data = [{"类别": c["category"], "投递数": c["total"], "面试率": f"{c['interview_rate']}%"} for c in categories] if categories else []

    rejection_data = [{"挂因": r["reason"], "次数": r["count"]} for r in rejections] if rejections else []

    timeline_data = [{"时期": t["period"], "投递": t["applications"], "面试": t["interviews"]} for t in timeline[-6:]] if timeline else []

    company_data = [{"公司": c["company"], "投递次数": c["total_applications"], "状态": c["status_label"]} for c in companies[:5]] if companies else []

    prompt = f"""
根据以下求职数据，给出3-5条深度洞察建议：

### 概览
{json.dumps(summary_data, ensure_ascii=False)}

### 漏斗
{json.dumps(funnel_data, ensure_ascii=False)}

### 渠道
{json.dumps(channel_data, ensure_ascii=False)}

### 岗位类别
{json.dumps(category_data, ensure_ascii=False)}

### 挂因
{json.dumps(rejection_data, ensure_ascii=False)}

### 趋势
{json.dumps(timeline_data, ensure_ascii=False)}

### 公司
{json.dumps(company_data, ensure_ascii=False)}

请给出具体的改进建议，要具体可操作，不要套话。
"""

    text = _call_deepseek(prompt)
    if text:
        lines = [l.strip("- 1234567890. ") for l in text.strip().split("\n") if l.strip()]
        return [l for l in lines if len(l) > 5]
    return None


def get_ai_prediction(stats: dict, timeline: list[dict]) -> str:
    """
    基于历史趋势预测
    需要足够数据（投递>5）才有意义
    """
    if not DEEPSEEK_API_KEY:
        return None

    total = stats.get("total", 0)
    if total < 3:
        return None

    # 近期趋势
    recent = timeline[-3:] if timeline else []
    trend_text = ""
    for t in recent:
        trend_text += f"{t['period']}: 投递{t['applications']}份, 面试{t['interviews']}场\n"

    prompt = f"""
你是求职数据分析专家。根据以下数据预测求职走向：

当前总投递: {total} 份
面试转化率: {stats.get('interview_rate', 0)}%
Offer率: {stats.get('offer_rate', 0)}%

近期趋势：
{trend_text}

请用2-3句话预测接下来的情况，并给出一条最关键的建议。语气积极、专业。
"""

    text = _call_deepseek(prompt)
    return text.strip() if text else None
