# AI Readers - 多Agent文章辩论评审系统

**版本**: v4.9  
**日期**: 2026-04-25  
**作者**: AI FundExpert

---

## 1. 核心流程

```
用户上传文章 → 系统保存文件 → 返回项目信息 → 开始辩论任务 → 查看结果
```

---

## 2. 已完成功能

### 2.1 文件上传

| 格式 | 说明 |
|------|------|
| TXT | 纯文本，直接读取 |
| MD | Markdown，直接读取 |
| PDF | 二进制文件，保存到磁盘，后端提取文本 |
| DOC/DOCX | 二进制文件，保存到磁盘，后端提取文本 |

### 2.2 辩论角色

**批评者（5个）**
- 结构批评者 - 从结构框架角度分析
- 语言批评者 - 从遣词造句角度分析
- 逻辑批评者 - 从逻辑论证角度分析
- 创意批评者 - 从立意风格角度分析
- 技术批评者 - 从技术细节角度分析

**辩护者（4个）**
- 平衡辩护者 - 理性分析，寻求共识
- 共情辩护者 - 理解作者意图
- 内容辩护者 - 从内容事实角度辩护
- 表达辩护者 - 从表达方式角度辩护

### 2.3 项目管理
- 创建项目（文本/文件）
- 查看项目列表
- 查看项目详情
- 删除项目
- 重新辩论
- **修改辩论设置**（轮次、批评者、辩护者）
- **辩论进度显示**（自动轮询状态）

### 2.4 报告导出
- PDF 导出
- HTML 导出

---

## 3. 数据存储

### 3.1 项目目录结构

```
history/
└── {project_id}/
    ├── metadata.json      # 项目元信息（标题、配置、时间）
    ├── original.pdf      # 原始文件（如果上传的是文件）
    ├── article.txt        # 提取的文本内容
    ├── debate_history.json # 辩论过程历史
    └── debate_result.json  # 辩论结果
```

### 3.2 metadata.json 结构

```json
{
  "id": "debate_20260425_xxxxxx",
  "title": "文章标题",
  "original_filename": "原文.pdf",
  "content_type": "application/pdf",
  "file_size": 47153155,
  "created_at": "2026-04-25T10:00:00",
  "status": "completed",
  "config": {
    "rounds": 3,
    "critics": ["结构批评者", "语言批评者", "逻辑批评者"],
    "defenders": ["平衡辩护者", "共情辩护者", "内容辩护者"]
  }
}
```

### 3.3 状态流转

```
pending → processing → completed
           ↓
         failed
```

| 状态 | 说明 |
|------|------|
| `pending` | 已创建，等待开始辩论 |
| `processing` | 辩论进行中（前端自动轮询） |
| `completed` | 辩论完成，报告已生成 |
| `failed` | 失败 |

---

## 4. API 设计

### 4.1 项目管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/projects` | 获取所有项目 |
| GET | `/api/projects/{id}` | 获取项目详情 |
| POST | `/api/projects` | 创建项目（文件上传） |
| POST | `/api/projects/json` | 创建项目（JSON文本） |
| PATCH | `/api/projects/{id}` | 更新项目配置 |
| DELETE | `/api/projects/{id}` | 删除项目 |
| POST | `/api/projects/{id}/debate` | 开始辩论 |

### 4.2 辩论配置

```json
{
  "title": "项目标题",
  "article": "文章内容（纯文本）",
  "config": {
    "rounds": 3,
    "critics": ["结构批评者", "语言批评者"],
    "defenders": ["平衡辩护者", "共情辩护者"]
  }
}
```

### 4.3 更新配置请求

```json
PATCH /api/projects/{id}
{
  "config": {
    "rounds": 5,
    "critics": ["结构批评者", "语言批评者", "逻辑批评者"],
    "defenders": ["平衡辩护者", "共情辩护者"]
  }
}
```

---

## 5. 前端页面

### 5.1 页面结构

| 路径 | 说明 |
|------|------|
| `/` (项目列表) | 显示所有项目，状态徽章 |
| `/projects/:id` | 项目详情，辩论内容，报告 |

