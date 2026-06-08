/**
 * JobPilot — 求职论坛 JS
 */

// ═══════════ 帖子列表 ═══════════

async function loadPosts(page = 1) {
    const search = document.getElementById('forumSearch')?.value || '';
    const tag = document.getElementById('forumTag')?.value || '';
    const params = new URLSearchParams({ page, search, tag });

    try {
        const r = await fetch(`/api/forum/posts?${params}`);
        const d = await r.json();
        if (!d.ok) return;

        const container = document.getElementById('postList');
        if (!d.data.length) {
            container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:40px;">暂无帖子，来写第一篇吧 ✍️</p>';
            document.getElementById('postPager').innerHTML = '';
            return;
        }

        container.innerHTML = d.data.map(p => `
            <div class="card" style="margin-bottom:12px;cursor:pointer;" onclick="location.href='/forum/${p.id}'">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;">
                        <h3 style="margin:0 0 6px;font-size:1.1rem;">${escHtml(p.title)}</h3>
                        <p style="color:var(--text-muted);font-size:.85rem;margin:0 0 8px;line-height:1.5;">${escHtml(p.content)}</p>
                        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                            ${p.tags ? p.tags.split(',').filter(Boolean).map(t => `<span class="tag">${escHtml(t.trim())}</span>`).join('') : ''}
                            <span style="font-size:.75rem;color:var(--text-muted);">👤 ${escHtml(p.author_name)}</span>
                            <span style="font-size:.75rem;color:var(--text-muted);">💬 ${p.comment_count}</span>
                            <span style="font-size:.75rem;color:var(--text-muted);">🕐 ${p.created_at}</span>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        const pager = document.getElementById('postPager');
        pager.innerHTML = '';
        for (let i = 1; i <= d.pages; i++) {
            const btn = document.createElement('button');
            btn.className = `btn btn-sm ${i === page ? 'btn-primary' : 'btn-outline'}`;
            btn.textContent = i;
            btn.onclick = () => loadPosts(i);
            pager.appendChild(btn);
        }
    } catch (e) {
        console.error(e);
    }
}

function openNewPost() {
    document.getElementById('newPostModal').style.display = 'flex';
}
function closeNewPost() {
    document.getElementById('newPostModal').style.display = 'none';
    document.getElementById('newPostForm').reset();
}

async function submitPost(e) {
    e.preventDefault();
    const title = document.getElementById('postTitle').value.trim();
    const content = document.getElementById('postContent').value.trim();
    const tags = document.getElementById('postTags').value.trim();
    const is_anonymous = document.getElementById('postAnonymous').checked ? 1 : 0;

    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true; btn.textContent = '发布中...';

    try {
        const r = await fetch('/api/forum/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content, tags, is_anonymous }),
        });
        const d = await r.json();
        if (d.ok) {
            closeNewPost();
            window.location.href = `/forum/${d.data.id}`;
        } else {
            alert(d.msg);
        }
    } catch (err) {
        alert('网络错误');
    }
    btn.disabled = false; btn.textContent = '发布帖子';
}

function escHtml(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

// ═══════════ 帖子详情 & 评论 ═══════════

let currentPost = null;

async function loadPostDetail() {
    if (typeof POST_ID === 'undefined') return;
    try {
        const r = await fetch(`/api/forum/posts/${POST_ID}`);
        const d = await r.json();
        if (!d.ok) { alert('帖子不存在'); return; }
        currentPost = d.data;

        document.getElementById('postDetail').innerHTML = `
            <h1 style="margin-bottom:8px;">${escHtml(currentPost.title)}</h1>
            <div style="color:var(--text-muted);font-size:.85rem;margin-bottom:16px;">
                👤 ${escHtml(currentPost.author_name)} · 🕐 ${currentPost.created_at}
                ${currentPost.tags ? '· ' + currentPost.tags.split(',').filter(Boolean).map(t => `<span class="tag">${escHtml(t.trim())}</span>`).join('') : ''}
                ${canDeletePost() ? `· <button class="btn btn-sm btn-outline" style="color:#EF4444;" onclick="deletePost()">🗑️ 删除</button>` : ''}
            </div>
            <div style="line-height:1.8;white-space:pre-wrap;">${escHtml(currentPost.content)}</div>
        `;

        document.getElementById('commentCount').textContent = `💬 评论 (${currentPost.comment_count})`;
        renderComments(currentPost.comments);
    } catch (e) {
        console.error(e);
    }
}

function renderComments(comments) {
    const container = document.getElementById('commentList');
    if (!comments || !comments.length) {
        container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px;">暂无评论，来发表第一条吧 💬</p>';
        return;
    }
    container.innerHTML = comments.map(c => renderCommentItem(c, 0)).join('');
}

function renderCommentItem(c, depth) {
    const ml = depth * 24;
    const childrenHtml = (c.children || []).map(ch => renderCommentItem(ch, depth + 1)).join('');
    return `
        <div style="margin-left:${ml}px;padding:12px;border-left:3px solid ${depth > 0 ? 'var(--border)' : 'var(--primary)'};margin-bottom:8px;background:var(--bg-muted);border-radius:4px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <span style="font-size:.8rem;font-weight:600;">${escHtml(c.author_name)}</span>
                <span style="font-size:.7rem;color:var(--text-muted);">${c.created_at}</span>
            </div>
            <p style="margin:0 0 6px;white-space:pre-wrap;">${escHtml(c.content)}</p>
            <div style="display:flex;gap:12px;">
                <button class="btn btn-sm btn-outline" style="font-size:.7rem;" onclick="replyTo(${c.id}, '${escHtml(c.author_name).replace(/'/g, "\\'")}')">💬 回复</button>
                <button class="btn btn-sm btn-outline" style="font-size:.7rem;color:#EF4444;" onclick="deleteComment(${c.id})">🗑️</button>
            </div>
            ${childrenHtml}
        </div>
    `;
}

function replyTo(commentId, name) {
    document.getElementById('commentParentId').value = commentId;
    document.getElementById('replyHint').style.display = 'block';
    document.getElementById('replyToName').textContent = name;
    document.getElementById('commentContent').focus();
}

function cancelReply() {
    document.getElementById('commentParentId').value = '';
    document.getElementById('replyHint').style.display = 'none';
}

async function submitComment(e) {
    e.preventDefault();
    const content = document.getElementById('commentContent').value.trim();
    const parentId = document.getElementById('commentParentId').value || null;
    const is_anonymous = document.getElementById('commentAnonymous').checked ? 1 : 0;
    if (!content) return;

    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true; btn.textContent = '发表中...';

    try {
        const r = await fetch(`/api/forum/posts/${POST_ID}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, parent_id: parentId, is_anonymous }),
        });
        const d = await r.json();
        if (d.ok) {
            document.getElementById('commentContent').value = '';
            cancelReply();
            loadPostDetail();
        } else {
            alert(d.msg);
        }
    } catch (err) {
        alert('网络错误');
    }
    btn.disabled = false; btn.textContent = '发表评论';
}

