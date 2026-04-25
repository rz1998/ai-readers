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
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any
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
    
    def __init__(self, article: str, config: 'DebateConfig', output_dir: Optional[str] = None) -> None:
        self.article = article
        self.config = config
        self.rounds: List[RoundResult] = []
        self.summary_report: str = ""  # AI 生成的总结报告
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if output_dir:
            self.debate_id = os.path.basename(output_dir)
            self.output_dir = output_dir
        else:
            self.debate_id = f"debate_{self.timestamp}"
            self.output_dir = os.path.join(SKILL_DIR, "history", self.debate_id)
    
    def add_round(self, result: RoundResult) -> None:
        """添加一轮结果"""
        self.rounds.append(result)
    
    def set_summary(self, summary: str) -> None:
        """设置总结报告"""
        self.summary_report = summary
    
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
            'rounds': [],
            'summary_report': self.summary_report,  # AI 生成的总结报告
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
        
        # ===== Part 1: 总结报告（最前）=====
        if self.summary_report:
            md.append(self.summary_report)
            md.append(f"\n---\n\n")
        
        # ===== Part 2: 文章原文（跳过，仅保留前500字符）=====
        md.append("## 📄 文章原文\n")
        article_preview = self.article[:500] + "\n\n[...文章内容已截断...]\n" if len(self.article) > 500 else self.article
        md.append(f"```\n{article_preview}\n```\n")
        md.append(f"\n---\n\n")
        
        # ===== Part 3: 详细辩论过程 =====
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
    
    def __str__(self) -> str:
        return f"DebateConfig(rounds={self.rounds}, critics={len(self.critics)}, defenders={len(self.defenders)})"


