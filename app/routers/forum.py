"""
论坛路由：发帖、评论、通知
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.forum import ForumPost, ForumComment, ForumNotification

router = APIRouter(prefix="/api/forum", tags=["forum"])


def _author_name(user: User, is_anonymous: int) -> str:
    if is_anonymous:
        return "匿名用户"
    return user.username


def _create_notification(db: Session, user_id: int, post_id: int, ntype: str,
                         from_user_id: int, preview: str):
    """创建通知（自己回复自己则跳过）"""
    if user_id == from_user_id:
        return
    notif = ForumNotification(
        user_id=user_id,
        post_id=post_id,
        type=ntype,
        from_user_id=from_user_id,
        content_preview=preview[:50],
    )
    db.add(notif)
    db.commit()


# ═══════════ 帖子 ═══════════

@router.get("/posts")
def api_list_posts(
    page: int = 1,
    tag: str = None,
    search: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ForumPost)
    if tag:
        query = query.filter(ForumPost.tags.contains(tag))
    if search:
        query = query.filter(
            ForumPost.title.contains(search) |
            ForumPost.content.contains(search)
        )
    total = query.count()
    posts = query.order_by(ForumPost.created_at.desc()).offset(
        (page - 1) * 20).limit(20).all()

    return {
        "ok": True,
        "data": [{
            "id": p.id,
            "title": p.title,
            "content": p.content[:200] + ("..." if len(p.content or "") > 200 else ""),
            "tags": p.tags,
            "author_name": _author_name(p.author, p.is_anonymous),
            "is_anonymous": p.is_anonymous,
            "comment_count": p.comment_count,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
        } for p in posts],
        "total": total,
        "page": page,
        "pages": max(1, (total + 19) // 20),
    }


@router.get("/posts/{post_id}")
def api_get_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not p:
        raise HTTPException(404, detail="帖子不存在")

    comments = db.query(ForumComment).filter(
        ForumComment.post_id == post_id
    ).order_by(ForumComment.created_at.asc()).all()

    # 构建评论树
    comment_list = []
    children_map = {}
    for c in comments:
        item = {
            "id": c.id,
            "parent_id": c.parent_id,
            "content": c.content,
            "author_name": _author_name(c.author, c.is_anonymous),
            "is_anonymous": c.is_anonymous,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
        }
        if c.parent_id is None:
            comment_list.append(item)
            children_map[c.id] = item.setdefault("children", [])
        else:
            children_map.setdefault(c.parent_id, [])
            children_map[c.parent_id].append(item)

    return {
        "ok": True,
        "data": {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "tags": p.tags,
            "author_name": _author_name(p.author, p.is_anonymous),
            "is_anonymous": p.is_anonymous,
            "author_id": p.author_id,
            "comment_count": p.comment_count,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            "comments": comment_list,
        }
    }


@router.post("/posts")
async def api_create_post(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    body = await request.json()
    title = body.get("title", "").strip()
    content = body.get("content", "").strip()
    if not title or not content:
        return JSONResponse({"ok": False, "msg": "标题和内容不能为空"}, 400)

    post = ForumPost(
        author_id=user.id,
        title=title,
        content=content,
        tags=body.get("tags", ""),
        is_anonymous=body.get("is_anonymous", 0),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"ok": True, "data": {"id": post.id}}


@router.delete("/posts/{post_id}")
def api_delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not p:
        raise HTTPException(404, detail="帖子不存在")
    if p.author_id != user.id and not user.is_admin:
        raise HTTPException(403, detail="无权删除")
    db.delete(p)
    db.commit()
    return {"ok": True}


# ═══════════ 评论 ═══════════

@router.post("/posts/{post_id}/comments")
async def api_create_comment(
    post_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not p:
        raise HTTPException(404, detail="帖子不存在")

    body = await request.json()
    content = body.get("content", "").strip()
    if not content:
        return JSONResponse({"ok": False, "msg": "评论内容不能为空"}, 400)

    parent_id = body.get("parent_id")
    is_anonymous = body.get("is_anonymous", 0)

    parent_author_id = None
    if parent_id:
        parent = db.query(ForumComment).filter(
            ForumComment.id == parent_id,
            ForumComment.post_id == post_id,
        ).first()
        if not parent:
            return JSONResponse({"ok": False, "msg": "要回复的评论不存在"}, 400)
        parent_author_id = parent.author_id

    comment = ForumComment(
        post_id=post_id,
        author_id=user.id,
        parent_id=parent_id,
        content=content,
        is_anonymous=is_anonymous,
    )
    db.add(comment)
    p.comment_count = (p.comment_count or 0) + 1
    db.commit()
    db.refresh(comment)

    # 发通知
    preview = content[:50]
    if parent_id and parent_author_id:
        _create_notification(db, parent_author_id, post_id, "comment_reply", user.id, preview)
    elif not parent_id:
        _create_notification(db, p.author_id, post_id, "post_reply", user.id, preview)

    return {
        "ok": True,
        "data": {
            "id": comment.id,
            "author_name": _author_name(user, is_anonymous),
            "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M") if comment.created_at else "",
        }
    }


@router.delete("/comments/{comment_id}")
def api_delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    if not c:
        raise HTTPException(404, detail="评论不存在")
    if c.author_id != user.id and not user.is_admin:
        raise HTTPException(403, detail="无权删除")

    p = db.query(ForumPost).filter(ForumPost.id == c.post_id).first()
    children_count = db.query(ForumComment).filter(
        ForumComment.parent_id == comment_id
    ).count()
    if p:
        p.comment_count = max(0, (p.comment_count or 0) - 1 - children_count)

    db.query(ForumComment).filter(ForumComment.parent_id == comment_id).delete()
    db.delete(c)
    db.commit()
    return {"ok": True}


# ═══════════ 通知 ═══════════

@router.get("/notifications")
def api_list_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifs = db.query(ForumNotification).filter(
        ForumNotification.user_id == user.id
    ).order_by(ForumNotification.created_at.desc()).limit(50).all()

    return {
        "ok": True,
        "data": [{
            "id": n.id,
            "post_id": n.post_id,
            "type": n.type,
            "from_user_name": n.from_user.username,
            "content_preview": n.content_preview,
            "is_read": n.is_read,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M") if n.created_at else "",
        } for n in notifs],
    }


@router.get("/notifications/unread-count")
def api_unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = db.query(func.count(ForumNotification.id)).filter(
        ForumNotification.user_id == user.id,
        ForumNotification.is_read == 0,
    ).scalar() or 0
    return {"ok": True, "count": count}


@router.post("/notifications/{notif_id}/read")
def api_read_notification(
    notif_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(ForumNotification).filter(
        ForumNotification.id == notif_id,
        ForumNotification.user_id == user.id,
    ).first()
    if n:
        n.is_read = 1
        db.commit()
    return {"ok": True}


@router.post("/notifications/read-all")
def api_read_all_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(ForumNotification).filter(
        ForumNotification.user_id == user.id,
        ForumNotification.is_read == 0,
    ).update({"is_read": 1})
    db.commit()
    return {"ok": True}
