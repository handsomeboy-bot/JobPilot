# JobPilot 求职论坛 — 设计文档

日期：2026-06-08 | 版本：v1.0

## 一、概述

在现有私有"面经库"基础上新增公共论坛模块。用户写完私有面经后可选择公开发布到论坛，其他用户可浏览、盖楼评论交流。

## 二、数据模型

### ForumPost（论坛帖子）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| author_id | Integer FK→users.id | 作者 |
| title | String(200) | 帖子标题 |
| content | Text | 正文（从面经 Q&A + reflection 拼接） |
| tags | String(200) | 标签 |
| is_anonymous | Integer | 0=实名, 1=匿名 |
| comment_count | Integer | 评论数缓存（防 N+1） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### ForumComment（评论）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| post_id | Integer FK→forum_posts.id | 所属帖子 |
| author_id | Integer FK→users.id | 评论者 |
| parent_id | Integer FK→forum_comments.id, nullable | 回复哪条评论，NULL=一级评论 |
| content | Text | 评论内容 |
| is_anonymous | Integer | 0=实名, 1=匿名 |
| created_at | DateTime | 创建时间 |

### ForumNotification（通知）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| user_id | Integer FK→users.id | 通知给谁 |
| post_id | Integer FK→forum_posts.id | 关联帖子 |
| type | String(20) | 'post_reply' 或 'comment_reply' |
| from_user_id | Integer FK→users.id | 谁触发的 |
| content_preview | String(50) | 回复内容预览 |
| is_read | Integer | 0=未读, 1=已读 |
| created_at | DateTime | 创建时间 |

## 三、API 设计

### 帖子

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /api/forum/posts | 帖子列表（分页：?page=1，筛选：?tag=xxx，搜索：?search=xxx） | 登录 |
| GET | /api/forum/posts/{id} | 帖子详情 + 评论树 | 登录 |
| POST | /api/forum/posts | 发帖 {title, content, tags, is_anonymous} | 登录 |
| DELETE | /api/forum/posts/{id} | 删帖 | 作者/管理员 |

### 评论

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /api/forum/posts/{id}/comments | 发评论 {content, parent_id?, is_anonymous} → 自动触发通知 | 登录 |
| DELETE | /api/forum/comments/{id} | 删评论 | 作者/管理员 |

### 通知

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /api/forum/notifications | 获取未读通知列表 | 登录 |
| GET | /api/forum/notifications/unread-count | 未读数量 | 登录 |
| POST | /api/forum/notifications/{id}/read | 标记已读 | 本人 |
| POST | /api/forum/notifications/read-all | 全部已读 | 本人 |

### 现有面经接口改动

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/notes/{note_id}/publish | 将私有面经发布到论坛 {is_anonymous} |

## 四、前端

### 页面

1. **论坛列表页**（新 Tab）：帖子卡片列表，标签筛选，关键词搜索
2. **帖子详情页**：正文 + 评论区（盖楼树形展示）+ 发表评论表单
3. **面经发布弹窗**：从面经编辑页点"发布到论坛"，选匿名/实名
4. **通知铃铛**：导航栏 🔔 图标 + 未读数量角标 + 下拉列表，点击通知跳转到帖子详情

### 显示规则

- 匿名帖子/评论：显示"匿名用户"，不显示作者昵称
- 评论树：一级评论按时间倒序，子回复缩进显示
- 通知列表：按时间倒序，未读项高亮，点击标记已读并跳转

## 五、权限规则

| 操作 | 权限 |
|------|------|
| 浏览论坛 | 所有登录用户 |
| 发帖 | 登录用户 |
| 发表评论 | 登录用户 |
| 删帖 | 作者本人 或 管理员 |
| 删评论 | 评论作者 或 管理员 |

## 六、实现范围

### 本次做
- ForumPost + ForumComment + ForumNotification 模型
- 论坛 CRUD API + 通知 API
- 面经发布到论坛
- 评论时自动触发通知（回复帖子→通知楼主，回复评论→通知被回复者）
- 论坛列表页 + 帖子详情页 + 评论组件
- 导航栏通知铃铛（未读角标 + 下拉列表）
- 帖子/评论删除

### 本次不做
- 点赞/收藏
- 编辑帖子/评论
- 富文本编辑器（纯文本即可）
- 举报/审核

## 七、技术约束

- 纯 SQLAlchemy 查询，不引入 ORM 外的额外依赖
- 保持 Jinja2 模板渲染，不开前后端分离
- 增删改遵循 RESTful 风格
- 保持现有代码风格和目录结构
