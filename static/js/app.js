/**
 * JobPilot — 看板交互逻辑
 */

const STATUS_LABELS = {
    applied: '📥 已投递',
    assessment: '📝 测评/笔试',
    interview: '🎤 面试中',
    waiting: '⏳ 等结果',
    offer: '✅ Offer',
    rejected: '❌ 已挂',
};

let allApps = [];

// ============================================================
// 页面加载
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    loadApplications();
    loadInterviews();
    initSortable();
    // 点击遮罩关闭弹窗
    document.getElementById('appModal').addEventListener('click', e => {
        if (e.target === document.getElementById('appModal')) closeModal();
    });
    document.getElementById('statsModal').addEventListener('click', e => {
        if (e.target === document.getElementById('statsModal')) closeStats();
    });
});

// ============================================================
// 加载数据 & 渲染
// ============================================================
async function loadApplications() {
    try {
        const r = await fetch('/api/applications');
        const data = await r.json();
        if (data.ok) {
            allApps = data.data;
            renderKanban();
        }
    } catch (e) {
        console.error('加载失败:', e);
    }
}

function renderKanban() {
    // 按状态分组
    const groups = {};
    for (const status of Object.keys(STATUS_LABELS)) {
        groups[status] = [];
    }
    for (const app of allApps) {
        if (groups[app.status]) {
            groups[app.status].push(app);
        }
    }

    for (const [status, apps] of Object.entries(groups)) {
        const col = document.getElementById(`col-${status}`);
        const count = document.getElementById(`count-${status}`);
        if (!col) continue;

        col.innerHTML = apps.map(a => cardHTML(a)).join('');
        if (count) count.textContent = apps.length;
    }
}

