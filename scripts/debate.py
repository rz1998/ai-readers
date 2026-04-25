#!/usr/bin/env python3
"""
AI Readers - 多Agent多视角辩论评审系统

支持多角色多实例，可配置辩论轮次

使用方法:
    python debate.py "文章内容"
    python debate.py --rounds 3 "文章内容..."
    python debate.py --critics 3 --defenders 2 --rounds 4 "文章内容..."
    python debate.py --article article.txt --rounds 3

辩论流程:
    Round 1: Critics初审 → Defenders回应
    Round 2: Critics追问 → Defenders再辩
    ...
    Round N: Critics复审 → Defenders总结 → Editor裁决
"""

import argparse
import os
import sys
import json
import textwrap
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime

# 路径配置
SKILL_DIR = os.path.expanduser("~/workspace/ai-readers")
ROLES_DIR = os.path.join(SKILL_DIR, "ROLES")


@dataclass
class Agent:
    """Agent定义"""
    id: str
    name: str
    role: str  # 'critic', 'defender', 'editor'
    specialty: str  # 'structural', 'linguistic', etc.
    perspective: str  # 视角描述
    prompt_template: str = ""  # 从文件加载的提示词


@dataclass
class RoundResult:
    """单轮辩论结果"""
    round_num: int
    critic_views: Dict[str, str] = field(default_factory=dict)
    defender_views: Dict[str, str] = field(default_factory=dict)
    issues_raised: List[str] = field(default_factory=list)
    defenses_made: List[str] = field(default_factory=list)


