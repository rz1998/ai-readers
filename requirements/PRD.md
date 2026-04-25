# AI Readers - 多Agent文章辩论评审系统

**版本**: v3.0  
**日期**: 2026-04-25  
**作者**: AI FundExpert

---

## 1. 核心流程

```
用户上传文章 → 系统保存文件 → 返回项目信息 → 开始辩论任务 → 查看结果
```

---

## 2. 文件上传

### 2.1 支持格式

| 格式 | 说明 |
|------|------|
| TXT | 纯文本，直接读取 |
| MD | Markdown，直接读取 |
| PDF | 二进制文件，保存到磁盘，后端提取文本 |
| DOC/DOCX | 二进制文件，保存到磁盘，后端提取文本 |

### 2.2 文件大小

- **无硬性限制** - Nginx 已配置最大 100MB
- 建议纯文本 ≤ 10MB
- PDF 等二进制文件按实际大小上传

### 2.3 上传方式

| 方式 | 说明 |
|------|------|
| 文件上传 | 支持拖拽或选择文件 |
| 粘贴文本 | 文本框直接输入，无大小限制 |

---

## 3. 数据存储

### 3.1 项目目录结构

```
history/
└── {project_id}/
    ├── metadata.json      # 项目元信息（标题、配置、时间）
    ├── article.pdf        # 原始文件（如果上传的是文件）
    ├── article.txt        # 提取的文本内容
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
  "status": "pending",
  "config": {
    "rounds": 3,
    "critics": ["结构批评者", "语言批评者"],
    "defenders": ["平衡辩护者", "共情辩护者"]
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
| `processing` | 辩论进行中 |
| `completed` | 辩论完成，报告已生成 |
| `failed` | 失败（可选） |

---

## 4. API 设计

### 4.1 创建项目（上传文件）

```
POST /api/projects
Content-Type: multipart/form-data

file: (binary)
title: "文章标题"
config: {"rounds": 3, "critics": [...], "defenders": [...]}

Response 200:
{
  "id": "debate_20260425_xxxxxx",
  "title": "文章标题",
  "status": "pending",
  "created_at": "...",
  "config": {...}
}
```

### 4.2 创建项目（粘贴文本）

```
POST /api/projects
Content-Type: application/json

{
  "title": "文章标题",
  "article": "文章内容...",
  "config": {...}
}

Response 200:
{
  "id": "debate_20260425_xxxxxx",
  "title": "文章标题",
  "status": "pending",
  ...
}
```

### 4.3 其他 API

```
GET  /api/projects              # 列表
GET  /api/projects/:id        # 详情
DELETE /api/projects/:id       # 删除
POST /api/projects/:id/debate  # 开始辩论（异步）
```

---

## 5. 前端交互

### 5.1 页面结构

| 页面 | 功能 |
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
- 辩论配置：轮次、批评者、辩护者
- 提交后立即关闭，返回列表

### 5.4 项目详情页

- 文章原文（可展开/折叠）
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
├── requirements.txt     # 依赖
└── services/
    ├── file_handler.py  # 文件处理（PDF提取等）
    └── debate_runner.py  # 辩论任务运行器
```

### 6.2 文件处理

| 类型 | 处理方式 |
|------|----------|
| TXT/MD | 直接读取内容 |
| PDF | 用 PyPDF2 或 pdfminer 提取文本 |
| DOCX | 用 python-docx 提取文本 |

### 6.3 Docker 部署

```yaml
services:
  backend:
    build: .
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - ./history:/app/history
    environment:
      - PYTHONUNBUFFERED=1

  nginx:
    image: nginx:alpine
    ports:
      - "8086:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
```

### 6.4 前端 (React + TypeScript)

- 组件化开发
- Zustand 状态管理
- Axios 请求库
- PDF 导出（jsPDF + html2canvas）

---

## 7. 待开发功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 文件上传（multipart） | P0 | 支持大文件 PDF/DOCX |
| 文本提取 | P1 | PDF/DOCX 转文本 |
| 异步辩论任务 | P2 | 后台运行辩论脚本 |
| 状态轮询 | P2 | 前端定期检查状态 |

---

## 8. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-04-25 | 初始版本，基础辩论功能 |
| v2.0 | 2026-04-25 | 添加前端页面、PDF导出 |
| v2.1-2.2 | 2026-04-25 | 辩论配置、项目删除 |
| v3.0 | 2026-04-25 | 大文件支持、完整需求文档 |