function cardHTML(app) {
    const stars = '⭐'.repeat(app.priority);
    // 统计该投递的面试数量
    const ivCount = allInterviews.filter(i => i.application_id === app.id).length;
    return `
    <div class="app-card priority-${app.priority}" data-id="${app.id}"
         ondblclick="editApplication(${app.id})">
        <div class="card-actions">
            <button onclick="openInterviewForm(${app.id})" title="添加面试">📅</button>
            <button onclick="editApplication(${app.id})" title="编辑">✏️</button>
            <button onclick="deleteApplication(${app.id})" title="删除">🗑️</button>
        </div>
        <div class="card-company">${esc(app.company)}</div>
        <div class="card-position">${esc(app.position)}</div>
        <div class="card-meta">
            ${app.location ? `<span>📍 ${esc(app.location)}</span>` : ''}
            ${app.salary_range ? `<span>💰 ${esc(app.salary_range)}</span>` : ''}
            <span>${stars}</span>
            ${app.source !== '其他' ? `<span>🏷️ ${esc(app.source)}</span>` : ''}
            <span style="font-size:.7rem;color:#94A3B8">${app.applied_date}</span>
        </div>
        ${ivCount > 0 ? `<div class="card-interview-badge">📅 ${ivCount}场面试</div>` : ''}
    </div>`;
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// ============================================================
// SortableJS — 拖拽
// ============================================================
function initSortable() {
    const cols = document.querySelectorAll('.col-body');
    for (const col of cols) {
        new Sortable(col, {
            group: 'applications',
            animation: 200,
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            onEnd: async function (evt) {
                const cardEl = evt.item;
                const appId = parseInt(cardEl.dataset.id);
                const newStatus = evt.to.closest('.kanban-col').dataset.status;

                // 乐观更新
                const app = allApps.find(a => a.id === appId);
                if (app) app.status = newStatus;
                renderKanban();

                // 发请求
                await fetch(`/api/applications/${appId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus }),
                });
            },
        });
    }
}

// ============================================================
// 新增 & 编辑
// ============================================================
function openAddModal() {
    document.getElementById('appId').value = '';
    document.getElementById('modalTitle').textContent = '+ 新增投递';
    document.getElementById('appForm').reset();
    document.getElementById('rowRejectReason').style.display = 'none';
    document.getElementById('rowOfferSalary').style.display = 'none';
    document.getElementById('appModal').classList.add('open');
}

function editApplication(id) {
    const app = allApps.find(a => a.id === id);
    if (!app) return;

    document.getElementById('appId').value = app.id;
    document.getElementById('modalTitle').textContent = '✏️ 编辑投递';
    document.getElementById('company').value = app.company;
    document.getElementById('position').value = app.position;
    document.getElementById('location').value = app.location || '';
    document.getElementById('salary_range').value = app.salary_range || '';
    document.getElementById('source').value = app.source || '其他';
    document.getElementById('priority').value = app.priority;
    document.getElementById('jd_link').value = app.jd_link || '';
    document.getElementById('job_category').value = app.job_category || '';
    document.getElementById('rejection_reason').value = app.rejection_reason || '';
    document.getElementById('offer_salary').value = app.offer_salary || '';
    document.getElementById('notes').value = app.notes || '';
    // 根据状态显示挂因/Offer薪资
    document.getElementById('rowRejectReason').style.display = app.status === 'rejected' ? 'flex' : 'none';
    document.getElementById('rowOfferSalary').style.display = app.status === 'offer' ? 'flex' : 'none';
    document.getElementById('appModal').classList.add('open');
}

function closeModal() {
    document.getElementById('appModal').classList.remove('open');
}

async function saveApplication(e) {
    e.preventDefault();
    const btn = document.getElementById('saveBtn');
    btn.disabled = true;
    btn.textContent = '保存中...';

    const appId = document.getElementById('appId').value;
    const form = new FormData();
    form.append('company', document.getElementById('company').value);
    form.append('position', document.getElementById('position').value);
    form.append('location', document.getElementById('location').value);
    form.append('salary_range', document.getElementById('salary_range').value);
    form.append('source', document.getElementById('source').value);
    form.append('priority', document.getElementById('priority').value);
    form.append('jd_link', document.getElementById('jd_link').value);
    form.append('job_category', document.getElementById('job_category').value);
    form.append('rejection_reason', document.getElementById('rejection_reason').value);
    form.append('offer_salary', document.getElementById('offer_salary').value);
    form.append('notes', document.getElementById('notes').value);

    try {
        let r;
        if (appId) {
            const body = {};
            for (const [k, v] of form.entries()) body[k] = v;
            r = await fetch(`/api/applications/${appId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
        } else {
            r = await fetch('/api/applications', { method: 'POST', body: form });
        }
        const data = await r.json();
        if (data.ok) {
            closeModal();
            await loadApplications();
        }
    } catch (e) {
        console.error('保存失败:', e);
    }
    btn.disabled = false;
    btn.textContent = '保存';
}

async function deleteApplication(id) {
    if (!confirm('确定删除这条投递记录吗？')) return;
    await fetch(`/api/applications/${id}`, { method: 'DELETE' });
    await loadApplications();
}

// ============================================================
// 统计面板
// ============================================================
async function openStats() {
    document.getElementById('statsModal').classList.add('open');
    try {
        const r = await fetch('/api/analytics/stats');
        const data = await r.json();
        if (!data.ok) return;

        document.getElementById('statTotal').textContent = data.total;
        document.getElementById('statInterview').textContent = data.by_status.interview || 0;
        document.getElementById('statOffer').textContent = data.by_status.offer || 0;

        const passed = (data.by_status.assessment || 0) + (data.by_status.interview || 0) +
                       (data.by_status.waiting || 0) + (data.by_status.offer || 0);
        const rate = data.total > 0 ? Math.round(passed / data.total * 100) : 0;
        document.getElementById('statRate').textContent = rate + '%';

        // ECharts 图表
        renderCharts(data);
    } catch (e) {
        console.error('加载统计失败:', e);
    }
}

function closeStats() {
    document.getElementById('statsModal').classList.remove('open');
}

function renderCharts(data) {
    const container = document.getElementById('statsCharts');
    if (!container) return;
    container.innerHTML = '<div class="chart-box" id="chartStatus"></div><div class="chart-box" id="chartSource"></div>';

    // 状态分布饼图
    const statusChart = echarts.init(document.getElementById('chartStatus'));
    const statusData = Object.entries(data.by_status).map(([k, v]) => ({
        name: STATUS_LABELS[k] || k, value: v,
    }));
    statusChart.setOption({
        title: { text: '投递状态分布', left: 'center', textStyle: { fontSize: 14 } },
        tooltip: { trigger: 'item' },
        series: [{
            type: 'pie', radius: ['40%', '70%'],
            data: statusData,
            label: { formatter: '{b}\n{d}%' },
            color: ['#94A3B8', '#F59E0B', '#4F46E5', '#8B5CF6', '#10B981', '#EF4444'],
        }],
    });

    // 渠道柱状图
    const sourceChart = echarts.init(document.getElementById('chartSource'));
    const sourceData = Object.entries(data.by_source);
    sourceChart.setOption({
        title: { text: '投递渠道分布', left: 'center', textStyle: { fontSize: 14 } },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: sourceData.map(([k]) => k) },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
            type: 'bar', data: sourceData.map(([, v]) => v),
            itemStyle: { color: '#4F46E5', borderRadius: [6, 6, 0, 0] },
        }],
    });
}

// ============================================================
// 面试日程
// ============================================================
let allInterviews = [];

async function openInterviews() {
    document.getElementById('interviewsModal').classList.add('open');
    await loadInterviews();
}

function closeInterviews() {
    document.getElementById('interviewsModal').classList.remove('open');
}

async function loadInterviews() {
    try {
        const r = await fetch('/api/interviews');
        const data = await r.json();
        if (data.ok) {
            allInterviews = data.data;
            renderInterviewList();
            renderKanban();  // 更新卡片上的面试标记
        }
    } catch (e) {
        console.error('加载面试失败:', e);
    }
}

function renderInterviewList() {
    const container = document.getElementById('interviewList');
    const upcoming = allInterviews.filter(iv => iv.interview_status === 'scheduled');
    const past = allInterviews.filter(iv => iv.interview_status !== 'scheduled');

    if (allInterviews.length === 0) {
        container.innerHTML = `
            <div class="iv-empty">
                <div class="iv-empty-icon">📅</div>
                <p>还没有面试安排</p>
                <p style="font-size:.82rem;">点击"+ 添加面试"或在看板卡片上快捷添加</p>
            </div>`;
        return;
    }

    const statusBadge = (s) => {
        if (s === 'scheduled') return '<span style="color:#4F46E5;">⏳ 待面试</span>';
        if (s === 'done') return '<span style="color:#10B981;">✅ 已完成</span>';
        if (s === 'cancelled') return '<span style="color:#EF4444;">❌ 已取消</span>';
        return s;
    };

    const itemHTML = (iv) => `
        <div class="interview-item ${iv.interview_status === 'done' ? 'iv-done' : ''} ${iv.interview_status === 'cancelled' ? 'iv-cancelled' : ''}">
            <div class="iv-time">
                ${iv.scheduled_time ? formatTime(iv.scheduled_time) : '<span style="color:#94A3B8;">待定</span>'}
            </div>
            <div class="iv-info">
                <div class="iv-company">${esc(iv.company)} — ${esc(iv.position)}</div>
                <div class="iv-detail">
                    ${iv.round} · ${iv.interview_type}
                    ${iv.interviewer ? ' · 面试官: ' + esc(iv.interviewer) : ''}
                    ${statusBadge(iv.interview_status)}
                </div>
            </div>
            <div class="iv-actions">
                ${iv.interview_status === 'scheduled' ? `
                    <button onclick="markInterviewDone(${iv.id})" title="标记完成">✅</button>
                    <button onclick="editInterview(${iv.id})" title="编辑">✏️</button>
                    <button onclick="cancelInterview(${iv.id})" title="取消">❌</button>
                ` : `
                    <button onclick="editInterview(${iv.id})" title="编辑">✏️</button>
                    <button onclick="deleteInterview(${iv.id})" title="删除">🗑️</button>
                `}
                <button onclick="openNoteForm(${iv.id})" title="写面经" style="color:var(--primary);border-color:var(--primary);">📝</button>
            </div>
        </div>`;

    let html = '';
    if (upcoming.length > 0) {
        html += '<h4 style="margin-bottom:10px;">🔔 即将到来 (' + upcoming.length + ')</h4>';
        html += upcoming.map(itemHTML).join('');
    }
    if (past.length > 0) {
        html += '<h4 style="margin:16px 0 10px;">📝 历史记录</h4>';
        html += past.map(itemHTML).join('');
    }
    container.innerHTML = html;
}

function formatTime(isoStr) {
    const d = new Date(isoStr);
    const now = new Date();
    // 用日期（去掉时分秒）比较，避免Math.ceil把当天算成明天
    const dDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const nDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffDays = Math.round((dDate - nDate) / (1000 * 60 * 60 * 24));

    let dayLabel = '';
    if (diffDays === 0) dayLabel = '<span style="color:#EF4444;font-size:.7rem;">今天!</span>';
    else if (diffDays === 1) dayLabel = '<span style="color:#F59E0B;font-size:.7rem;">明天</span>';
    else if (diffDays < 0) dayLabel = `<span style="color:#EF4444;font-size:.7rem;">已过期</span>`;
    else if (diffDays <= 3) dayLabel = `<span style="font-size:.7rem;">${diffDays}天后</span>`;
    else dayLabel = `<span style="font-size:.7rem;">${diffDays}天后</span>`;

    const time = d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    const date = d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', weekday: 'short' });
    return `<div>${time}</div><div class="iv-date">${date}</div>${dayLabel}`;
}

// ---- 面试表单 ----
async function openInterviewForm(appId) {
    document.getElementById('ivId').value = '';
    document.getElementById('ivAppId').value = appId || '';
    document.getElementById('ivFormTitle').textContent = '添加面试';
    document.getElementById('interviewForm').reset();

    // 填充投递下拉
    const select = document.getElementById('ivAppSelect');
    select.innerHTML = allApps.map(a =>
        `<option value="${a.id}" ${a.id === appId ? 'selected' : ''}>${esc(a.company)} — ${esc(a.position)}</option>`
    ).join('');
    if (allApps.length === 0) {
        select.innerHTML = '<option value="">请先创建投递记录</option>';
    }

    // 默认时间设为明天10点
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);
    const localStr = tomorrow.toISOString().slice(0, 16);
    document.getElementById('ivTime').value = localStr;

    document.getElementById('interviewFormModal').classList.add('open');
}

function closeInterviewForm() {
    document.getElementById('interviewFormModal').classList.remove('open');
}

function editInterview(id) {
    const iv = allInterviews.find(i => i.id === id);
    if (!iv) return;

    document.getElementById('ivId').value = iv.id;
    document.getElementById('ivAppId').value = iv.application_id;
    document.getElementById('ivFormTitle').textContent = '编辑面试';
    document.getElementById('ivRound').value = iv.round;
    document.getElementById('ivType').value = iv.interview_type;
    document.getElementById('ivInterviewer').value = iv.interviewer || '';
    document.getElementById('ivNotes').value = iv.notes || '';
    if (iv.scheduled_time) {
        document.getElementById('ivTime').value = iv.scheduled_time.slice(0, 16);
    }

    const select = document.getElementById('ivAppSelect');
    select.innerHTML = allApps.map(a =>
        `<option value="${a.id}" ${a.id === iv.application_id ? 'selected' : ''}>${esc(a.company)} — ${esc(a.position)}</option>`
    ).join('');

    document.getElementById('interviewFormModal').classList.add('open');
}

async function saveInterview(e) {
    e.preventDefault();
    const btn = document.getElementById('ivSaveBtn');
    btn.disabled = true; btn.textContent = '保存中...';

    const ivId = document.getElementById('ivId').value;
    const appId = document.getElementById('ivAppId').value || document.getElementById('ivAppSelect').value;

    const formData = new FormData();
    formData.append('round', document.getElementById('ivRound').value);
    formData.append('scheduled_time', document.getElementById('ivTime').value);
    formData.append('interviewer', document.getElementById('ivInterviewer').value);
    formData.append('interview_type', document.getElementById('ivType').value);
    formData.append('notes', document.getElementById('ivNotes').value);

    try {
        let r;
        if (ivId) {
            const body = {};
            body['round'] = document.getElementById('ivRound').value;
            body['scheduled_time'] = document.getElementById('ivTime').value;
            body['interviewer'] = document.getElementById('ivInterviewer').value;
            body['interview_type'] = document.getElementById('ivType').value;
            body['notes'] = document.getElementById('ivNotes').value;
            r = await fetch(`/api/interviews/${ivId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
        } else {
            r = await fetch(`/api/applications/${appId}/interviews`, {
                method: 'POST', body: formData,
            });
        }
        const data = await r.json();
        if (data.ok) {
            closeInterviewForm();
            await loadInterviews();
        }
    } catch (e) {
        console.error('保存失败:', e);
    }
    btn.disabled = false; btn.textContent = '保存';
}

async function markInterviewDone(id) {
    await fetch(`/api/interviews/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interview_status: 'done' }),
    });
    await loadInterviews();
}