### 5.2 项目列表页

- 统计卡片：总数/进行中/已完成
- 项目卡片：标题、时间、状态、评分
- 上传按钮 → 弹窗

### 5.3 上传弹窗

- 两种输入方式切换：文件上传 / 粘贴文本
- 文件上传：拖拽区域 + 点击选择
- 粘贴文本：文本框
- 辩论配置：轮次、批评者、辩护者（复选框）
- 提交后立即关闭，返回列表

### 5.4 项目详情页

- **项目信息（置顶）**：状态、轮次、批评者、辩护者、创建时间
- **设置按钮**：修改辩论配置
- 文章原文（可展开/折叠）
- **辩论进度动画**：processing 时显示旋转动画和进度条
- 辩论流程（按轮次展示）
- 评分雷达图
- 报告内容
- 导出按钮（PDF/HTML）
- 删除/重新辩论按钮

---

## 6. 技术方案

### 6.1 后端 (Python FastAPI)

```
backend/
├── main.py              # FastAPI 应用
├── pdf_generator.py     # PDF 报告生成器（reportlab）
├── LXGWWenKai-Regular.ttf # 中文字体
├── Dockerfile           # Docker 镜像构建
└── requirements.txt     # 依赖
```

**依赖**
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- pydantic==2.5.3
- python-multipart==0.0.6
- python-docx==1.1.0
- PyPDF2==3.0.1
- slowapi==0.1.9
- reportlab==4.0.9  # PDF 生成（中文字体支持）

### 6.2 文件处理

| 类型 | 处理方式 |
|------|----------|
| TXT/MD | 直接读取内容 |
| PDF | 用 PyPDF2 提取文本 |
| DOCX | 用 python-docx 提取文本 |

### 6.3 PDF 报告生成

| 组件 | 说明 |
|------|------|
| 字体 | LXGW WenKai（霞鹜文楷）18MB 中文字体 |
| 库 | reportlab（支持复杂 TTF 字体） |
| 挂载 | docker-compose.yml 将字体挂载到容器 `/app/LXGWWenKai-Regular.ttf` |
| 解析 | `parse_markdown_to_paragraphs()` 将 Markdown 转为 ReportLab Flowable |
| 格式 | 支持标题(H1-H4)、段落、表格、列表、引用、代码块 |

**PDF 生成流程**
1. 读取 `debate_full.md` Markdown 文件
2. 清理特殊字符（移除 CJK Radicals 兼容区字符）
3. 解析为段落类型列表
4. 使用 `clean_article_content()` 清理文章内容区域
5. 生成带样式的 PDF 文档

### 6.4 Docker 部署

```yaml
services:
  backend:
    build: ./backend
    volumes:
      - ./history:/app/history
      - ./scripts:/app/scripts
      - ./frontend/dist:/app/dist:ro
      - ./backend/LXGWWenKai-Regular.ttf:/app/LXGWWenKai-Regular.ttf:ro
    environment:
      - ALLOWED_ORIGINS=http://localhost:8086,http://10.147.18.38:8086
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "8086:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    restart: unless-stopped
```

### 6.5 前端 (React + TypeScript)

```
frontend/
├── src/
│   ├── pages/
│   │   ├── ProjectsPage.tsx      # 项目列表页
│   │   └── ProjectDetailPage.tsx # 项目详情页
│   ├── components/
│   │   ├── debate/
│   │   │   ├── DebateView.tsx   # 辩论视图
│   │   │   └── ReportSection.tsx # 报告区域
│   │   └── layout/
│   │       └── AppLayout.tsx     # 布局组件
│   ├── services/
│   │   └── api.ts               # API 调用
│   └── store/
│       └── projectStore.ts      # Zustand 状态
└── dist/                        # 构建产物
```

**技术栈**
- React 18 + TypeScript
- Vite 构建工具
- TailwindCSS + shadcn/ui 风格
- Recharts（雷达图）
- Zustand（状态管理）
- jsPDF + html2canvas（PDF导出）

### 6.6 安全特性