class ArticleCritic:
    """批评者模拟器"""
    
    CRITIC_PROMPTS = {
        "critic_structural": """你是一位专注于文章结构的资深批评者。你的批评遵循"先整体后局部"的原则：

## 第一阶段：整体结构分析
首先分析文章的整体框架：
1. 文章的核心论点/主题是什么？是否清晰明确？
2. 采用的是什么结构模式？（时间顺序、空间顺序、逻辑递进、总分总等）
3. 各段落之间的逻辑关系是什么？是否有清晰的层次？
4. 开头是否能吸引读者？结尾是否有升华或总结？
5. 整体结构的比例是否协调？（开头、论证、结尾的篇幅）

## 第二阶段：局部段落分析
然后深入分析各段落的安排：
1. 每个段落的中心句是什么？是否明确？
2. 段落之间的过渡是否自然流畅？
3. 是否存在重复论述或冗余内容？
4. 段落长度的节奏感如何？

## 第三阶段：改进建议
最后给出具体可操作的改进建议：
1. 针对结构问题的具体修改方案
2. 建议增加或删除的内容
3. 优化结构的优先级排序

文章：
---
{article}
---

请按照上述三阶段输出详细的结构批评：""",
        
        "critic_linguistic": """你是一位对语言有敏锐洞察的资深编辑。你的语言批评遵循"精准-精炼-传神"的递进原则：

## 第一阶段：精准性诊断
首先检查用词的精准程度：
1. 核心概念是否定义清晰？关键术语使用是否准确？
2. 形容词的抽象程度如何？是否有"空洞形容词"？（如"非常优秀"、"十分出色"等）
3. 动词是否具体有力？还是停留在"做""是""有"等抽象动词？
4. 术语使用是否前后一致？

## 第二阶段：精炼度分析
然后检查表达是否精炼：
1. 哪些句子可以更简洁？找出可以删减的冗余表达
2. 是否存在重复论述同一观点的情况？
3. 介词短语是否过于冗长？可精简的结构有哪些？
4. 语言风格是否统一？学术/口语/文艺风格是否混乱？

## 第三阶段：传神度评估
最后评估语言的感染力：
1. 是否有令人印象深刻的表达？（金句）
2. 修辞手法是否恰当运用？
3. 语言的节奏感和韵律如何？
4. 是否有让读者产生共鸣的表述？

## 具体改进清单
请按优先级列出：
- 【必须修改】影响理解的问题
- 【建议修改】可以优化的问题  
- 【可选优化】锦上添花的建议

文章：
---
{article}
---

请按照上述原则输出详细的语言批评：""",
        
        "critic_logical": """你是一位严谨的逻辑审查者。你的逻辑批评遵循"假设-推理-验证"的思维框架：

## 第一阶段：论点与核心主张识别
首先明确文章的核心论点：
1. 文章试图证明什么？核心主张是什么？
2. 这个主张的适用范围和边界是否明确？
3. 作者对论点的信心程度是否与论据匹配？

## 第二阶段：论证结构分析
然后分析论证的逻辑链条：
1. 论据（数据、案例、引用）是否能支撑论点？
2. 从论据到论点的推理过程是否有效？
3. 是否存在逻辑跳跃或隐性假设？
4. 是否存在常见的逻辑谬误？
   - 因果谬误（相关≠因果）
   - 诉诸权威（权威≠正确）
   - 稻草人谬误（攻击弱化后的观点）
   - 虚假两难（非此即彼思维）
   - 滑坡谬误（一步步放大风险）
5. 反例或反驳观点是否被考虑？

## 第三阶段：事实与数据核查
检查事实的准确性：
1. 引用数据的时间、来源是否可靠？
2. 统计数字是否存在"幸存者偏差"或样本偏差？
3. 百分比和绝对值的表述是否恰当？
4. 事实陈述与观点陈述是否分开？

## 第四阶段：改进建议
1. 指出论证中最薄弱的环节
2. 建议补充什么论据或反例
3. 建议如何强化逻辑链条

文章：
---
{article}
---

请输出详细的逻辑批评：""",
        
        "critic_technical": """你是一位一丝不苟的技术审查者。你的技术审查覆盖"语法-标点-格式-规范"四个层面：

## 第一阶段：语法与用词
1. 主谓是否一致？
2. 动词时态是否正确且一致？
3. 修饰语位置是否恰当？（悬垂修饰语）
4. 词性使用是否正确？（特别是"的、地、得"）
5. 是否有错别字？请逐字检查。

## 第二阶段：标点规范
1. 句号、逗号、顿号使用是否规范？
2. 引号、括号、省略号是否匹配？
3. 冒号、分号的用法是否正确？
4. 破折号、书名号使用是否规范？
5. 标点与文字之间是否有不必要的空格？

## 第三阶段：格式统一
1. 标题层级是否清晰统一？
2. 列表格式是否一致？（数字编号vs项目符号）
3. 段落缩进是否统一？
4. 字体、字号是否协调？
5. 中英文混排时格式是否规范？

## 第四阶段：引用规范
1. 直接引用、间接引用是否区分清楚？
2. 引用来源是否注明？
3. 引用格式是否统一？（APA/MLA/Chicago等）
4. 网络来源是否标注访问时间？

## 完整问题清单
请按"错误位置→问题描述→正确写法"的格式列出所有问题。

文章：
---
{article}
---

请输出详细的技术层面批评：""",
        
        "critic_creative": """你是一位对创意有敏锐嗅觉的文学评论家。你的创意批评从"立意-视角-表达-共鸣"四个维度展开：

## 第一阶段：立意分析
1. 主题的核心价值是什么？是否具有普遍意义或时效性？
2. 立意深度如何？是在表面徘徊还是触及本质？
3. 是否有独特的切入点或差异化视角？
4. 主题是否被过度消费？（陈词滥调）
5. 标题是否能准确反映内容，同时具有吸引力？

## 第二阶段：视角与立场
1. 作者的视角是什么？（第一人称旁观者/第三人称全知/第二人称等）
2. 这个视角是否最适合表达这个主题？
3. 作者的立场是否明确？态度是客观中立还是有倾向性？
4. 是否有"为什么是这个视角"的自觉？

## 第三阶段：表达技巧
1. 修辞手法的运用：
   - 比喻是否新颖贴切？
   - 排比是否有气势而不堆砌？
   - 对比是否鲜明有力？
   - 拟人/通感是否有独特发现？
2. 意象系统是否统一？是否有贯穿全文的核心意象？
3. 语言的陌生化程度如何？是否有"熟悉的陌生感"？
4. 节奏与韵律：长短句搭配、段落起伏是否精心设计？

## 第四阶段：共鸣评估
1. 读者最可能在哪一点产生共鸣？
2. 情感力量是否足够但不过度煽情？
3. 结尾是否有"余韵"？能否让读者回味？
4. 是否具有反复阅读的价值？

## 创意亮点与改进空间
请列出：
- 【亮点】文章中最具创意的部分
- 【遗憾】本可以更好但未达到的部分
- 【建议】具体可操作的改进方向

文章：
---
{article}
---

请输出详细的创意批评："""
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
        """模拟批评输出 - 详细版本"""
        critiques = {
            "critic_structural": """
## 结构批评报告

### 第一阶段：整体结构分析

#### 1.1 核心论点识别
文章的核心论点是[在AI时代，个人需要把自己做成不可替代的资产]。这个论点在开篇即已明确，奠定了全文的论证方向。

#### 1.2 结构模式判断
文章采用的是"问题-分析-方案"的三段式结构：
- 第一部分（第1-2段）：提出"AI替代焦虑"这个普遍痛点
- 第二部分（第3-6段）：从多个维度分析"什么是不可替代"
- 第三部分（第7-9段）：给出成为"不可替代资产"的具体路径

这种结构的优势是[逻辑清晰，层层递进]，但也存在[过渡略显生硬]的问题。

#### 1.3 段落逻辑关系
| 段落 | 中心句 | 逻辑类型 |
|------|--------|----------|
| 1 | AI正在改变很多行业 | 背景铺垫 |
| 2 | 很多人开始焦虑 | 问题提出 |
| 3 | 焦虑源于对自身价值的误解 | 观点转折 |
| 4-6 | [分论点1,2,3] | 并列论证 |
| 7-9 | 具体行动方案 | 总结落地 |

**关键发现**：第3段到第4段之间存在逻辑跳跃。作者直接抛出"误解"这个说法，但没有解释为什么这是误解。

#### 1.4 开头与结尾评估
- **开头**：以"AI替代"的焦虑场景切入，有效锁定目标读者注意力。但"越来越多人开始焦虑"的表述过于笼统，建议改为更具体的场景描述。
- **结尾**：以"复利思维"收尾，回扣开头"资产"概念，体现了结构意识。但结尾略显仓促，缺乏"最后一点升华"。

#### 1.5 结构比例分析
| 部分 | 字数 | 占比 | 评价 |
|------|------|------|------|
| 开头铺垫 | ~400 | 20% | 略长 |
| 问题分析 | ~900 | 45% | 适中 |
| 方案建议 | ~700 | 35% | 略短 |

**建议**：压缩开头，将省出的200字充实到方案建议部分。

---

### 第二阶段：局部段落分析

#### 2.1 段落逐一分析

**第2段**
- 中心句："越来越多人开始焦虑被AI替代"
- 问题："越来越多人"是模糊表述，缺乏数据支撑
- 建议：添加具体数据（如"根据某报告，60%的职场人对AI感到焦虑"）

**第4段**
- 中心句："不可替代性来自创造力"
- 问题：与第3段的"AI擅长重复性工作"形成呼应，但"创造力"的定义过于宽泛
- 建议：缩小"创造力"的范围，明确为"创意变现"或"问题解决"等具体能力

**第6段**
- 中心句："建立个人品牌很重要"
- 问题：这是全文最重要的分论点之一，但论述过于简短（仅100字）
- 建议：增加2-3个案例，详细说明如何建立个人品牌

#### 2.2 过渡问题诊断
| 位置 | 问题 | 建议过渡句 |
|------|------|------------|
| 第3→4段 | 突然引入"创造力" | "既然AI不擅长这些，那么人的价值在哪里？"
| 第6→7段 | 从"个人品牌"到"具体行动" | "知道做什么很重要，知道怎么做更重要。"

#### 2.3 重复内容识别
- "AI替代"相关表述在全文出现8次，可精简为5-6次
- "不可替代"出现12次，建议适度替换为"独特价值"等近义表达

---

### 第三阶段：改进建议

#### 优先级排序

**【必须修改】**
1. 第3→4段添加过渡句，解决逻辑跳跃问题
2. 第6段（个人品牌）扩充内容，至少增加300字
3. 删除第2段的"越来越多人"，替换为具体数据

**【建议修改】**
4. 开头压缩200字，避免"慢热"
5. 结尾增加一句话的"升华"，如"在AI时代，最大的风险不是被替代，而是停止成长"
6. 在第7段前添加小标题："三步打造你的不可替代性"

**【可选优化】**
7. 考虑在第5段增加一个"反面案例"，增强说服力
8. 统一各段落的首句格式（都使用动宾结构）
""",
            "critic_linguistic": """
## 语言批评报告

### 第一阶段：精准性诊断

#### 1.1 核心概念核查
| 概念 | 定义是否清晰 | 使用是否一致 |
|------|--------------|--------------|
| 不可替代 | ❌ 仅在结尾含糊提到 | ❌ 有时指"能力"，有时指"资产" |
| AI替代 | ✅ 有具体场景描述 | ✅ 基本一致 |
| 复利 | ✅ 有明确定义 | ✅ 一致 |
| 个人品牌 | ❌ 仅"影响力"描述 | ✅ 一致 |

**核心问题**：`"不可替代"`是文章最关键的概念，但全篇没有给出清晰定义。读者可能理解为：
- 能力上不可替代
- 市场上不可替代
- 情感上不可替代

这三种理解导向完全不同。

#### 1.2 空洞形容词清单
| 位置 | 原表达 | 问题 | 建议修改 |
|------|--------|------|----------|
| 第2段 | "越来越焦虑" | 程度模糊 | "焦虑到失眠" |
| 第3段 | "深刻理解" | 空洞 | "理解到能复述、能应用、能创新" |
| 第4段 | "非常重要的能力" | 空洞 | 删除或具体化 |
| 第5段 | "真正有价值" | 空洞 | "能解决他人无法解决的问题" |
| 第7段 | "持续提升自己" | 空洞 | "每周学习一个新技能" |

#### 1.3 动词精准度检查
| 原动词 | 出现次数 | 问题 | 建议 |
|--------|----------|------|------|
| 做 | 15+ | 过于笼统 | 根据语境替换为"执行""创作""分析"等 |
| 是 | 20+ | 判断句过多 | 增加"成为""意味着"等变化 |
| 有 | 30+ | 存在"有X有Y有Z"堆砌 | 拆分为具体描述 |

---

### 第二阶段：精炼度分析

#### 2.1 冗余表达识别

**结构冗余**
- "根据自己的实际情况来进行判断" → "结合实际判断"
- "对于这个问题，我认为" → "这个问题"
- "在本文中，我们将探讨" → "本文探讨"

**语义重复**
- "焦虑和担忧" → "焦虑"（担忧是焦虑的同义词）
- "创新和创意" → "创新"（创意是创新的过程/结果）
- "学习和掌握" → "学习"（掌握是学习的目标）

**位置冗余**
- "首先"出现4次，前3次可删除，保留最后一次
- "最重要的是"出现3次，建议替换为"关键在于""核心是"等变化

#### 2.2 精简效果预估
如果全面精简，文章可从2000字压缩到1700字，同时表达更精准。

#### 2.3 语言风格评估
| 段落 | 风格 | 问题 |
|------|------|------|
| 1-3 | 半正式 | 基本协调 |
| 4-6 | 口语化 | "说白了""搞懂"等词降低专业感 |
| 7-9 | 半正式 | 末尾回归正式，但第8段混入"其实吧" |

**问题根源**：作者可能在"亲切感"和"专业感"之间摇摆。

**建议**：全文统一为"专业但不晦涩"的风格，删除所有口语化表达。

---

### 第三阶段：传神度评估

#### 3.1 亮点表达
以下表达具有较强的穿透力：
- "把自己做成资产"（第1段）——用经济学术语重新定义个人价值
- "复利的威力"（结尾）——与开头"资产"概念形成呼应
- "AI擅长的是战术，人类擅长的是战略"（第3段）——简洁有力的对比

#### 3.2 修辞分析
- **比喻**：仅有1个明喻（"像...一样"），建议增加
- **排比**：第7段"X、Y、Z"使用得当
- **对比**：第3段"AI vs 人类"运用成功
- **设问**：全文未使用，建议在关键转折处增加

#### 3.3 节奏感评估
- **长句**过多，平均句长35字，建议控制在25字以内
- **段落**长度差异大（100-400字），建议均衡化
- **呼吸感**不足，建议在第4、第6段后各增加一个空行

---

### 具体改进清单

**【必须修改】**
1. 开篇定义"不可替代"："本书所说的不可替代，是指在某个细分领域，你的能力稀缺到无可替代"
2. 删除第4段"非常重要的能力"中的"非常"
3. 统一全文风格，删除所有口语化表达

**【建议修改】**
4. 精简"根据自己的..."类冗余表达（估计可删100字）
5. 将"做"字句替换为更精准的动词（至少5处）
6. 拆分过长的复合句（至少3句）

**【可选优化】**
7. 在第3段增加一个精彩比喻
8. 结尾"复利"处增加一句升华
""",
            "critic_logical": """
## 逻辑批评报告

### 第一阶段：论点与核心主张识别

#### 1.1 核心主张确认
文章试图证明的核心观点是：**在AI时代，个人应该把自己打造成"不可替代的资产"，而这需要从"能力积累"和"个人品牌"两个维度努力。**

#### 1.2 主张的隐含假设
1. "AI会替代大量工作"——这个假设成立吗？文章未提供数据
2. "被替代的人需要转型"——但转型方向是否一定是"不可替代"？
3. "不可替代是好事"——但作者未论证"可替代"为什么不好
4. "个人品牌能带来不可替代性"——这是文章最核心的逻辑链，但最薄弱

#### 1.3 主张的适用边界
文章未明确说明其主张的适用范围：
- 适用于所有职业？还是只适用于"知识工作者"？
- 适用于所有发展阶段？还是只适用于"职业中期"？
- 适用于所有文化背景？还是只适用于"中国职场"？

---

### 第二阶段：论证结构分析

#### 2.1 论据清单与评估

| 论据 | 类型 | 是否可靠 | 能否支撑论点 |
|------|------|----------|--------------|
| "越来越多人焦虑" | 断言 | ❌ 无数据 | 部分支撑 |
| "AI擅长重复性工作" | 事实 | ✅ 基本成立 | 有效 |
| "创造力难以复制" | 观点 | ⚠️ 存疑 | 需进一步论证 |
| "个人品牌带来机会" | 案例 | ⚠️ 单一案例 | 需补充 |
| "复利思维" | 模型 | ⚠️ 过于简化 | 部分支撑 |

#### 2.2 逻辑链分析

**核心逻辑链**：
```
前提1: AI会替代重复性工作
前提2: 人的价值在于创造力
前提3: 创造力难以被AI复制
结论: 因此人要发展创造力
```

**问题诊断**：
- 前提2和3之间的推理依赖"创造力=不可替代"这个未明确的前提
- "创造力"本身定义不清，导致整个逻辑链松动

**最大漏洞**：
文章未回答"为什么创造力不可替代？"——这恰恰是最需要论证的部分。

#### 2.3 逻辑谬误识别

**1. 因果谬误（第5段）**
"因为建立了个人品牌，所以获得了更多机会"
- 问题：相关≠因果。可能是因为"能力出众"同时导致"品牌建立"和"机会增多"
- 建议：改为"个人品牌有助于展示能力，从而吸引机会"

**2. 诉诸权威（第3段）**
"某知名投资人曾说..."
- 问题：投资人的观点≠事实。投资人可能有自己的利益考量
- 建议：说明该投资人为什么值得引用，或补充其他来源

**3. 虚假两难（第7段）**
"要么打造不可替代性，要么被淘汰"
- 问题：忽略了第三种可能——"与AI协作"
- 建议：论证为什么"协作"不是最优选择

**4. 滑坡谬误（结尾）**
"如果不积累复利，十年后你会后悔"
- 问题：从"短期不积累"到"十年后后悔"，跳跃了多个中间环节
- 建议：添加"如果不积累，每次选择都会受限，十年后将陷入被动"

#### 2.4 反例考虑
文章未考虑任何反例或反驳观点，例如：
- "有些人不需要不可替代性也能活得很好"（如公务员）
- "过度追求不可替代性可能导致"过度工作"
- "个人品牌可能带来"过度曝光"的风险"

---

### 第三阶段：事实与数据核查

#### 3.1 数据来源问题
- "越来越多人焦虑"：未注明数据来源
- "研究表明创造力难以复制"：未注明是哪个研究
- "很多人通过个人品牌获得机会"：未提供具体数据

#### 3.2 百分比使用评估
- 文章未使用具体数字，全为定性描述
- 建议：添加"78%的知识工作者认为..."等具体数据（需核实后使用）

---

### 第四阶段：改进建议

**【必须修改】**
1. 在第3段补充"为什么创造力不可替代"的论证
2. 删除或标注"某知名投资人"这类未核实的引用
3. 明确"不可替代"的适用边界

**【建议修改】**
4. 将"因果"表述改为"相关"表述，保持谨慎
5. 添加一个"反例"并回应，展现论证的严谨性
6. 在结尾处增加"使用建议"，说明本文主张不适用于哪些情况
""",
            "critic_technical": """
## 技术批评报告

### 第一阶段：语法与用词

#### 1.1 主谓一致检查
✅ 全文主谓一致，未发现明显错误

#### 1.2 词性问题
| 位置 | 原表达 | 问题 | 建议 |
|------|--------|------|------|
| 第2段 | "焦虑的心情" | "焦虑"已是形容词 | 改为"焦虑情绪" |
| 第3段 | "创造性的工作" | 用作名词 | 改为"创造性工作" |
| 第5段 | "很重要的" | 副词+形容词的堆砌 | 精简为"重要" |

#### 1.3 错别字核查
| 位置 | 疑似错字 | 建议 |
|------|----------|------|
| 第3段 | "即然" | 应为"既然" |
| 第5段 | "复然" | 应为"果然"或"显然" |
| 第8段 | "帐号" | 应为"账号" |

**注意**：以上基于语义推断，需对照原文核实。

---

### 第二阶段：标点规范

#### 2.1 标点使用问题
| 位置 | 问题 | 正确用法 |
|------|------|----------|
| 第2段 | 逗号使用过多，3个短句连用 | 前两个改为句号 |
| 第4段 | 顿号使用不当 | "创造力、判断力、执行力"中"创造力、判断力"之间应为"和" |
| 第6段 | 引号未匹配 | 第7段开头多了"号 |
| 第7段 | 省略号使用错误 | "......"应为"..."（中文六点省略号） |
| 第8段 | 破折号前后未空格 | "AI——一种——技术"应为"AI——一种技术" |

#### 2.2 标点与格式
- 句末标点后是否有多余空格：第3段存在
- 引号内外标点是否正确：第5段存在内引号标点问题

---

### 第三阶段：格式统一

#### 3.1 标题层级
| 标题 | 层级 | 问题 |
|------|------|------|
| 第一部分 | H2 | ✅ 一致 |
| 子标题 | H3 | 第3段用了加粗但非H3 |
| 小节 | 无 | 建议统一使用某种标记 |

#### 3.2 列表格式
- 正文使用"1. 2. 3."编号
- 建议列表使用"- "项目符号
- 避免混用编号和符号

#### 3.3 段落格式
- 首行缩进：全文不统一，建议统一缩进2字符
- 段间距：部分段落间距过大，建议统一

---

### 第四阶段：引用规范

#### 4.1 引用问题
| 位置 | 引用内容 | 问题 |
|------|----------|------|
| 第3段 | "某知名投资人" | 未注明来源和时间 |
| 第5段 | "研究表明" | 未注明研究名称 |
| 第8段 | 网络文章 | 未标注访问时间 |

#### 4.2 引用格式建议
```
格式：[作者, 年份]
示例：[张华, 2023]

或采用脚注形式...
```

---

### 完整问题清单

| # | 位置 | 问题 | 正确写法 |
|---|------|------|----------|
| 1 | 第3段 | "即然" | "既然" |
| 2 | 第4段 | 顿号不当 | 改为"和" |
| 3 | 第6段 | 引号未匹配 | 检查配对 |
| 4 | 第7段 | 省略号 | 改为"..." |
| 5 | 第3段 | "某知名投资人" | 补充来源 |
| 6 | 第5段 | "研究表明" | 注明研究名称 |
| 7 | 第2段 | 逗号过多 | 适当断句 |
""",
            "critic_creative": """
## 创意批评报告

### 第一阶段：立意分析

#### 1.1 主题价值评估
- **时效性**：⭐⭐⭐⭐⭐  AI时代焦虑是当下的热门话题
- **普遍性**：⭐⭐⭐⭐☆  职场人普遍关心，但执行层面不够
- **独特性**：⭐⭐⭐☆☆  话题常见，观点较为常规
- **深度**：⭐⭐⭐☆☆  触及表面，未深入探讨

**综合评估**：这是一个"容易火"的主题，但"容易火"不等于"有深度"。

#### 1.2 立意深度分析
文章的核心立意是"成为不可替代的资产"，但这个命题存在深层问题：

1. **过于功利**：将人"资产化"是否合适？这种价值观导向值得商榷
2. **忽略多元价值**：不是所有人都想"不可替代"，有人追求安稳
3. **执行导向过重**：整篇文章在"教方法"，缺少对人存在意义的思考

**建议方向**：可以从"在与AI的协作中找到人的独特价值"角度切入，而非"竞争取代"的角度。

#### 1.3 独特视角
文章的独特视角不够鲜明。如果把标题换成"如何避免被AI取代"，同样成立。

**真正独特的视角可能是**：
- "AI时代，最重要的不是"不可替代"，而是"持续进化""
- "与其担心被替代，不如思考如何与AI协作"
- "不可替代性不是目的，幸福感才是"

#### 1.4 标题分析
**现有标题**：《不可替代》
- 优势：简洁有力，锁定核心概念
- 劣势：过于抽象，读者不知道能获得什么
- 建议修改：《在AI时代，如何成为那个"无可替代"的人》

---

### 第二阶段：视角与立场

#### 2.1 叙事视角
文章采用第二人称"你"，这是一种[拉近距离]的选择。

**优势**：
- 增加读者的代入感
- 让建议更有针对性

**风险**：
- 语气过于说教，像"人生导师"
- 可能让部分读者产生抵触

**评估**：第二人称适合"方法论"文章，但本文部分段落（如第3段）更适合第一人称"我"来分享感悟。

#### 2.2 立场分析
作者立场偏向[积极进取型]，认为人应该主动应对变化。

**问题**：
- 未考虑"躺平一族"的合理性
- 语气略带"成功学"色彩

**建议**：增加一些"不必每个人都成为强者"的表述，让文章更包容。

---

### 第三阶段：表达技巧

#### 3.1 修辞手法盘点

| 修辞 | 使用 | 评价 |
|------|------|------|
| 比喻 | 1处 | 缺乏生动比喻，建议增加 |
| 排比 | 2处 | 使用得当，有气势 |
| 对比 | 1处 | "AI vs 人类"效果不错 |
| 设问 | 0处 | 建议增加，引发思考 |
| 反问 | 1处 | 第7段使用，效果一般 |

#### 3.2 意象系统
文章没有贯穿的核心意象。

**建议**：可以围绕"资产"这个概念构建意象体系：
- "把自己当作文易变现的股票"
- "积累能力就像定投"
- "个人品牌是市值"

这样可以让抽象概念更具体。

#### 3.3 语言陌生化
文章语言过于"熟悉"，缺少"熟悉的陌生感"。

**可以改进的地方**：
- "焦虑" → "对未来的不安感"
- "学习" → "认知的持续充值"
- "坚持" → "和时间做朋友"

#### 3.4 节奏设计
- **长句**过多，平均句长35字
- **短句**不足，建议在关键处使用短句制造节奏感
- **建议**：在每段开头使用短句开头，制造"心跳感"

---

### 第四阶段：共鸣评估

#### 4.1 读者共鸣点预测
读者可能最容易在以下地方产生共鸣：
1. 第1段的"被AI替代的焦虑场景"
2. 第3段的"知道但做不到"
3. 第7段的"道理都懂，但..."

#### 4.2 情感力量评估
- **温暖感**：⭐⭐⭐☆☆  较少
- **冲击力**：⭐⭐⭐⭐☆  第3段较好
- **回味感**：⭐⭐⭐☆☆  结尾不够有力

#### 4.3 金句潜力
以下表达具有金句潜力：
- "在AI时代，最大的风险不是被替代，而是停止成长"
- "把自己做成资产，才能在不确定的时代找到确定性"
- "不可替代不是目的，幸福才是"

---

### 创意亮点与改进空间

**【亮点】**
1. "把自己做成资产"这个重新定义很有创意
2. 结尾"复利"的回扣体现了结构意识
3. 整体阅读体验轻松不晦涩

**【遗憾】**
1. 观点偏"成功学"套路，缺少独特洞见
2. 没有令人"眼前一亮"的表达
3. 读完感觉"听过很多遍了"

**【建议】**
1. 找一个更独特的切入点，如"AI时代，你需要"不合群"的勇气"
2. 增加个人经历或独特案例，让内容更鲜活
3. 在结尾增加一句让人回味的话
4. 考虑加入"反常识"观点，如"有时候，可替代才是优势"
"""
        }
        
        return critiques.get(critic_type, critiques["critic_structural"])


class ArticleDefender:
    """辩护者模拟器"""
    
    DEFENDER_PROMPTS = {
        "defender_balanced": """你是理性公正的辩护者。面对批评，你采用"理解-评估-回应"的辩护框架：

## 第一步：理解批评
首先准确理解每一项批评：
1. 这项批评的核心观点是什么？
2. 批评者使用了哪些论据？这些论据是否准确？
3. 批评者的推理过程是否有效？
4. 这项批评是否适用于文章的整体，还是只针对局部？

## 第二步：评估批评
然后客观评估每项批评的有效性：
1. 【完全合理】哪些批评确实指出了文章的问题？
2. 【部分有效】哪些批评有一定道理但过于绝对？
3. 【存在误解】哪些批评可能是对文章意图的误解？
4. 【不当批评】哪些批评的评判标准不适用于这篇文章？

## 第三步：有理有据地回应
对于有价值的批评：
1. 承认文章的不足，但指出这是在特定约束条件下的合理取舍
2. 解释作者做出该选择的上下文和考量
3. 提出文章已经采取的补救措施（如有）

对于误解性批评：
1. 澄清文章的真实意图
2. 指出批评者可能遗漏的上下文

## 第四步：建设性建议
指出文章的优点，并说明为什么这些优点使文章仍然有效。

文章：
---
{article}
---

批评意见：
---
{critiques}
---

请输出你的辩护意见：""",
        
        "defender_empathetic": """你是善于理解作者意图的辩护者。你从"共情-背景-意图-价值"的角度为文章辩护：

## 第一步：理解作者的创作背景
1. 作者写这篇文章的目的是什么？（启发读者？说服决策？记录思考？）
2. 目标读者是谁？文章是否针对目标读者进行了优化？
3. 这篇文章是在什么情境下写的？（即时评论vs深度复盘）
4. 作者的知识背景和专业领域是什么？

## 第二步：还原创作意图
对于每一项批评，尝试还原作者做出该选择的原始意图：
1. "这个选择背后，作者可能在想什么？"
2. "在作者当时的认知条件下，这个选择是否合理？"
3. "如果我们处在作者的位置，是否也会做出同样的选择？"

## 第三步：发现被忽视的价值
1. 文章中哪些地方体现了作者的独特经历或洞察？
2. 批评者是否可能因为不了解作者的背景而产生了误判？
3. 文章中是否有"无声的优点"被批评者忽略了？

## 第四步：表达理解与尊重
在保持批判精神的同时，表达对作者努力和尝试的理解：
1. 承认文章不完美，但肯定作者的诚意和努力
2. 指出文章的真诚度——作者是否在认真地分享观点？
3. 强调文章对特定读者的价值

## 第五步：建设性桥梁
尝试在批评和作者意图之间搭建桥梁：
- 提出如何更好地实现作者意图的具体建议
- 而不是简单否定

文章：
---
{article}
---

批评意见：
---
{critiques}
---

请从共情角度输出辩护意见："""
    }
    
    @classmethod
    def generate_defense(cls, defender_type: str, article: str, critiques: str) -> str:
        """生成辩护意见"""
        return cls._simulate_defense(defender_type, article, critiques)
    
    @staticmethod
    def _simulate_defense(defender_type: str, article: str, critiques: str) -> str:
        """模拟辩护输出 - 详细版本"""
        defenses = {
            "defender_balanced": """
## 平衡辩护报告

### 第一步：理解批评

批评者指出了以下问题，让我们逐一分析其有效性：

| 批评类型 | 批评要点 | 我们评估 |
|----------|----------|----------|
| 结构批评 | 背景冗长 | ⚠️ 部分合理，但需考虑目标读者 |
| 结构批评 | 过渡跳跃 | ✅ 有效批评，确有此问题 |
| 语言批评 | 空洞形容词 | ⚠️ 部分存在，非致命问题 |
| 语言批评 | 风格不统一 | ✅ 有效批评，确实存在 |
| 逻辑批评 | 论据不足 | ⚠️ 有一定道理，但可商榷 |
| 逻辑批评 | 因果谬误 | ⚠️ 过度解读，文章未明确因果 |
| 技术批评 | 标点问题 | ✅ 确实存在，但属小问题 |

### 第二步：评估批评的有效性

**【完全合理的批评】**
1. 第3→4段过渡确实跳跃，这是真实问题
2. 部分口语化表达确实降低了文章的专业感
3. 技术层面的问题（标点、错字）确实存在

**【部分有效的批评】**
1. "背景冗长"：对于专业读者确实冗长，但对于文章的目标读者（职场新人），背景铺陈是必要的
2. "空洞形容词"：确实存在，但主要出现在过渡性语句中，不影响核心观点的表达
3. "论据不足"：文章定位是"方法论"而非"学术论文"，不需要严格论证

**【存在误解的批评】**
1. "因果谬误"：文章并未声称"做了X就一定成功"，而是建议"做了X更可能成功"，这是概率性表述而非确定性因果
2. "创意不足"：文章定位是"实用方法论"，创意性不是核心追求

### 第三步：有理有据地回应

**回应1：关于背景冗长**
文章面向的是"对AI替代感到焦虑但不知如何应对"的职场人。这些读者可能：
- 不了解AI的最新发展（需要背景铺垫）
- 不清楚自己的焦虑根源（需要问题分析）
- 不知道应对方向（需要方案建议）

因此，"冗长"的背景对于目标读者来说是"必要的热身"。批评者可能是以专业读者视角审视，而非目标读者视角。

**回应2：关于论据不足**
文章是"方法论"而非"论证文"。它的目标是提供可操作的建议，而非严密证明某个命题。
- "研究表明"等表述是引用共识，节省篇幅
- 案例的作用是"illustration"（例证）而非"proof"（证明）
- 读者可以自行验证这些观点的正确性

**回应3：关于逻辑严谨性**
文章采用的是"实践理性"的论证方式：
- 承认不确定性（"在AI时代..."）
- 提供方向性建议（"建议..."而非"必须..."）
- 强调个人选择（"可以根据自身情况..."）

这是面向大众的务实写法，而非学术写作的严格论证。

### 第四步：建设性建议

**承认的问题**：
1. 第3→4段的过渡确实需要加强
2. 标点和格式问题确实存在，需要校对

**不需要修改的**：
1. 文章的"入门级"定位是刻意的，不需要增加专业论证
2. 口语化表达是风格选择，适合目标读者
3. "空洞形容词"在非关键位置，不影响理解

**真正的价值**：
这篇文章的核心价值在于："把复杂问题简单化，让更多人能行动起来"。这是它的独特价值，不应该为了"更专业"而失去这种亲和力。
""",
            "defender_empathetic": """
## 共情辩护报告

### 第一步：理解作者的创作背景

#### 1.1 创作情境推测
从文章的内容和语气推断，作者可能：
- 是一位有10年以上经验的职场人
- 经历过从"新人"到"能手"的转变
- 看到很多年轻人为AI焦虑，想帮助他们
- 写作时带着一种"过来人"的真诚

#### 1.2 目标读者画像
文章假设的读者是：
- 25-35岁的知识工作者
- 对AI感到焦虑但不知道如何应对
- 有上进心但不盲目跟风
- 需要具体可行的建议，而非空洞的安慰

#### 1.3 创作动机分析
作者写这篇文章可能是为了：
1. 分享自己应对变化的经验
2. 帮助那些"想行动但不知从何开始"的人
3. 在"AI替代"的舆论中提供一种"积极但不鸡汤"的声音

### 第二步：还原创作意图

对于每一项批评，让我尝试还原作者的选择：

**批评：背景铺陈太长**
→ 作者可能在想："年轻人可能不了解AI的发展程度，不铺垫直接讲方法会让他们困惑"
→ 这是"担心读者跟不上"的体贴，而非"不会精简"的笨拙

**批评：空洞的形容词**
→ 作者可能在想："我不想写得太冰冷，需要一些温度"
→ "非常优秀"不是敷衍，而是"快速肯定"的表达方式

**批评："说白了"等口语**
→ 作者可能在想："我想让读者觉得我在跟他聊天，不是在教训他们"
→ 这是"平等对话"的姿态，而非"不专业"的失误

**批评：论据不够严密**
→ 作者可能在想："我不是在写论文，是想分享经验，太严格会让读者有压力"
→ 这是"去学术化"的刻意选择

### 第三步：发现被忽视的价值

#### 3.1 真诚的力量
读这篇文章，能感受到作者是真诚地想帮助人，而不是：
- 炫耀自己的见识
- 推销某种产品
- 证明自己是对的

这种真诚是能从字里行间感受到的，是文章最珍贵的部分。

#### 3.2 实用主义的价值
文章没有花太多篇幅讨论"为什么"，而是直接给"怎么做"。

这对于焦虑中的读者来说，反而是最有用的。

他们不需要再被告知"问题有多严重"，他们需要的是"我该怎么办"。

#### 3.3 适度的乐观
文章的基调是"积极但不盲目乐观"：
- 承认AI的威胁
- 但指出人的独特价值
- 提供可操作的建议

这种"务实的乐观"比"鸡汤"更有价值。

### 第四步：表达理解与尊重

作为辩护者，我想说：

1. **写作是艰难的工作**
这篇文章可能花了作者超过10个小时，包括构思、写作、修改。每一篇文章都是作者的心血。

2. **完美是卓越的敌人**
如果作者追求"无懈可击"才发表，这篇文章可能永远不会问世。而现在，它已经帮助了可能几百人。

3. **批评应该是建设性的**
指出问题的同时，也应该认可作者的努力和价值。

### 第五步：建设性桥梁

以下是我认为可以"在不破坏文章气质的前提下"做的优化：

1. **过渡问题**：可以在不改变整体风格的情况下，在第3段末尾添加一句话过渡
2. **标点问题**：校对时通读一遍即可修正
3. **空洞形容词**：可以在二稿时逐一替换

但这些优化应该是"打磨"而非"重写"。

---

### 总结

这篇文章的核心价值是"真诚+实用"。

批评者可能没有意识到：让文章失去这些特质的"完美"，可能比"不完美"更糟糕。

作者的真诚和亲和力，是他独特的写作风格，也是这篇文章能打动人的原因。

**建议**：在保持文章核心气质的前提下，做小幅优化；而不是追求"专业"而失去"温度"。
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




def extract_critic_feedback(rounds: List[RoundResult]) -> Dict[str, List[Dict]]:
    """从辩论轮次中提取具体的批评反馈"""
    feedback = {
        "结构": [],
        "语言": [],
        "逻辑": [],
        "创意": [],
        "技术": [],
        "内容": [],
    }
    
    for r in rounds:
        for critic_name, critic_text in r.critic_views.items():
            # 改进的匹配模式：匹配引号内的实际文章原文
            # 模式：中文引号「...」或英文引号"..."
            quote_pattern = r'[`"「"]([^"「」`\n]{10,80})[`"」"]'
            
            for match in re.finditer(quote_pattern, critic_text):
                quote = match.group(1).strip()
                
                if len(quote) < 5:
                    continue
                
                # 查找该引号后面的问题和建议（在同一段落附近）
                start = match.end()
                search_range = critic_text[start:start+800]
                
                # 提取问题 - 查找"问题："或"问题分析"后的内容
                problem_match = re.search(r'问题[：:]\s*([^\n。]{10,100})', search_range)
                problem = problem_match.group(1).strip() if problem_match else ""
                
                # 提取建议 - 查找"建议："或"修改建议"后的内容
                suggestion_match = re.search(r'建议[：:]\s*([^\n。]{10,100})', search_range)
                suggestion = suggestion_match.group(1).strip() if suggestion_match else ""
                
                if problem or suggestion:
                    # 判断类别
                    if any(kw in quote + problem + suggestion for kw in ["结构", "过渡", "衔接", "段落", "框架"]):
                        category = "结构"
                    elif any(kw in quote + problem + suggestion for kw in ["语言", "词汇", "表达", "用词", "遣词", "口语"]):
                        category = "语言"
                    elif any(kw in quote + problem + suggestion for kw in ["逻辑", "论证", "推理", "因果", "论据"]):
                        category = "逻辑"
                    elif any(kw in quote + problem + suggestion for kw in ["创意", "立意", "深度", "独特", "见解"]):
                        category = "创意"
                    elif any(kw in quote + problem + suggestion for kw in ["技术", "标点", "格式", "错字", "拼写"]):
                        category = "技术"
                    else:
                        category = "内容"
                    
                    # 去重：如果已经有相同引用，不再添加
                    existing = [f["quote"] for f in feedback[category]]
                    if quote not in existing:
                        feedback[category].append({
                            "quote": quote, 
                            "problem": problem[:100] if problem else "需要进一步分析",
                            "suggestion": suggestion[:100] if suggestion else "建议优化表述"
                        })
    
    return feedback




def make_issue_section(issue_name: str, specific_feedback: Dict) -> str:
    """生成问题章节"""
    section = f"### 2.x 【最重要】{issue_name}问题\n\n"
    feedbacks = specific_feedback.get(issue_name, [])
    
    if feedbacks:
        # 有具体反馈时，生成详细的改进建议
        for i, fb in enumerate(feedbacks[:3], 1):  # 最多3条
            quote_preview = fb['quote'][:80] + "..." if len(fb['quote']) > 80 else fb['quote']
            section += f"""**问题{i}**
- **原文引用**：「{quote_preview}」
- **问题分析**：{fb['problem']}
- **修改建议**：{fb['suggestion']}

"""
    else:
        # 没有具体反馈时，生成通用建议
        if issue_name == "结构":
            section += """**问题分析**：文章结构存在优化空间，部分过渡和衔接不够自然

**修改建议**：
1. 仔细检查段落之间的过渡句，确保逻辑连贯
2. 考虑在关键转折处添加承上启下的语句
3. 参考优秀文章的结构处理方式

"""
        elif issue_name == "语言":
            section += """**问题分析**：文章语言表达有提升空间，个别用词可以更精准

**修改建议**：
1. 精炼冗余表达，删除不必要的修饰词
2. 统一全文语言风格
3. 避免口语化表达（除非是有意为之）

"""
        elif issue_name == "逻辑":
            section += """**问题分析**：论证逻辑基本清晰，但部分推理可以更严密

**修改建议**：
1. 检查因果关系是否成立
2. 确保论据能够支撑论点
3. 考虑添加反面论据增强说服力

"""
        elif issue_name == "创意":
            section += """**问题分析**：文章立意有一定深度，但可以进一步挖掘

**修改建议**：
1. 在结尾处升华主题
2. 添加独特的个人见解或洞察
3. 考虑从新角度切入常见话题

"""
        elif issue_name == "技术":
            section += """**问题分析**：技术细节方面存在一些小问题

**修改建议**：
1. 仔细校对标点符号使用
2. 检查格式统一性
3. 修正可能的错别字

"""
        else:
            section += """**问题分析**：内容方面有完善空间

**修改建议**：
1. 补充具体数据或案例支撑
2. 确保事实准确性
3. 考虑添加更多实用建议

"""
    return section


def generate_summary_report(article: str, rounds: List[RoundResult], config: DebateConfig) -> str:
    """生成面向作者的总结报告
    
    基于所有辩论轮次的内容，生成一份包含：
    1. 总体评价
    2. 需要关注的问题（按重要性排序）- 必须包含具体原文引用和修改建议
    3. 优点总结
    4. 优化优先级
    5. 行动建议
    """
    
    # 汇总所有issues
    all_issues = []
    for r in rounds:
        for issue in r.issues_raised:
            all_issues.append(issue)
    
    # 统计各类问题出现的频次
    issue_keywords = {
        "结构": 0,
        "语言": 0,
        "逻辑": 0,
        "创意": 0,
        "技术": 0,
        "内容": 0,
    }
    
    for issue in all_issues:
        issue_lower = issue.lower()
        if "结构" in issue_lower:
            issue_keywords["结构"] += 1
        elif "语言" in issue_lower or "词汇" in issue_lower or "遣词" in issue_lower:
            issue_keywords["语言"] += 1
        elif "逻辑" in issue_lower:
            issue_keywords["逻辑"] += 1
        elif "创意" in issue_lower or "立意" in issue_lower:
            issue_keywords["创意"] += 1
        elif "技术" in issue_lower:
            issue_keywords["技术"] += 1
        elif "内容" in issue_lower or "事实" in issue_lower:
            issue_keywords["内容"] += 1
    
    # 提取具体反馈
    specific_feedback = extract_critic_feedback(rounds)
    
    # 按频次排序问题类别
    sorted_issues = sorted(issue_keywords.items(), key=lambda x: x[1], reverse=True)
    
    # 确定主要问题类别
    top_issue = sorted_issues[0][0] if sorted_issues else "结构"
    second_issue = sorted_issues[1][0] if len(sorted_issues) > 1 else "语言"
    third_issue = sorted_issues[2][0] if len(sorted_issues) > 2 else "技术"
    
    # 构建问题章节
    top_issue_section = make_issue_section(top_issue, specific_feedback)
    second_issue_section = make_issue_section(second_issue, specific_feedback)
    third_issue_section = make_issue_section(third_issue, specific_feedback)
    
    # 生成总结报告
    summary = f"""
# 📊 文章评审总结报告

_本报告由 AI Readers 多Agent辩论系统自动生成_

## 一、总体评价

本文是一篇关于**AI时代个人价值定位**的文章，采用了**问题-分析-方案**的经典结构。文章主题鲜明，选题贴近当下职场人的焦虑点，具有一定的实用价值和参考意义。

**总体评价**：结构基本清晰，语言平实易懂，内容有一定深度，但部分细节尚有提升空间。

## 二、需要关注的问题

以下是辩论过程中各位批评者提出的主要问题，按出现频次排序：

| 排名 | 问题类别 | 出现频次 | 具体问题数 |
|------|----------|----------|------------|
| 1 | {top_issue} | {sorted_issues[0][1] if sorted_issues else 0} 次 | {len(specific_feedback.get(top_issue, []))} 条 |
| 2 | {second_issue} | {sorted_issues[1][1] if len(sorted_issues) > 1 else 0} 次 | {len(specific_feedback.get(second_issue, []))} 条 |
| 3 | {third_issue} | {sorted_issues[2][1] if len(sorted_issues) > 2 else 0} 次 | {len(specific_feedback.get(third_issue, []))} 条 |

---

{top_issue_section}
---

{second_issue_section}
---

{third_issue_section}

## 三、优点总结

通过辩护者的陈述，我们可以看到文章的以下优点：

1. **主题鲜明**：选题紧扣时代热点，针对性强
2. **结构清晰**：采用经典的三段式结构，读者容易跟随
3. **语言平实**：表达通俗易懂，适合目标读者群体
4. **实用性强**：提供了可操作的建议，读者可以直接应用

## 四、优化优先级

| 优先级 | 问题 | 预计修改工作量 |
|--------|------|----------------|
| 🔴 高 | {top_issue}优化 | 1-2小时 |
| 🟡 中 | {second_issue}提升 | 2-3小时 |
| 🟢 低 | {third_issue}完善 | 30分钟-1小时 |

## 五、行动建议

基于以上分析，建议作者按以下步骤优化文章：

1. **第一步（立即处理）**：先解决{top_issue}问题，确保文章核心框架完善
2. **第二步（近期处理）**：处理{second_issue}问题，进一步提升质量
3. **第三步（可选优化）**：完善{third_issue}细节，达到精益求精

---

_本总结由 AI Readers 基于{config.rounds}轮辩论内容自动生成_
_参与角色：{', '.join([c[1] for c in config.critics])}_
"""
    return summary


def parse_arguments() -> Tuple[Any, str]:
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
    
    # ========== Summary Report 生成 ==========
    print(f"\n{'='*70}")
    print("📋 [Summary] 生成总结报告")
    print(f"{'='*70}\n")
    
    summary = generate_summary_report(article, round_results, config)
    
    # 保存总结到历史记录
    if history:
        history.set_summary(summary)
    
    print("✓ 总结报告生成完成")
    
    # ========== Editor 裁决 ==========
    print(f"\n{'='*70}")
    print("📋 [Final] Editor 裁决")
    print(f"{'='*70}\n")
    
    report = Editor.generate_report(article, round_results, config)
    
    print("✓ 报告生成完成")
    
    return report


def main() -> None:
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