async function cancelInterview(id) {
    if (!confirm('确定取消这场面试吗？')) return;
    await fetch(`/api/interviews/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interview_status: 'cancelled' }),
    });
    await loadInterviews();
}

async function deleteInterview(id) {
    if (!confirm('确定删除这条面试记录吗？')) return;
    await fetch(`/api/interviews/${id}`, { method: 'DELETE' });
    await loadInterviews();
}

// ---- 浏览器通知 ----
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

async function checkUpcomingInterviews() {
    try {
        const r = await fetch('/api/interviews/upcoming');
        const data = await r.json();
        if (!data.ok || data.data.length === 0) return;

        for (const iv of data.data) {
            if (!iv.scheduled_time) continue;
            const t = new Date(iv.scheduled_time);
            const now = new Date();
            const diffMin = Math.floor((t - now) / 60000);

            // 1小时内的面试弹通知
            if (diffMin > 0 && diffMin <= 60 && !sessionStorage.getItem('notified_' + iv.id)) {
                if ('Notification' in window && Notification.permission === 'granted') {
                    new Notification(`⏰ 面试提醒 — ${iv.company}`, {
                        body: `${iv.position} · ${iv.round} · ${iv.interview_type}\n${t.toLocaleTimeString('zh-CN')}`,
                        icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">📅</text></svg>',
                    });
                }
                sessionStorage.setItem('notified_' + iv.id, '1');
            }
        }
    } catch (e) { /* 静默失败 */ }
}

// 每5分钟检查一次
setInterval(checkUpcomingInterviews, 5 * 60 * 1000);
// 页面加载时请求通知权限
document.addEventListener('DOMContentLoaded', () => {
    requestNotificationPermission();
    checkUpcomingInterviews();
});

// ============================================================
// 面经库
// ============================================================
let allNotes = [];

async function openNotes() {
    document.getElementById('notesModal').classList.add('open');
    document.getElementById('notesSearch').value = '';
    await loadNotes();
}

function closeNotes() {
    document.getElementById('notesModal').classList.remove('open');
}

async function loadNotes() {
    const search = document.getElementById('notesSearch')?.value || '';
    try {
        const r = await fetch('/api/notes' + (search ? '?search=' + encodeURIComponent(search) : ''));
        const data = await r.json();
        if (data.ok) {
            allNotes = data.data;
            renderNotesList();
        }
    } catch (e) {
        console.error('加载面经失败:', e);
    }
}

function renderNotesList() {
    const container = document.getElementById('notesContent');
    if (!container) return;

    if (allNotes.length === 0) {
        container.innerHTML = `
            <div class="iv-empty">
                <div class="iv-empty-icon">📝</div>
                <p>还没有面经记录</p>
                <p style="font-size:.82rem;">在面试日程中点击"📝"按钮记录面经</p>
            </div>`;
        return;
    }

    // 提取所有标签
    const tagCount = {};
    allNotes.forEach(n => {
        if (n.tags) {
            n.tags.split(',').map(t => t.trim()).filter(Boolean).forEach(t => {
                tagCount[t] = (tagCount[t] || 0) + 1;
            });
        }
    });

    let html = '';
    // 标签筛选
    if (Object.keys(tagCount).length > 0) {
        html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;">';
        html += '<span style="font-size:.82rem;color:var(--text-muted);">标签筛选：</span>';
        html += Object.entries(tagCount).map(([t, c]) =>
            `<span class="note-tag" onclick="filterByTag('${esc(t)}')">${esc(t)} (${c})</span>`
        ).join('');
        html += '</div>';
    }

    allNotes.forEach(n => {
        let qas = [];
        try { qas = JSON.parse(n.questions_answers); } catch(e) {}
        const tags = n.tags ? n.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

        html += `
        <div class="note-card">
            <div class="note-header">
                <div>
                    <strong>${esc(n.company)}</strong> — ${esc(n.position)} · ${esc(n.round)}
                    <span style="font-size:.75rem;color:var(--text-muted);margin-left:8px;">${n.created_at}</span>
                </div>
                <div class="note-actions">
                    <button onclick="editNote(${n.id})" title="编辑">✏️</button>
                    <button onclick="deleteNote(${n.id})" title="删除">🗑️</button>
                </div>
            </div>
            ${tags.length > 0 ? `<div style="margin:6px 0;">${tags.map(t => `<span class="note-tag">${esc(t)}</span>`).join('')}</div>` : ''}
            ${qas.length > 0 ? `
                <div class="note-qa-list">
                    ${qas.map((qa, i) => `
                        <div class="note-qa-item">
                            <div class="qa-q"><strong>Q${i+1}:</strong> ${esc(qa.q)}</div>
                            <div class="qa-a"><strong>A:</strong> ${esc(qa.a)}</div>
                        </div>
                    `).join('')}
                </div>
            ` : '<p style="color:var(--text-muted);font-size:.82rem;">暂无问答记录</p>'}
            ${n.reflection ? `<div class="note-reflection"><strong>💡 复盘：</strong>${esc(n.reflection)}</div>` : ''}
        </div>`;
    });
    container.innerHTML = html;
}

function filterByTag(tag) {
    document.getElementById('notesSearch').value = tag;
    loadNotes();
}

// ---- 面经编辑 ----
async function openNoteForm(interviewId) {
    document.getElementById('noteId').value = '';
    document.getElementById('noteInterviewId').value = interviewId || '';
    document.getElementById('noteFormTitle').textContent = '写面经';
    document.getElementById('noteReflection').value = '';
    document.getElementById('noteTags').value = '';
    document.getElementById('qaList').innerHTML = '';

    // 填充面试下拉
    const select = document.getElementById('noteInterviewSelect');
    const doneInterviews = allInterviews.filter(iv => iv.interview_status === 'done');
    select.innerHTML = doneInterviews.map(iv =>
        `<option value="${iv.id}" ${iv.id === interviewId ? 'selected' : ''}>
            ${esc(iv.company)} — ${esc(iv.position)} · ${iv.round} @ ${iv.scheduled_time || ''}
        </option>`
    ).join('');
    if (doneInterviews.length === 0) {
        select.innerHTML = '<option value="">暂无已完成的面试，请先在日程中标记完成</option>';
    }

    // 初始化3个空Q&A
    document.getElementById('qaList').innerHTML = '';
    for (let i = 0; i < 3; i++) addQA();

    document.getElementById('noteFormModal').classList.add('open');
}

function closeNoteForm() {
    document.getElementById('noteFormModal').classList.remove('open');
}

function addQA() {
    const container = document.getElementById('qaList');
    const idx = container.children.length;
    const div = document.createElement('div');
    div.className = 'qa-row';
    div.innerHTML = `
        <input type="text" class="qa-q-input" placeholder="Q${idx+1}: 面试官问了什么？">
        <input type="text" class="qa-a-input" placeholder="A${idx+1}: 你是怎么回答的？">
        <button type="button" class="qa-remove" onclick="this.parentElement.remove()">✕</button>
    `;
    container.appendChild(div);
}

async function editNote(noteId) {
    const note = allNotes.find(n => n.id === noteId);
    if (!note) return;

    document.getElementById('noteId').value = note.id;
    document.getElementById('noteInterviewId').value = note.interview_id;
    document.getElementById('noteFormTitle').textContent = '编辑面经';
    document.getElementById('noteReflection').value = note.reflection || '';
    document.getElementById('noteTags').value = note.tags || '';

    // 填充面试下拉
    const select = document.getElementById('noteInterviewSelect');
    select.innerHTML = allInterviews.map(iv =>
        `<option value="${iv.id}" ${iv.id === note.interview_id ? 'selected' : ''}>
            ${esc(iv.company)} — ${esc(iv.position)} · ${iv.round}
        </option>`
    ).join('');

    // 填充Q&A
    const qaList = document.getElementById('qaList');
    qaList.innerHTML = '';
    let qas = [];
    try { qas = JSON.parse(note.questions_answers); } catch(e) {}
    if (qas.length === 0) {
        for (let i = 0; i < 3; i++) addQA();
    } else {
        qas.forEach(qa => {
            const div = document.createElement('div');
            div.className = 'qa-row';
            div.innerHTML = `
                <input type="text" class="qa-q-input" placeholder="Q" value="${esc(qa.q)}">
                <input type="text" class="qa-a-input" placeholder="A" value="${esc(qa.a)}">
                <button type="button" class="qa-remove" onclick="this.parentElement.remove()">✕</button>
            `;
            qaList.appendChild(div);
        });
    }

    document.getElementById('noteFormModal').classList.add('open');
}

async function saveNote(e) {
    e.preventDefault();
    const btn = document.getElementById('noteSaveBtn');
    btn.disabled = true; btn.textContent = '保存中...';

    const noteId = document.getElementById('noteId').value;
    const interviewId = document.getElementById('noteInterviewId').value || document.getElementById('noteInterviewSelect').value;

    // 收集Q&A
    const qas = [];
    document.querySelectorAll('#qaList .qa-row').forEach(row => {
        const q = row.querySelector('.qa-q-input').value.trim();
        const a = row.querySelector('.qa-a-input').value.trim();
        if (q || a) qas.push({ q, a });
    });

    const formData = new FormData();
    formData.append('questions_answers', JSON.stringify(qas));
    formData.append('reflection', document.getElementById('noteReflection').value);
    formData.append('tags', document.getElementById('noteTags').value);

    try {
        let r;
        if (noteId) {
            r = await fetch(`/api/notes/${noteId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    questions_answers: JSON.stringify(qas),
                    reflection: document.getElementById('noteReflection').value,
                    tags: document.getElementById('noteTags').value,
                }),
            });
        } else {
            r = await fetch(`/api/interviews/${interviewId}/notes`, {
                method: 'POST', body: formData,
            });
        }
        const data = await r.json();
        if (data.ok) {
            closeNoteForm();
            await loadNotes();
            // 保存成功后显示发布按钮
            const savedId = noteId || (data.data && data.data.id);
            if (savedId) {
                currentNoteId = savedId;
                const pb = document.getElementById('publishBtn');
                if (pb) pb.style.display = 'block';
            }
        }
    } catch (e) {
        console.error('保存面经失败:', e);
    }
    btn.disabled = false; btn.textContent = '保存面经';
}

