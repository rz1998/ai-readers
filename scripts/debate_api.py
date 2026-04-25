#!/usr/bin/env python3
"""
AI Readers - 多Agent多轮辩论系统
真实Agent调用版本

架构：
1. Python脚本负责：参数解析、prompt构建、数据存储
2. 真实的Agent调用：通过 OpenClaw sessions_spawn 工具实现

使用方式（通过OpenClaw agent调用）：
    spawn_debate(article, config) -> 启动多Agent辩论
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

# 路径配置
SKILL_DIR = Path(__file__).parent.parent
HISTORY_DIR = SKILL_DIR / "history"


@dataclass
class DebateConfig:
    """辩论配置"""
    rounds: int = 3
    critics: List[str] = field(default_factory=lambda: ["结构批评者", "语言批评者"])
    defenders: List[str] = field(default_factory=lambda: ["平衡辩护者", "共情辩护者"])


@dataclass
class RoundResult:
    """单轮辩论结果"""
    round_num: int
    critics: Dict[str, str] = field(default_factory=dict)
    defenders: Dict[str, str] = field(default_factory=dict)


@dataclass
class DebateResult:
    """完整辩论结果"""
    debate_id: str
    timestamp: str
    article_length: int
    config: DebateConfig
    rounds: List[RoundResult]
    final_report: str = ""


def build_critic_prompt(article: str, critic_name: str, round_num: int, 
                        context: Optional[str] = None) -> str:
    """构建批评者prompt"""
    
    base_prompt = f"""你是一位严格的文章批评者，你的名字是：{critic_name}

## 你的评审维度
1. 结构 (Organization)
2. 遣词造句 (Word Choice)
3. 立意 (Theme & Message)
4. 文笔 (Writing Quality)
5. 风格 (Style)
6. 内容 (Content)
7. 技术 (Technical)

## 待评审文章
---
{article[:8000]}...
---

[文章内容过长，已截断]
"""

    if round_num == 1:
        return f"""# Round 1: 批评者 [{critic_name}] 初审

{base_prompt}

## 任务
请从7个维度严格评审这篇文章，指出具体问题，引用原文说明。

## 输出格式
### 各维度问题（引用原文）
### 问题汇总（按严重程度）
### 核心批评观点（3句话）
"""
    else:
        return f"""# Round {round_num}: 批评者 [{critic_name}] 复审

{base_prompt}

## 前轮辩护者观点
---
{context or '无'}
---

## 任务
针对辩护者观点，重新审视你的批评：
1. 哪些批评被有效反驳，需要调整？
2. 哪些批评依然成立，坚持立场？
3. 最终问题清单是什么？

## 输出格式
### 坚持的问题
### 调整的问题
### 最终问题清单
"""


def build_defender_prompt(article: str, defender_name: str, round_num: int,
                          critics_views: Dict[str, str]) -> str:
    """构建辩护者prompt"""
    
    critics_summary = "\n\n".join([
        f"=== {name} 的批评 ===\n{view}"
        for name, view in critics_views.items()
    ])
    
    return f"""# Round {round_num}: 辩护者 [{defender_name}] 发言

你是一位理性的文章辩护者，你的名字是：{defender_name}

## 你的任务
1. 为文章的优点辩护
2. 反驳不合理的批评
3. 解释作者可能的创作意图

## 待评审文章
---
{article[:8000]}...
---

[文章内容过长，已截断]

## 批评者观点汇总
---
{critics_summary}
---

## 输出格式
### 针对各批评的回应
### 被忽视的优点
### 核心辩护立场（3句话）
"""


def build_editor_prompt(article: str, debate_result: DebateResult) -> str:
    """构建编辑prompt"""
    
    all_rounds = "\n\n".join([
        f"=== Round {r.round_num} ===\n"
        f"批评者:\n" + "\n".join([f"[{k}]: {v[:500]}..." for k, v in r.critics.items()]) +
        f"\n辩护者:\n" + "\n".join([f"[{k}]: {v[:500]}..." for k, v in r.defenders.items()])
        for r in debate_result.rounds
    ])
    
    return f"""# 最终评审: 编辑综合

你是一位资深编辑，负责综合辩论双方的观战，给出最终评审报告。

## 待评审文章
---
{article[:8000]}...
---

## 完整辩论过程

{all_rounds}

## 你的任务
1. 独立判断，不偏袒任何一方
2. 对7个维度打分（1-10分）
3. 给出具体可操作的修改建议

## 输出格式
```markdown
# 📝 文章评审报告

## 📊 总评
- 综合得分：X/10
- 核心优势：3-5条
- 主要问题：3-5条

## 🔍 各维度评分
| 维度 | 得分 | 简评 |
|------|------|------|
| 结构 | X/10 | ... |
| 遣词造句 | X/10 | ... |
| 立意 | X/10 | ... |
| 文笔 | X/10 | ... |
| 风格 | X/10 | ... |
| 内容 | X/10 | ... |
| 技术 | X/10 | ... |

## ✨ 优点详解
## ⚠️ 问题详解
## 📝 修改建议
### 必须修改
### 建议修改
### 可选修改
## 💬 辩论裁判
| 焦点 | 批评者 | 辩护者 | 裁决 |
```
"""


def save_debate_result(result: DebateResult) -> Dict[str, str]:
    """保存辩论结果"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    result_dir = HISTORY_DIR / result.debate_id
    result_dir.mkdir(exist_ok=True)
    
    saved_files = {}
    
    # 保存JSON
    json_path = result_dir / "debate_data.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(result), f, ensure_ascii=False, indent=2)
    saved_files['json'] = str(json_path)
    
    # 保存Markdown格式的完整辩论
    md_content = [
        f"# 📚 完整辩论记录\n",
        f"**辩论ID**: {result.debate_id}\n",
        f"**时间**: {result.timestamp}\n",
        f"**配置**: {result.config.rounds}轮, {len(result.config.critics)}批评者, {len(result.config.defenders)}辩护者\n",
        f"\n---\n",
    ]
    
    for r in result.rounds:
        md_content.append(f"\n## Round {r.round_num}\n")
        md_content.append("\n### 批评者发言\n")
        for name, view in r.critics.items():
            md_content.append(f"\n#### 【{name}】\n{view}\n")
        md_content.append("\n### 辩护者发言\n")
        for name, view in r.defenders.items():
            md_content.append(f"\n#### 【{name}】\n{view}\n")
    
    md_content.append(f"\n---\n\n## 最终报告\n{result.final_report}\n")
    
    md_path = result_dir / "debate_full.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md_content))
    saved_files['markdown'] = str(md_path)
    
    return saved_files


def create_debate_id() -> str:
    """创建辩论ID"""
    return f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


if __name__ == "__main__":
    # 测试用
    print("AI Readers 辩论模块")
    print("此模块需要通过 OpenClaw sessions_spawn 调用")
    print("直接运行仅用于测试数据结构")
    
    # 测试数据结构
    config = DebateConfig(rounds=2, critics=["批评者A"], defenders=["辩护者A"])
    result = DebateResult(
        debate_id=create_debate_id(),
        timestamp=datetime.now().isoformat(),
        article_length=1000,
        config=config,
        rounds=[RoundResult(round_num=1, critics={}, defenders={})]
    )
    
    print(f"\n测试辩论ID: {result.debate_id}")
    print(f"保存路径示例: {HISTORY_DIR / result.debate_id}")