| 特性 | 说明 |
|------|------|
| CORS 限制 | 可配置允许的源 |
| 项目 ID 验证 | 正则 `^[\w-]+$` 防止路径遍历 |
| 请求限流 | 辩论端点 5次/分钟 |
| 日志系统 | 使用 logging 模块 |
| Dockerfile | 非 root 用户运行 |
| 异步任务超时 | 10分钟超时保护 |

### 6.7 辩论脚本 (Python)

```
scripts/
├── debate.py              # 主辩论脚本
├── debate_api.py         # API 接口封装
└── __init__.py
```

**提示词优化**
- 多阶段分析框架（整体→局部→建议）
- 批评者：结构/语言/逻辑/技术/创意 5维度
- 辩护者：平衡/共情 2类型
- 内容详实，包含表格化分析

### 6.8 报告结构（总结优先）

PDF/HTML 报告采用**总结优先**的结构，确保用户第一时间获取核心信息：

| 顺序 | 部分 | 内容说明 |
|------|------|----------|
| 1 | 📊 文章评审总结报告 | AI 根据辩论内容生成的面向作者的总结 |
| 2 | 📄 文章原文 | 原始文章内容（前500字符截断） |
| 3 | 🔄 详细辩论过程 | 按轮次展示批评者和辩护者观点 |
| 4 | 📊 评分详情 | 各维度评分和雷达图数据 |
| 5 | 📝 编辑裁决 | 资深编辑的最终判断 |

**总结报告包含**：
- 总体评价（2-3句话概括文章质量）
- 需要关注的问题（按重要性排序）
- 优点总结
- 优化优先级（高/中/低）
- 行动建议（具体修改步骤）

---

## 7. 已完成功能清单

| 功能 | 状态 | 说明 |
|------|------|------|
| 文件上传（multipart） | ✅ | 支持 PDF/DOCX/TXT/MD |
| 文本提取 | ✅ | PyPDF2 + python-docx |
| 异步辩论任务 | ✅ | asyncio 后台运行 |
| 状态轮询 | ✅ | 前端 3 秒轮询 |
| 项目列表页 | ✅ | 统计卡片 + 项目卡片 |
| 上传弹窗 | ✅ | 文件/文本切换 |
| 项目详情页 | ✅ | 辩论视图 + 报告 |
| 修改辩论设置 | ✅ | PATCH API + 弹窗 |
| 辩论进度显示 | ✅ | processing 动画 |
| PDF 导出 | ✅ | 后端 API + reportlab + LXGW WenKai 中文字体 |
| HTML 导出 | ✅ | 完整 HTML 文件（完美中文支持） |
| 项目删除 | ✅ | 确认弹窗 |
| 重新辩论 | ✅ | 使用当前配置 |
| Docker 部署 | ✅ | docker-compose |
| 安全审计 | ✅ | CORS/限流/验证 |

---

## 8. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-04-25 | 初始版本，基础辩论功能 |
| v2.0 | 2026-04-25 | 添加前端页面、PDF导出 |
| v2.1-2.2 | 2026-04-25 | 辩论配置、项目删除 |
| v3.0 | 2026-04-25 | 大文件支持、完整需求文档 |
| v4.0 | 2026-04-25 | 修改设置、进度显示、提示词优化、安全审计 |
| v4.1 | 2026-04-25 | PDF 导出改用后端 API，降级为 HTML 下载 |
| v4.2 | 2026-04-25 | 辩论内容 Markdown 渲染修复 |
| v4.3 | 2026-04-25 | PDF 报告结构重构：总结优先 |
| v4.4 | 2026-04-25 | AI 生成面向作者的总结报告（总体评价/问题/建议） |
| v4.5 | 2026-04-25 | 网页端评分优先展示（评分概览在总结之前） |
| v4.6 | 2026-04-25 | PDF 报告服务器端生成（中文字体 LXGW WenKai） |
| v4.7 | 2026-04-25 | PDF 结构优化：清晰的分节标题和分隔线 |
| v4.8 | 2026-04-25 | 修复报告格式：提取真实原文引用，而非表格内容 |
| v4.9 | 2026-04-25 | 总结报告详细化：逐条引用原文、详细修改建议、纠错清单 |