async function deleteNote(id) {
    if (!confirm('确定删除这条面经吗？')) return;
    await fetch(`/api/notes/${id}`, { method: 'DELETE' });
    await loadNotes();
}

// ============================================================
// 邮件设置
// ============================================================
async function openEmailSettings() {
    document.getElementById('emailModal').classList.add('open');
    // 加载邀请码配置
    try {
        const r = await fetch('/api/invite-config');
        const d = await r.json();
        if (d.ok) {
            document.getElementById('inviteEnabled').checked = d.data.enabled;
            document.getElementById('inviteCodeInput').value = d.data.code !== '***' ? d.data.code : '';
            toggleInviteInput();
        }
    } catch(e) {}
    loadInviteList();
}

function closeEmailSettings() {
    document.getElementById('emailModal').classList.remove('open');
}

// 邀请码设置
function toggleInviteInput() {
    document.getElementById('inviteCodeInput').disabled = !document.getElementById('inviteEnabled').checked;
}

async function saveInviteConfig() {
    const body = {
        enabled: document.getElementById('inviteEnabled').checked,
        code: document.getElementById('inviteCodeInput').value,
    };
    if (body.enabled && !body.code) { alert('请输入邀请码'); return; }
    const r = await fetch('/api/invite-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    const d = await r.json();
    alert(d.msg || '保存成功');
}

// 加载设置时同时加载邀请码配置
const origOpenEmailSettings = openEmailSettings;
openEmailSettings = async function() {
    await origOpenEmailSettings();
    // 同时加载邀请码配置
    try {
        const r = await fetch('/api/invite-config');
        const d = await r.json();
        if (d.ok) {
            document.getElementById('inviteEnabled').checked = d.data.enabled;
            document.getElementById('inviteCodeInput').value = d.data.code !== '***' ? d.data.code : '';
            document.getElementById('inviteCodeInput').disabled = !d.data.enabled;
        }
    } catch(e) {}
    loadInviteList();
};

// 邮箱邀请管理
async function sendInvite() {
    const email = document.getElementById('inviteEmailInput').value.trim();
    if (!email) { alert('请输入邮箱'); return; }
    const r = await fetch('/api/invites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });
    const d = await r.json();
    if (d.ok && d.data && d.data.code) {
        alert(`✅ 邀请码：${d.data.code}\n发到：${d.data.email}\n\n${d.msg}\n（如未收到邮件，直接复制此码发给对方即可）`);
    } else {
        alert(d.msg);
    }
    if (d.ok) {
        document.getElementById('inviteEmailInput').value = '';
        loadInviteList();
    }
}

async function loadInviteList() {
    try {
        const r = await fetch('/api/invites');
        const d = await r.json();
        if (!d.ok) return;
        const container = document.getElementById('inviteList');
        if (d.data.length === 0) {
            container.innerHTML = '<p style="font-size:.78rem;color:var(--text-muted);text-align:center;">暂无邀请记录</p>';
            return;
        }
        container.innerHTML = d.data.map(i => `
            <div style="display:flex;align-items:center;justify-content:space-between;padding:4px 8px;font-size:.78rem;border-bottom:1px solid #F1F5F9;">
                <span>📧 ${esc(i.email)}</span>
                <code style="font-size:.75rem;color:var(--primary);">${esc(i.code)}</code>
                <span style="font-size:.7rem;color:${i.used ? '#EF4444' : '#10B981'};">${i.used ? '已使用' : '未使用'}</span>
                <span style="font-size:.7rem;color:var(--text-muted);">${i.created_at}</span>
                ${!i.used ? `<button class="btn btn-sm" style="font-size:.65rem;padding:1px 6px;color:#EF4444;" onclick="revokeInvite('${esc(i.code)}')">撤销</button>` : ''}
            </div>
        `).reverse().join('');
    } catch(e) {}
}

async function revokeInvite(code) {
    if (!confirm('确定撤销这个邀请码吗？')) return;
    await fetch('/api/invites/' + encodeURIComponent(code), { method: 'DELETE' });
    loadInviteList();
}

// ---- 修改密码 ----
async function changePassword(e) {
    e.preventDefault();
    const oldPw = document.getElementById('oldPassword').value;
    const newPw = document.getElementById('newPassword').value;
    const newPw2 = document.getElementById('newPassword2').value;

    if (!oldPw) { alert('请输入旧密码'); return; }
    if (newPw.length < 6) { alert('新密码至少6位'); return; }
    if (newPw !== newPw2) { alert('两次新密码不一致'); return; }

    const form = new FormData();
    form.append('old_password', oldPw);
    form.append('new_password', newPw);
    form.append('new_password2', newPw2);

    try {
        const r = await fetch('/api/auth/change-password', { method: 'POST', body: form });
        const d = await r.json();
        alert(d.msg);
        if (d.ok) {
            document.getElementById('passwordForm').reset();
        }
    } catch(e) {
        alert('网络错误');
    }
}

// ---- 提醒横幅 ----
function updateReminderBar() {
    const now = new Date();
    const upcoming = allInterviews.filter(iv => {
        if (iv.interview_status !== 'scheduled' || !iv.scheduled_time) return false;
        const t = new Date(iv.scheduled_time);
        const diff = (t - now) / (1000 * 60 * 60);
        return diff >= 0 && diff <= 24;
    });

    const bar = document.getElementById('reminderBar');
    const text = document.getElementById('reminderText');
    if (!bar || !text) return;

    if (upcoming.length === 0) {
        bar.style.display = 'none';
        return;
    }

    bar.style.display = 'flex';
    const next = upcoming[0];
    const t = new Date(next.scheduled_time);
    const diffH = Math.floor((t - now) / (1000 * 60 * 60));
    const diffM = Math.floor((t - now) / (1000 * 60)) % 60;
    const urgency = diffH < 1 ? '⚠️' : '🔔';

    if (upcoming.length === 1) {
        text.innerHTML = `${urgency} <strong>${esc(next.company)} ${esc(next.position)}</strong> — ${next.round} ${next.interview_type} @ ${t.toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'})} (${diffH > 0 ? diffH + '小时' + diffM + '分钟后' : diffM + '分钟后'})`;
    } else {
        text.innerHTML = `${urgency} 未来24小时有 <strong>${upcoming.length}场</strong> 面试，最近：<strong>${esc(next.company)}</strong> ${diffH > 0 ? diffH + '小时' + diffM + '分钟后' : diffM + '分钟后'}`;
    }
}

// 每2分钟更新提醒 + 加载时更新
setInterval(() => { if (allInterviews.length > 0) updateReminderBar(); }, 2 * 60 * 1000);
// 在加载面试后更新
const origLoadInterviews = loadInterviews;
loadInterviews = async function() {
    await origLoadInterviews();
    updateReminderBar();
};

// 响应式调整 echarts
window.addEventListener('resize', () => {
    ['chartStatus', 'chartSource', 'chartFunnel', 'chartChannel', 'chartTimeline'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const instance = echarts.getInstanceByDom(el);
            if (instance) instance.resize();
        }
    });
});