function canDeletePost() {
    return currentPost && currentPost.author_id;
}

async function deletePost() {
    if (!confirm('确定删除这个帖子吗？所有评论也会被删除。')) return;
    try {
        const r = await fetch(`/api/forum/posts/${POST_ID}`, { method: 'DELETE' });
        const d = await r.json();
        if (d.ok) {
            window.location.href = '/forum';
        } else {
            alert(d.detail || '删除失败');
        }
    } catch (err) {
        alert('网络错误');
    }
}

async function deleteComment(commentId) {
    if (!confirm('确定删除这条评论吗？')) return;
    try {
        const r = await fetch(`/api/forum/comments/${commentId}`, { method: 'DELETE' });
        const d = await r.json();
        if (d.ok) {
            loadPostDetail();
        } else {
            alert(d.detail || '删除失败');
        }
    } catch (err) {
        alert('网络错误');
    }
}

// ═══════════ 通知 ═══════════

async function loadNotifications() {
    try {
        const [nr, cr] = await Promise.all([
            fetch('/api/forum/notifications'),
            fetch('/api/forum/notifications/unread-count'),
        ]);
        const nd = await nr.json();
        const cd = await cr.json();

        const badge = document.getElementById('notifBadge');
        if (badge) {
            badge.textContent = cd.count;
            badge.style.display = cd.count > 0 ? 'inline' : 'none';
        }

        const list = document.getElementById('notifDropdown');
        if (!list || list.style.display === 'none') return;

        if (!nd.data || !nd.data.length) {
            list.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:12px;">暂无通知</p>';
            return;
        }

        list.innerHTML = nd.data.map(n => `
            <div class="notif-item" style="padding:10px 12px;border-bottom:1px solid var(--border);cursor:pointer;
                ${n.is_read ? '' : 'background:rgba(79,70,229,0.05);font-weight:600;'}"
                onclick="goToPost(${n.post_id}, ${n.id})">
                <p style="margin:0;font-size:.85rem;">
                    ${n.type === 'post_reply' ? '💬' : '↩️'} <b>${escHtml(n.from_user_name)}</b> 回复了你
                </p>
                <p style="margin:2px 0 0;font-size:.75rem;color:var(--text-muted);">${escHtml(n.content_preview)}</p>
                <p style="margin:2px 0 0;font-size:.7rem;color:var(--text-muted);">${n.created_at}</p>
            </div>
        `).join('');

        list.innerHTML += `
            <div style="text-align:center;padding:8px;border-top:1px solid var(--border);">
                <button class="btn btn-sm btn-outline" onclick="readAllNotifications()" style="font-size:.75rem;">全部已读</button>
            </div>
        `;
    } catch (e) { console.error(e); }
}

async function goToPost(postId, notifId) {
    await fetch(`/api/forum/notifications/${notifId}/read`, { method: 'POST' });
    window.location.href = `/forum/${postId}`;
}

async function readAllNotifications() {
    await fetch('/api/forum/notifications/read-all', { method: 'POST' });
    loadNotifications();
}

function toggleNotifDropdown() {
    const list = document.getElementById('notifDropdown');
    const show = list.style.display === 'none' || !list.style.display;
    list.style.display = show ? 'block' : 'none';
    if (show) loadNotifications();
}

document.addEventListener('click', (e) => {
    const bell = document.getElementById('notifBell');
    const list = document.getElementById('notifDropdown');
    if (bell && list && !bell.contains(e.target) && !list.contains(e.target)) {
        list.style.display = 'none';
    }
});

// ═══════════ 初始化 ═══════════
document.addEventListener('DOMContentLoaded', () => {
    if (typeof POST_ID !== 'undefined') {
        loadPostDetail();
    } else {
        loadPosts();
    }
    loadNotifications();
    setInterval(() => loadNotifications(), 30000);
});
