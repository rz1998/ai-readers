# AI Readers - 多Agent文章辩论评审系统

通过多个专业角色的多轮辩论，对文章进行全方位深度评审。

## 功能特性

- 📝 **文章上传** - 支持文本粘贴和文件上传（PDF/DOC/TXT/MD）
- 👥 **多角色辩论** - 可配置批评者/辩护者角色
- 🔄 **多轮辩论** - 支持1-5轮辩论流程
- 📊 **7维度评分** - 结构/遣词/立意/文笔/风格/内容/技术
- 📄 **报告导出** - PDF/HTML格式下载
- 🎨 **现代化前端** - React + TypeScript + TailwindCSS

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:8092

### 辩论脚本

```bash
cd scripts
python3 debate.py "文章内容" --rounds 3
```

## 项目结构

```
ai-readers/
├── critics/           # 批评者角色定义
├── defenders/         # 辩护者角色定义
├── editors/          # 编辑角色定义
├── scripts/          # 辩论脚本
├── frontend/          # React前端
├── requirements/      # 需求文档
└── history/          # 辩论历史
```

## 辩论流程

```
Round 1: 批评者初审 → 辩护者回应
Round 2: 批评者复审 → 辩护者再回应
Round 3: 批评者终审 → 辩护者总结
Final:   编辑综合 → 最终报告
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | React 18, TypeScript, TailwindCSS |
| 图表 | Recharts |
| 状态 | Zustand |
| 路由 | React Router v6 |
| 导出 | jsPDF, html2canvas |
| Agent | OpenClaw sessions_spawn |

## 部署信息

| 服务 | 端口 | 状态 |
|------|------|------|
| nginx (前端) | 8091 | ✅ 运行中 |
| backend (Python) | 容器内 | ✅ 运行中 |

### 端口历史
- 8086 → 与 ai-fund-market-data-service 冲突
- 8087 → 与 ai-fund-strategy-service 冲突
- 8089 → 端口占用
- 8091
- 8092 → 当前端口 (2026-04-29)

## License

MIT