// ============================================================
// 求职洞察 — 数据分析面板
// ============================================================
async function openAnalytics() {
    document.getElementById('analyticsModal').classList.add('open');
    try {
        const [summaryR, funnelR, channelsR, timelineR, companiesR, catsR, rejectR, salaryR] = await Promise.all([
            fetch('/api/analytics/summary').then(r => r.json()),
            fetch('/api/analytics/funnel').then(r => r.json()),
            fetch('/api/analytics/channels').then(r => r.json()),
            fetch('/api/analytics/timeline').then(r => r.json()),
            fetch('/api/analytics/companies').then(r => r.json()),
            fetch('/api/analytics/categories').then(r => r.json()),
            fetch('/api/analytics/rejection-reasons').then(r => r.json()),
            fetch('/api/analytics/salary-comparison').then(r => r.json()),
        ]);

        if (summaryR.ok) renderSummary(summaryR.data);
        if (funnelR.ok) renderFunnelChart(funnelR.data);
        if (channelsR.ok) renderChannelChart(channelsR.data);
        if (timelineR.ok) renderTimelineChart(timelineR.data);
        if (companiesR.ok) renderCompaniesTable(companiesR.data);
        if (catsR.ok) renderCategoriesChart(catsR.data);
        if (rejectR.ok) renderRejectionChart(rejectR.data);
        if (salaryR.ok) renderSalaryComparison(salaryR.data);

        // AI 洞察和预测（异步加载，显示进度）
        const insightsDiv = document.getElementById('analyticsInsights');
        insightsDiv.innerHTML += '<br><span id="aiLoading" style="color:var(--text-muted);">🤖 AI 分析中...</span>';

        fetch('/api/analytics/ai-insights').then(r => r.json()).then(d => {
            if (d.ai_enabled && d.data.length) renderAIInsights(d.data);
            else document.getElementById('aiLoading')?.remove();
        }).catch(() => document.getElementById('aiLoading')?.remove());

        fetch('/api/analytics/ai-prediction').then(r => r.json()).then(d => {
            if (d.ai_enabled && d.data) renderAIPrediction(d.data);
        });
    } catch (e) {
        console.error('加载数据分析失败:', e);
    }
}