class DebateHistory:
    """辩论历史记录器"""
    
    def __init__(self, article: str, config: 'DebateConfig', output_dir: str = None):
        self.article = article
        self.config = config
        self.rounds: List[RoundResult] = []
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if output_dir:
            self.debate_id = os.path.basename(output_dir)
            self.output_dir = output_dir
        else:
            self.debate_id = f"debate_{self.timestamp}"
            self.output_dir = os.path.join(SKILL_DIR, "history", self.debate_id)
    
    def add_round(self, result: RoundResult):
        """添加一轮结果"""
        self.rounds.append(result)
    
    def save_all(self) -> Dict[str, str]:
        """保存所有辩论过程，返回保存的文件路径"""
        os.makedirs(self.output_dir, exist_ok=True)
        saved_files = {}
        
        # 1. 保存完整辩论历史 (JSON)
        json_path = self._save_json()
        saved_files['json'] = json_path
        
        # 2. 保存完整辩论过程 (Markdown)
        md_path = self._save_markdown()
        saved_files['markdown'] = md_path
        
        # 3. 保存文章原文
        article_path = os.path.join(self.output_dir, "article.txt")
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(self.article)
        saved_files['article'] = article_path
        
        return saved_files
    
    def _save_json(self) -> str:
        """保存JSON格式的辩论历史"""
        data = {
            'debate_id': self.debate_id,
            'timestamp': self.timestamp,
            'config': {
                'rounds': self.config.rounds,
                'critics': [c[1] for c in self.config.critics],
                'defenders': [d[1] for d in self.config.defenders],
            },
            'article_length': len(self.article),
            'rounds': []
        }
        
        for r in self.rounds:
            round_data = {
                'round_num': r.round_num,
                'critics': r.critic_views,
                'defenders': r.defender_views,
                'issues_summary': r.issues_raised,
                'defenses_summary': r.defenses_made
            }
            data['rounds'].append(round_data)
        
        json_path = os.path.join(self.output_dir, "debate_history.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return json_path
    
    def _save_markdown(self) -> str:
        """保存Markdown格式的完整辩论过程"""
        md = []
        md.append(f"# 📚 完整辩论记录\n")
        md.append(f"**辩论ID**: `{self.debate_id}`\n")
        md.append(f"**时间**: {self.timestamp}\n")
        md.append(f"**轮次**: {self.config.rounds}轮\n")
        md.append(f"**批评者**: {', '.join([c[1] for c in self.config.critics])}\n")
        md.append(f"**辩护者**: {', '.join([d[1] for d in self.config.defenders])}\n")
        md.append(f"\n---\n\n")
        
        md.append("## 📄 文章原文\n")
        md.append(f"```\n{self.article}\n```\n")
        md.append(f"\n---\n\n")
        
        for r in self.rounds:
            md.append(f"## 🔄 Round {r.round_num}\n")
            md.append(f"\n### 👥 批评者发言\n")
            for name, view in r.critic_views.items():
                md.append(f"#### 【{name}】\n")
                md.append(f"{view}\n")
                md.append(f"\n---\n")
            
            md.append(f"\n### 🛡️ 辩护者回应\n")
            for name, view in r.defender_views.items():
                md.append(f"#### 【{name}】\n")
                md.append(f"{view}\n")
                md.append(f"\n---\n")
            
            md.append(f"\n{'='*70}\n\n")
        
        md_path = os.path.join(self.output_dir, "debate_full.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md))
        
        return md_path


class RoleLoader:
    """角色定义加载器"""
    
    @staticmethod
    def load_role_file(filepath: str) -> str:
        """加载单个角色文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def get_available_roles(role_type: str) -> List[str]:
        """获取可用的角色列表"""
        role_dir = os.path.join(ROLES_DIR, role_type)
        if not os.path.exists(role_dir):
            return []
        return [f.replace('.md', '') for f in os.listdir(role_dir) if f.endswith('.md')]


class DebateConfig:
    """辩论配置"""
    
    # 默认批评者（必须与 CRITIC_PROMPTS 的 key 一致）
    DEFAULT_CRITICS = [
        ("critic_structural", "结构批评者", "从结构框架角度分析"),
        ("critic_linguistic", "语言批评者", "从遣词造句角度分析"),
        ("critic_logical", "逻辑批评者", "从逻辑论证角度分析"),
        ("critic_creative", "创意批评者", "从立意风格角度分析"),
        ("critic_technical", "技术批评者", "从技术细节角度分析"),
    ]
    
    # 默认辩护者（必须与 DEFENDER_PROMPTS 的 key 一致）
    DEFAULT_DEFENDERS = [
        ("defender_balanced", "平衡辩护者", "理性分析，寻求共识"),
        ("defender_empathetic", "共情辩护者", "理解作者意图"),
        ("defender_content", "内容辩护者", "从内容事实角度辩护"),
        ("defender_expression", "表达辩护者", "从表达方式角度辩护"),
    ]
    
    # 默认编辑
    DEFAULT_EDITOR = ("editor_senior", "资深编辑")
    
    # 角色名称到ID的映射
    CRITIC_NAME_TO_ID = {
        '结构批评者': 'critic_structural',
        '逻辑批评者': 'critic_logical',
        '语言批评者': 'critic_linguistic',
        '创意批评者': 'critic_creative',
        '技术批评者': 'critic_technical',
        '商业批评者': 'critic_business',
    }
    
    DEFENDER_NAME_TO_ID = {
        '平衡辩护者': 'defender_balanced',
        '共情辩护者': 'defender_empathetic',
        '内容辩护者': 'defender_content',
        '表达辩护者': 'defender_expression',
    }
    
    def __init__(self, rounds: int = 3, num_critics: int = 2, num_defenders: int = 2, 
                 critics_list: list = None, defenders_list: list = None):
        self.rounds = rounds
        self.num_critics = num_critics
        self.num_defenders = num_defenders
        
        # 如果指定了角色名称列表，使用指定的角色
        if critics_list:
            self.critics = []
            for name in critics_list:
                cid = self.CRITIC_NAME_TO_ID.get(name)
                if cid:
                    # 找到对应的默认角色
                    for c in self.DEFAULT_CRITICS:
                        if c[0] == cid:
                            self.critics.append(c)
                            break
            if not self.critics:
                self.critics = self.DEFAULT_CRITICS[:num_critics]
        else:
            self.critics = self.DEFAULT_CRITICS[:num_critics]
        
        if defenders_list:
            self.defenders = []
            for name in defenders_list:
                did = self.DEFENDER_NAME_TO_ID.get(name)
                if did:
                    for d in self.DEFAULT_DEFENDERS:
                        if d[0] == did:
                            self.defenders.append(d)
                            break
            if not self.defenders:
                self.defenders = self.DEFAULT_DEFENDERS[:num_defenders]
        else:
            self.defenders = self.DEFAULT_DEFENDERS[:num_defenders]
        
        self.editor = self.DEFAULT_EDITOR
    
    def __str__(self):
        return f"DebateConfig(rounds={self.rounds}, critics={len(self.critics)}, defenders={len(self.defenders)})"


class ArticleCritic:
    """批评者模拟器"""
    
    CRITIC_PROMPTS = {
        "critic_structural": """你是一位专注于文章结构的批评者。分析以下文章，指出结构上的问题。

关注点：
- 整体框架是否清晰
- 段落安排是否合理
- 过渡衔接是否自然
- 开头结尾是否有力

文章：
---
{article}
---

请输出你的结构批评：""",
        
        "critic_linguistic": """你是一位对语言有敏锐洞察的批评者。分析以下文章，指出语言上的问题。

关注点：
- 用词是否精准
- 是否有冗余表达
- 语言风格是否统一
- 是否有空洞形容词

文章：
---
{article}
---

请输出你的语言批评：""",
        
        "critic_logical": """你是一位严谨的逻辑审查者。分析以下文章，指出逻辑和论证上的问题。

关注点：
- 论据是否支撑论点
- 是否存在逻辑跳跃
- 事实是否准确
- 是否有逻辑谬误

文章：
---
{article}
---

请输出你的逻辑批评：""",
        
        "critic_technical": """你是一位一丝不苟的技术审查者。分析以下文章，指出技术层面的问题。

关注点：
- 语法是否正确
- 标点是否规范
- 格式是否统一
- 引用是否规范

文章：
---
{article}
---

请输出你的技术批评：""",
        
        "critic_creative": """你是一位对创意有敏锐嗅觉的批评者。分析以下文章，从立意、风格、文笔角度批评。

关注点：
- 立意是否深刻
- 风格是否鲜明
- 文笔是否有感染力
- 是否有独特视角

文章：
---
{article}
---

请输出你的创意批评："""
    }
    
    @classmethod
    def generate_critique(cls, critic_type: str, article: str, context: Optional[str] = None) -> str:
        """生成批评意见"""
        prompt = cls.CRITIC_PROMPTS.get(critic_type, cls.CRITIC_PROMPTS["critic_structural"])
        prompt = prompt.format(article=article)
        
        if context:
            prompt += f"\n\n参考前轮辩论：\n{context}"
        
        # 模拟实际运行（实际应该调用LLM）
        return cls._simulate_critique(critic_type, article, context)
    
    @staticmethod
    def _simulate_critique(critic_type: str, article: str, context: Optional[str]) -> str:
        """模拟批评输出"""
        critiques = {
            "critic_structural": """
## 结构批评

### 整体框架问题
文章采用"背景-问题-分析-结论"的标准结构，但对于[目标读者]来说，背景铺垫略显冗长。

### 段落安排
- 第二段与第三段存在逻辑重叠，都是在讲现状
- 第四段突然引入新概念，缺少过渡

### 过渡问题
第三段到第四段之间缺少过渡句，读者可能感到跳跃。

### 建议
1. 精简开头背景，控制在300字以内
2. 在第四段前添加过渡句
3. 考虑使用小标题增强结构感
""",
            "critic_linguistic": """
## 语言批评

### 用词问题
- "非常优秀"：空洞形容词，无法传达实质信息
- "大概"出现3次：模糊表达降低可信度
- "基本上"：语义重复，可用"主要"替代

### 冗余表达
- "根据自己的实际情况来进行判断" → "结合实际判断"
- "对于...来说"出现5次，可精简

### 风格不统一
- 前半部分偏学术，后半部分口语化（如"说白了"）
- 建议统一为半正式风格

### 建议
1. 替换空洞形容词为具体描述
2. 减少模糊词汇使用
3. 统一全文语言风格
""",
            "critic_logical": """
## 逻辑批评

### 论据问题
- 第五段的统计数据未注明来源
- "研究表明"缺乏具体研究名称

### 论证漏洞
- 从用户增长直接跳到产品成功，逻辑跳跃
- 未考虑其他可能因素（市场因素、竞品问题等）

### 因果谬误
- "因为做了X，所以成功了"——忽略了其他变量

### 建议
1. 补充数据来源
2. 使用"可能""或许"等留有余地
3. 添加反事实分析
""",
            "critic_technical": """
## 技术批评

### 标点问题
- 第三段：顿号使用不当
- 第五段：引号未匹配
- 第七段：省略号应为省略号（...而非。。。）

### 语法错误
- "已经已经"重复
- "对于...而言赘余"

### 格式问题
- 标题格式不统一（有的加粗有的不加）
- 列表编号混乱（混用1.和-）

### 建议
1. 通读全文检查标点
2. 使用格式刷统一样式
3. 完成后全文校对一遍
""",
            "critic_creative": """
## 创意批评

### 立意问题
- 主题停留在表面，缺乏深层解读
- "成功"定义过于狭隘，未探讨复杂性

### 风格问题
- 缺乏个人特色，比较"标准化"
- 有明显的模板痕迹

### 感染力
- 文字较为平淡，缺少点睛之笔
- 未能让读者产生共鸣

### 建议
1. 加入个人经历增加温度
2. 用更有冲击力的开头吸引读者
3. 结尾避免说教，增加回味
"""
        }
        
        return critiques.get(critic_type, critiques["critic_structural"])


class ArticleDefender:
    """辩护者模拟器"""
    
    DEFENDER_PROMPTS = {
        "defender_balanced": """你是理性公正的辩护者。分析批评意见，为文章的合理之处辩护。

文章：
---
{article}
---

批评意见：
---
{critiques}
---

请输出你的辩护意见：""",
        
        "defender_empathetic": """你是善于理解作者意图的辩护者。从作者角度为文章辩护。

文章：
---
{article}
---

批评意见：
---
{critiques}
---

请输出你的辩护意见："""
    }
    
    @classmethod
    def generate_defense(cls, defender_type: str, article: str, critiques: str) -> str:
        """生成辩护意见"""
        return cls._simulate_defense(defender_type, article, critiques)
    
    @staticmethod
    def _simulate_defense(defender_type: str, article: str, critiques: str) -> str:
        """模拟辩护输出"""
        defenses = {
            "defender_balanced": """
## 平衡辩护

### 对结构批评的回应
背景铺陈的"冗长"需要结合文章定位来看。这是一篇面向[非专业读者]的入门文章，背景介绍是必要的——它帮助目标读者建立理解基础。对于专业读者可能多余，但对于目标读者恰恰是体贴。

### 对语言批评的回应
"非常优秀"等表达出现在[评论性段落]，是对他人观点的简略引用，目的是[快速建立对比]。在目标语境中是恰当的。

### 对逻辑批评的回应
关于数据来源：文末有完整参考文献，文中使用"研究表明"是学术惯例。只要参考文献可查，就符合规范。

### 对技术批评的回应
标点问题是真实存在的，但属于[不影响理解的轻微瑕疵]，可在最终校对时修正。

### 总结
综合考虑，文章的主要价值在于[清晰传达核心观点]，这些"问题"属于锦上不够完美，不影响整体发表价值。
""",
            "defender_empathetic": """
## 共情辩护

### 创作语境理解
作者写这篇文章时，可能处于[推广新产品]的情境下，需要在专业性和可读性之间做权衡。这种权衡本身就体现了对读者的体贴。

### 读者感受
作为[目标读者]，我读这篇文章的感觉是：
- 结构清晰，容易跟随
- 语言亲切，不觉得晦涩
- 例子生动，贴近生活
- 读完之后有收获

### 意图还原
- "冗长"的背景 → 为了让非专业读者跟上
- "空洞"的形容词 → 为了[情感共鸣]，不是精确描述
- "说白了" → 为了[拉近距离]，不是不专业

### 情感价值
文章传递了[积极向上的价值观]，这种真挚的情感是能从字里行间感受到的。批评者可能忽略了这种情感价值。

### 总结
每篇文章都有创作语境。在评判之前，不妨先问：作者想传达什么？读者实际感受如何？
"""
        }
        
        return defenses.get(defender_type, defenses["defender_balanced"])


class Editor:
    """编辑模拟器"""
    
    @staticmethod
    def generate_report(article: str, rounds: List[RoundResult], config: DebateConfig) -> str:
        """生成最终评审报告"""
        
        # 计算评分（模拟）
        scores = {
            "结构": 7,
            "遣词造句": 6,
            "立意": 6,
            "文笔": 7,
            "风格": 6,
            "内容": 7,
            "技术": 6
        }
        
        avg_score = sum(scores.values()) / len(scores)
        
        # 生成报告
        report = f"""
# 📝 文章评审报告

> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
> 辩论配置：{config}
> 辩论轮次：{config.rounds}轮

---

## 📊 总评

- **综合得分**：{avg_score:.1f}/10
- **评价等级**：{'优秀' if avg_score >= 8 else '良好' if avg_score >= 7 else '一般' if avg_score >= 6 else '需改进'}

### 核心优势
1. **结构清晰**：采用经典框架，逻辑链条完整
2. **语言亲切**：适合目标读者，通俗易懂
3. **实用性强**：提供了可操作的建议
4. **情感真挚**：能感受到作者的真诚

### 主要问题
1. **技术细节**：标点使用偶有不当
2. **语言精炼**：部分表达可更精准
3. **立意深度**：可进一步挖掘

---

## 🔍 各维度评分

| 维度 | 得分 | 简评 |
|------|------|------|
| 结构 | {scores['结构']}/10 | 框架清晰，但过渡略显生硬 |
| 遣词造句 | {scores['遣词造句']}/10 | 基本精准，偶有冗余 |
| 立意 | {scores['立意']}/10 | 定位准确，深度有限 |
| 文笔 | {scores['文笔']}/10 | 流畅通顺，感染力中等 |
| 风格 | {scores['风格']}/10 | 基本统一，辨识度一般 |
| 内容 | {scores['内容']}/10 | 论证基本有力，数据待完善 |
| 技术 | {scores['技术']}/10 | 小有瑕疵，不影响阅读 |

---

## ✨ 优点详解

### 1. 案例选取贴近生活
文章选取的案例都是普通人熟悉的生活场景，大大降低了理解门槛。这种案例选择体现了对目标读者的精准把握。

### 2. 逻辑框架清晰
采用"问题-分析-解决"的经典框架，读者可以轻松跟随作者的思路。这种结构虽然传统，但效果扎实。

### 3. 实用指导价值
结尾给出了具体的行动步骤，不是空洞的号召，而是真正可操作的建议。这种务实态度值得肯定。

### 4. 语言亲切友好
整篇文章的语言风格亲切自然，没有居高临下的说教感。这种平易近人的态度有利于知识传播。

---

## ⚠️ 问题详解

### 1. 技术细节不规范
- **问题**：标点使用偶有不当，如顿号滥用、引号不匹配
- **影响**：轻微影响阅读体验，专业感降低
- **严重程度**：🟡 中等（可快速修正）

### 2. 表达不够精炼
- **问题**：部分段落存在冗余表达，如"根据自己的实际情况来进行判断"
- **影响**：略显啰嗦，可读性下降
- **严重程度**：🟡 中等（建议精简）

### 3. 立意深度有限
- **问题**：主题停留在"怎么做"的层面，未深入探讨"为什么"
- **影响**：思想深度受限，读者收获有限
- **严重程度**：🟢 轻微（取决于文章定位）

---

## 📝 修改建议

### 必须修改（影响发表）
1. **技术规范**：检查全文标点使用，统一格式
2. **数据来源**：补充第三段数据的具体来源

### 建议修改（提升质量）
1. **精简语言**：将长句拆分，删除冗余表达
2. **增强过渡**：在段落间添加过渡句
3. **深化立意**：考虑添加"为什么"的部分

### 可选修改（锦上添花）
1. 添加小标题增强结构感
2. 在结尾添加互动问题引导读者思考
3. 考虑配图增强可读性

---

## 💬 辩论摘要

### 辩论配置
- **批评者**：{', '.join([c[1] for c in config.critics])}
- **辩护者**：{', '.join([d[1] for d in config.defenders])}
- **轮次**：{config.rounds}轮

### 关键争议点

| 争议点 | 批评者 | 辩护者 | 编辑裁决 |
|--------|--------|--------|----------|
| 开头冗长 | 应精简快速切入 | 照顾非专业读者有必要 | **部分采纳**：可精简但保留核心 |
| 语言风格 | 口语化破坏专业感 | 亲民风格有意识为之 | **部分采纳**：统一为半正式 |
| 数据来源 | 来源不明不可接受 | 参考文献可查符合惯例 | **批评采纳**：需补充来源 |
| 立意深度 | 缺乏深层挖掘 | 科普定位深度适宜 | **辩护采纳**：深度与定位匹配 |

### 共识
- ✅ 文章结构总体合理
- ✅ 案例选取贴近生活
- ✅ 语言通俗易懂
- ⚠️ 技术细节需完善

### 编辑独立判断

作为资深编辑，我认为这篇文章的核心价值在于**降低专业门槛，让更多人受益**。这是很有意义的工作。

建议作者在修改时记住一个原则：**科普文章的专业性不仅体现在内容准确上，也体现在表达规范上**。

---

*本报告由 AI Readers 多Agent辩论系统生成*
*参与角色：{', '.join([c[1] for c in config.critics])}、{', '.join([d[1] for d in config.defenders])}、资深编辑*
"""
        return report


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="AI Readers - 多Agent多视角辩论评审系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python debate.py "文章内容..."
  python debate.py --rounds 3 "文章内容..."
  python debate.py --critics 3 --defenders 2 --rounds 4 "文章内容..."
  python debate.py --article article.txt --rounds 3
        """
    )
    
    parser.add_argument('article', nargs='?', help='文章内容（也可以用 --file 指定文件）')
    parser.add_argument('--file', '-f', help='从文件读取文章')
    parser.add_argument('--rounds', '-r', type=int, default=3, help='辩论轮数 (默认: 3)')
    parser.add_argument('--critics', '-c', type=int, default=2, help='批评者数量 (默认: 2)')
    parser.add_argument('--defenders', '-d', type=int, default=2, help='辩护者数量 (默认: 2)')
    parser.add_argument('--critics-list', help='批评者名称列表 (JSON数组, 如 ["结构批评者","语言批评者"])')
    parser.add_argument('--defenders-list', help='辩护者名称列表 (JSON数组, 如 ["平衡辩护者","共情辩护者"]')
    parser.add_argument('--output-dir', help='输出目录 (默认为 ~/workspace/ai-readers/history/<timestamp>/)')
    parser.add_argument('--output', '-o', help='输出到文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 获取文章内容
    article = args.article
    
    if args.article and args.file:
        print("错误：不能同时指定文章内容和 --file 参数")
        sys.exit(1)
    
    if not article and not args.file:
        print("错误：请提供文章内容或使用 --article 指定文件")
        parser.print_help()
        sys.exit(1)
    
    # 从文件读取
    if args.article:
        article = args.article
    
    return args, article


def run_debate(article: str, config: DebateConfig, verbose: bool = False, 
                history: Optional[DebateHistory] = None) -> str:
    """运行辩论流程"""
    
    print("=" * 70)
    print("AI Readers - 多Agent多视角辩论评审系统")
    print("=" * 70)
    print(f"\n📄 文章长度: {len(article)} 字符")
    print(f"⚙️  辩论配置: {config}")
    print()
    
    # 存储辩论过程
    round_results: List[RoundResult] = []
    
    # ========== 辩论循环 ==========
    for round_num in range(1, config.rounds + 1):
        print(f"\n{'='*70}")
        print(f"📢 Round {round_num}/{config.rounds}")
        print(f"{'='*70}")
        
        result = RoundResult(round_num=round_num)
        
        # Phase 1: Critics 发言
        print(f"\n  📋 [Phase 1] Critics 发言")
        for i, (critic_id, critic_name, critic_perspective) in enumerate(config.critics):
            if verbose:
                print(f"\n    [{critic_name}] 正在分析...")
            
            # 获取前一轮的辩护作为上下文
            context = None
            if round_num > 1 and round_results:
                prev_result = round_results[-1]
                if prev_result.defender_views:
                    context = "\n\n".join(prev_result.defender_views.values())
            
            critique = ArticleCritic.generate_critique(critic_id, article, context)
            result.critic_views[critic_name] = critique
            result.issues_raised.append(f"[{critic_name}]: {critique[:200]}...")
            
            if verbose:
                print(f"    ✓ [{critic_name}] 完成")
            else:
                print(f"    ✓ {critic_name}", end=" ")
        
        print()
        
        # Phase 2: Defenders 回应
        print(f"\n  📋 [Phase 2] Defenders 回应")
        
        # 汇总所有批评
        all_critiques = "\n\n".join([
            f"=== {name} 的批评 ===\n{view}"
            for name, view in result.critic_views.items()
        ])
        
        for i, (defender_id, defender_name, defender_perspective) in enumerate(config.defenders):
            if verbose:
                print(f"\n    [{defender_name}] 正在辩护...")
            
            defense = ArticleDefender.generate_defense(defender_id, article, all_critiques)
            result.defender_views[defender_name] = defense
            result.defenses_made.append(f"[{defender_name}]: {defense[:200]}...")
            
            if verbose:
                print(f"    ✓ [{defender_name}] 完成")
            else:
                print(f"    ✓ {defender_name}", end=" ")
        
        print()
        
        # 存储本轮结果
        round_results.append(result)
        
        # 保存到历史记录
        if history:
            history.add_round(result)
        
        # 中间轮次提示
        if round_num < config.rounds:
            print(f"\n  ⏳ 等待下一轮辩论...")
    
    # ========== Editor 裁决 ==========
    print(f"\n{'='*70}")
    print("📋 [Final] Editor 裁决")
    print(f"{'='*70}\n")
    
    report = Editor.generate_report(article, round_results, config)
    
    print("✓ 报告生成完成")
    
    return report


def main():
    """主函数"""
    args, article = parse_arguments()
    
    # 从文件读取（如果指定）
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                article = f.read()
        except FileNotFoundError:
            print(f"⚠️ 文件未找到: {args.file}")
            sys.exit(1)
        except Exception as e:
            print(f"⚠️ 读取文件失败: {e}")
            sys.exit(1)
    
    # 验证文章长度
    if len(article) < 50:
        print("⚠️ 文章内容过短，请提供更完整的文章进行分析（至少50字符）")
        sys.exit(1)
    
    # 解析 critics 和 defenders 列表
    critics_list = None
    defenders_list = None
    if args.critics_list:
        import json
        try:
            critics_list = json.loads(args.critics_list)
        except:
            print("⚠️ critics-list 解析失败")
    if args.defenders_list:
        import json
        try:
            defenders_list = json.loads(args.defenders_list)
        except:
            print("⚠️ defenders-list 解析失败")
    
    # 创建辩论配置
    config = DebateConfig(
        rounds=args.rounds,
        num_critics=args.critics,
        num_defenders=args.defenders,
        critics_list=critics_list,
        defenders_list=defenders_list
    )
    
    # 创建辩论历史记录器
    output_dir = args.output_dir
    if output_dir:
        # Expand user path and ensure it exists
        output_dir = os.path.expanduser(output_dir)
    debate_history = DebateHistory(article, config, output_dir=output_dir)
    
    # 运行辩论
    report = run_debate(article, config, verbose=args.verbose, history=debate_history)
    
    # 输出报告
    print("\n" + "=" * 70)
    print("📝 最终评审报告")
    print("=" * 70)
    print(report)
    
    # 保存到文件（如果指定）
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✅ 报告已保存到: {args.output}")
    
    # 保存完整辩论历史
    print(f"\n💾 正在保存辩论历史...")
    saved_files = debate_history.save_all()
    print(f"✅ 辩论历史已保存:")
    for key, path in saved_files.items():
        print(f"   [{key}] {path}")


if __name__ == "__main__":
    main()