function closeAnalytics() {
    document.getElementById('analyticsModal').classList.remove('open');
}

function renderSummary(data) {
    const container = document.getElementById('analyticsSummary');
    container.innerHTML = `
        <div class="stat-card"><div class="stat-num">${data.total}</div><div class="stat-label">总投递</div></div>
        <div class="stat-card"><div class="stat-num">${data.total_interviews}</div><div class="stat-label">总面试</div></div>
        <div class="stat-card stat-rate"><div class="stat-num">${data.interview_rate}%</div><div class="stat-label">面试转化率</div></div>
        <div class="stat-card stat-rate"><div class="stat-num">${data.offer_rate}%</div><div class="stat-label">Offer率</div></div>
    `;

    const insightsDiv = document.getElementById('analyticsInsights');
    if (data.insights && data.insights.length > 0) {
        insightsDiv.innerHTML = '<strong>💡 AI 洞察</strong><br>' +
            data.insights.map((t, i) => `<span style="color:#92400E;">${i+1}. ${t}</span>`).join('<br>');
    }
}

function renderFunnelChart(data) {
    const chart = echarts.init(document.getElementById('chartFunnel'));
    chart.setOption({
        title: { text: '转化漏斗', left: 'center', textStyle: { fontSize: 14 } },
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        series: [{
            type: 'funnel',
            left: '10%', right: '10%', top: 40, bottom: 20,
            minSize: '20%',
            sort: 'none',
            gap: 2,
            label: { show: true, position: 'inside', formatter: '{b}\n{c}份' },
            data: data.map(d => ({ name: d.label, value: d.count })),
            itemStyle: { borderColor: '#fff', borderWidth: 1 },
            color: ['#4F46E5', '#7C3AED', '#8B5CF6', '#A78BFA', '#10B981'],
        }],
    });
}

function renderChannelChart(data) {
    const chart = echarts.init(document.getElementById('chartChannel'));
    chart.setOption({
        title: { text: '渠道效率对比', left: 'center', textStyle: { fontSize: 14 } },
        tooltip: { trigger: 'axis' },
        legend: { data: ['面试率', 'Offer率'], bottom: 0, textStyle: { fontSize: 11 } },
        xAxis: { type: 'category', data: data.map(d => d.channel), axisLabel: { fontSize: 11 } },
        yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
        series: [
            { name: '面试率', type: 'bar', data: data.map(d => d.interview_rate), itemStyle: { color: '#4F46E5', borderRadius: [4,4,0,0] } },
            { name: 'Offer率', type: 'bar', data: data.map(d => d.offer_rate), itemStyle: { color: '#10B981', borderRadius: [4,4,0,0] } },
        ],
        grid: { bottom: 40 },
    });
}

function renderTimelineChart(data) {
    const chart = echarts.init(document.getElementById('chartTimeline'));
    chart.setOption({
        title: { text: '投递 & 面试趋势', left: 'center', textStyle: { fontSize: 14 } },
        tooltip: { trigger: 'axis' },
        legend: { data: ['投递', '面试'], bottom: 0 },
        xAxis: { type: 'category', data: data.map(d => d.period), axisLabel: { rotate: 30, fontSize: 10 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
            { name: '投递', type: 'line', data: data.map(d => d.applications), smooth: true, itemStyle: { color: '#4F46E5' } },
            { name: '面试', type: 'line', data: data.map(d => d.interviews), smooth: true, itemStyle: { color: '#F59E0B' } },
        ],
        grid: { bottom: 40 },
    });
}

function renderCompaniesTable(data) {
    const container = document.getElementById('analyticsCompanies');
    if (data.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:40px;">暂无数据</p>';
        return;
    }
    let html = '<h4 style="text-align:center;margin-bottom:8px;font-size:.9rem;">公司投递分析</h4>';
    html += '<table style="width:100%;font-size:.78rem;border-collapse:collapse;">';
    html += '<thead><tr style="background:#F1F5F9;"><th style="padding:6px 8px;text-align:left;">公司</th><th>投递</th><th>面试轮次</th><th>最新状态</th><th>岗位</th></tr></thead><tbody>';
    data.forEach(d => {
        html += `<tr style="border-bottom:1px solid #E2E8F0;">
            <td style="padding:6px 8px;font-weight:600;">${esc(d.company)}</td>
            <td style="text-align:center;">${d.total_applications}</td>
            <td style="text-align:center;">${d.interview_rounds}</td>
            <td style="text-align:center;">${d.status_label}</td>
            <td style="font-size:.7rem;color:var(--text-muted);">${d.positions.join(', ')}</td>
        </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
    container.style.padding = '12px';
    container.style.background = '#F8FAFC';
    container.style.borderRadius = 'var(--radius)';
}

function renderAIInsights(insights) {
    const container = document.getElementById('analyticsInsights');
    container.innerHTML = '<strong>🤖 AI 深度洞察</strong><br>' +
        insights.map((t, i) => `<span style="color:#312E81;">💡 ${t}</span>`).join('<br>');
}

function renderAIPrediction(prediction) {
    const container = document.getElementById('analyticsContent');
    const html = `
        <div style="margin-bottom:24px;padding:16px;background:linear-gradient(135deg,#EEF2FF,#E0E7FF);border-radius:12px;border:1px solid #C7D2FE;">
            <h4 style="margin:0 0 8px;color:#4338CA;">🔮 AI 预测</h4>
            <p style="margin:0;color:#312E81;line-height:1.7;white-space:pre-wrap;">${prediction}</p>
        </div>`;
    container.insertAdjacentHTML('afterbegin', html);
}

function exportData() {
    window.open('/api/analytics/export', '_blank');
}

function renderCategoriesChart(data) {
    if (!data || !data.length) return;
    const container = document.getElementById('analyticsContent');
    const labels = data.map(d => d.category);
    const values = data.map(d => d.total);
    const colors = ['#4F46E5','#7C3AED','#EC4899','#F59E0B','#10B981','#3B82F6',
                    '#EF4444','#6366F1','#8B5CF6','#14B8A6','#F97316','#06B6D4'];
    const html = `
        <div style="margin-bottom:24px;">
            <h4 style="margin-bottom:12px;">📂 岗位类别分布</h4>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                ${data.map((d, i) => `
                    <div style="flex:1;min-width:120px;padding:12px;background:#F8FAFC;border-radius:8px;text-align:center;
                        border-left:4px solid ${colors[i % colors.length]};">
                        <div style="font-weight:600;">${d.category}</div>
                        <div style="font-size:1.3rem;font-weight:700;color:${colors[i % colors.length]};">${d.total}</div>
                        <div style="font-size:.75rem;color:var(--text-muted);">面试率 ${d.interview_rate}%</div>
                    </div>
                `).join('')}
            </div>
        </div>`;
    container.insertAdjacentHTML('beforeend', html);
}

function renderRejectionChart(data) {
    if (!data || !data.length) return;
    const container = document.getElementById('analyticsContent');
    const maxCount = Math.max(...data.map(d => d.count));
    const html = `
        <div style="margin-bottom:24px;">
            <h4 style="margin-bottom:12px;">❌ 挂因分析</h4>
            <div style="display:flex;flex-direction:column;gap:8px;">
                ${data.map(d => `
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="width:80px;font-size:.85rem;text-align:right;">${d.reason}</span>
                        <div style="flex:1;height:22px;background:#FEE2E2;border-radius:4px;overflow:hidden;">
                            <div style="height:100%;width:${(d.count / maxCount * 100).toFixed(0)}%;background:#EF4444;border-radius:4px;"></div>
                        </div>
                        <span style="font-weight:600;width:30px;">${d.count}</span>
                    </div>
                `).join('')}
            </div>
        </div>`;
    container.insertAdjacentHTML('beforeend', html);
}

function renderSalaryComparison(data) {
    if (!data || !data.offer_salaries || !data.offer_salaries.length) return;
    const container = document.getElementById('analyticsContent');
    const html = `
        <div style="margin-bottom:24px;">
            <h4 style="margin-bottom:12px;">💰 Offer 薪资</h4>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                ${data.offer_salaries.map(s => `
                    <span style="padding:6px 14px;background:#D1FAE5;color:#065F46;border-radius:20px;font-weight:600;font-size:.9rem;">${s}</span>
                `).join('')}
            </div>
            ${data.expected_salaries && data.expected_salaries.length ? `
                <p style="font-size:.78rem;color:var(--text-muted);margin-top:8px;">期望薪资参考：${data.expected_salaries.slice(0,5).join('、')}</p>
            ` : ''}
        </div>`;
    container.insertAdjacentHTML('beforeend', html);
}

// ---- 面经发布到论坛 ----
let currentNoteId = null;

async function promptPublish() {
    if (!currentNoteId) return;
    const isAnon = confirm('匿名发布？\n确定=匿名，取消=实名');
    const r = await fetch(`/api/notes/${currentNoteId}/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_anonymous: isAnon ? 1 : 0 }),
    });
    const d = await r.json();
    if (d.ok) {
        alert('已发布到论坛！');
        document.getElementById('publishBtn').style.display = 'none';
    } else {
        alert(d.detail || '发布失败');
    }
}
