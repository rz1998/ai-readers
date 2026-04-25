"""PDF生成工具 - 使用reportlab + 中文字体"""

import os
import re
from io import BytesIO
from pathlib import Path

import markdown


def markdown_to_html(text: str) -> str:
    """将Markdown文本转换为HTML"""
    if not text:
        return ''
    html = markdown.markdown(
        text,
        extensions=['tables', 'fenced_code', 'codehilite', 'nl2br']
    )
    return html


def clean_article_content(content: str) -> str:
    """清理文章内容中的文件路径和无关信息"""
    if not content:
        return ''
    # 移除文件路径
    content = re.sub(r'ﬁle:///[^•\n]*', '', content)
    # 移除页码标记如 "1/146"
    content = re.sub(r'\d+/\d+\s*$', '', content, flags=re.MULTILINE)
    # 移除多余的空白行
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def generate_pdf_from_html(html_content: str, output_path: str) -> bool:
    """
    从HTML内容生成PDF
    
    Args:
        html_content: HTML字符串
        output_path: 输出PDF文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        
        # 注册中文字体
        font_path = '/app/LXGWWenKai-Regular.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('LXGWWenKai', font_path))
        else:
            print(f"Font not found: {font_path}")
            return False
        
        # 创建PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 样式定义
        title_style = ParagraphStyle(
            'Title',
            fontName='LXGWWenKai',
            fontSize=18,
            alignment=1,  # 居中
            spaceAfter=20,
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            fontName='LXGWWenKai',
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#1e40af'),
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            fontName='LXGWWenKai',
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor('#374151'),
        )
        
        body_style = ParagraphStyle(
            'Body',
            fontName='LXGWWenKai',
            fontSize=10,
            leading=16,
        )
        
        small_style = ParagraphStyle(
            'Small',
            fontName='LXGWWenKai',
            fontSize=9,
            leading=14,
        )
        
        # 故事元素
        story = []
        
        # 提取标题
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
        if title_match:
            story.append(Paragraph(title_match.group(1), title_style))
            story.append(Spacer(1, 10))
        
        # 提取元信息
        meta_pattern = r'<p><strong>([^<]+)</strong>([^<]*)</p>'
        meta_matches = re.findall(meta_pattern, html_content)
        for label, value in meta_matches:
            value = value.strip()
            if value and value != 'N/A':
                story.append(Paragraph(f"<b>{label}</b>{value}", body_style))
        
        story.append(Spacer(1, 20))
        
        # 提取文章内容（已清理）
        article_match = re.search(r'<h2[^>]*>📝[^<]*</h2>.*?<div class="article-content">(.*?)</div>', html_content, re.DOTALL)
        if article_match:
            story.append(Paragraph("📝 文章内容", heading_style))
            article_text = re.sub(r'<[^>]+>', '', article_match.group(1))
            # 清理文件路径
            article_text = clean_article_content(article_text)
            # 截取前800字
            article_text = article_text[:800] + '...' if len(article_text) > 800 else article_text
            story.append(Paragraph(article_text, small_style))
            story.append(Spacer(1, 15))
        
        # 提取评分（如果有）
        score_match = re.search(r'<div class="score">(\d+)</div>', html_content)
        if score_match:
            score = score_match.group(1)
            story.append(Paragraph(f"<b>综合评分：</b>{score} / 10", body_style))
            story.append(Spacer(1, 15))
        
        # 提取优点
        pros_match = re.search(r'<h3[^>]*>✅[^<]*</h3>(.*?)</ul>', html_content, re.DOTALL)
        if pros_match:
            story.append(Paragraph("✅ 优点", subheading_style))
            items = re.findall(r'<li>(.*?)</li>', pros_match.group(1), re.DOTALL)
            for item in items[:5]:
                item_text = re.sub(r'<[^>]+>', '', item)
                story.append(Paragraph(f"• {item_text}", small_style))
        
        # 提取缺点
        cons_match = re.search(r'<h3[^>]*>❌[^<]*</h3>(.*?)</ul>', html_content, re.DOTALL)
        if cons_match:
            story.append(Paragraph("❌ 缺点", subheading_style))
            items = re.findall(r'<li>(.*?)</li>', cons_match.group(1), re.DOTALL)
            for item in items[:5]:
                item_text = re.sub(r'<[^>]+>', '', item)
                story.append(Paragraph(f"• {item_text}", small_style))
        
        story.append(Spacer(1, 15))
        
        # 提取辩论过程
        rounds_section = re.search(r'<h2[^>]*>🔄[^<]*</h2>(.*?)(?:<div class="footer"|</body>)', html_content, re.DOTALL)
        if rounds_section:
            story.append(Paragraph("🔄 辩论过程", heading_style))
            
            # 提取每轮 - 使用 finditer 找到每轮的起始位置
            round_pattern = r'<h3[^>]*>第\s*(\d+)\s*轮</h3>'
            content = rounds_section.group(1)
            matches = list(re.finditer(round_pattern, content))
            
            for idx, m in enumerate(matches):
                round_num = m.group(1)
                # 每轮内容从当前位置到下一轮之前
                start = m.end()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
                round_content = content[start:end]
                
                story.append(Paragraph(f"<b>第 {round_num} 轮</b>", subheading_style))
                
                # 提取批评者观点 - 使用分割方法
                critic_parts = re.split(r'(<div class="critic-content">)', round_content)
                critics_html = []
                current = ''
                for p in critic_parts:
                    if p == '<div class="critic-content">':
                        current = p
                    else:
                        current += p
                        if '</div>' in current and 'agent-name' in current:
                            critics_html.append(current)
                            current = ''
                
                if critics_html:
                    story.append(Paragraph("批评者观点：", small_style))
                    for critic_html in critics_html[:5]:  # 最多5个批评者
                        name_match = re.search(r'class="agent-name"[^>]*>([^<]+)', critic_html)
                        text_content = re.sub(r'<[^>]+>', '', critic_html)
                        text_content = re.sub(r'🔴|🟢', '', text_content).strip()
                        text_content = text_content[:200] + '...' if len(text_content) > 200 else text_content
                        if name_match and text_content:
                            name = name_match.group(1).replace('🔴 ', '').replace('🟢 ', '')
                            story.append(Paragraph(f"<b>{name}:</b> {text_content}", small_style))
                
                # 提取辩护者观点 - 使用同样的分割方法
                defender_parts = re.split(r'(<div class="defender-content">)', round_content)
                defenders_html = []
                current = ''
                for p in defender_parts:
                    if p == '<div class="defender-content">':
                        current = p
                    else:
                        current += p
                        if '</div>' in current and 'agent-name' in current:
                            defenders_html.append(current)
                            current = ''
                
                if defenders_html:
                    story.append(Spacer(1, 5))
                    story.append(Paragraph("辩护者观点：", small_style))
                    for defender_html in defenders_html[:4]:  # 最多4个辩护者
                        name_match = re.search(r'class="agent-name"[^>]*>([^<]+)', defender_html)
                        text_content = re.sub(r'<[^>]+>', '', defender_html)
                        text_content = re.sub(r'🔴|🟢', '', text_content).strip()
                        text_content = text_content[:200] + '...' if len(text_content) > 200 else text_content
                        if name_match and text_content:
                            name = name_match.group(1).replace('🔴 ', '').replace('🟢 ', '')
                            story.append(Paragraph(f"<b>{name}:</b> {text_content}", small_style))
                
                story.append(Spacer(1, 10))
        
        # 添加页脚
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            fontName='LXGWWenKai',
            fontSize=8,
            textColor=colors.grey,
            alignment=1,
        )
        story.append(Paragraph("本报告由 AI Readers 自动生成", footer_style))
        
        # 构建PDF
        doc.build(story)
        
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
        
    except Exception as e:
        print(f"Error generating PDF with reportlab: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_html_report_template(project_data: dict) -> str:
    """
    生成HTML报告模板
    
    Args:
        project_data: 项目数据字典
        
    Returns:
        str: HTML字符串
    """
    article = project_data.get('article', '')
    config = project_data.get('config', {})
    rounds = project_data.get('rounds', [])
    final_report = project_data.get('final_report') or {}
    created_at = project_data.get('created_at', '')
    
    # 格式化创建时间
    if created_at and created_at != 'N/A':
        try:
            # 格式: 2026-04-25T03:46:41.917206 -> 2026-04-25 03:46:41
            created_at = created_at.replace('T', ' ').split('.')[0]
        except:
            created_at = ''
    
    # 清理文章内容中的文件路径
    article = clean_article_content(article)
    
    # 构建HTML
    html_parts = [
        f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>辩论评审报告 - {project_data.get('title', '未命名')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: "Droid Sans Fallback", "Noto Sans CJK SC", "Source Han Sans SC", 
                       "WenQuanYi Micro Hei", "Microsoft YaHei", "PingFang SC", sans-serif;
            font-size: 11pt;
            line-height: 1.8;
            color: #333;
            padding: 2cm;
        }}
        h1 {{
            font-size: 22pt;
            text-align: center;
            color: #1a1a1a;
            margin-bottom: 20pt;
            border-bottom: 2pt solid #3b82f6;
            padding-bottom: 10pt;
        }}
        h2 {{
            font-size: 14pt;
            color: #1e40af;
            margin-top: 20pt;
            margin-bottom: 10pt;
            border-left: 3pt solid #3b82f6;
            padding-left: 8pt;
        }}
        h3 {{
            font-size: 12pt;
            color: #374151;
            margin-top: 15pt;
            margin-bottom: 8pt;
        }}
        h4 {{
            font-size: 11pt;
            color: #4b5563;
            margin-top: 10pt;
            margin-bottom: 5pt;
        }}
        .meta {{
            text-align: center;
            color: #666;
            font-size: 10pt;
            margin-bottom: 20pt;
        }}
        .article-content {{
            background: #f9fafb;
            padding: 15pt;
            border-radius: 6pt;
            margin-bottom: 20pt;
            white-space: pre-wrap;
            font-size: 10pt;
        }}
        .score-section {{
            text-align: center;
            margin: 25pt 0;
        }}
        .score {{
            font-size: 48pt;
            font-weight: bold;
            color: #3b82f6;
        }}
        .score-label {{
            font-size: 12pt;
            color: #666;
        }}
        .dimensions {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10pt;
            margin: 15pt 0;
        }}
        .dimension {{
            background: #f3f4f6;
            padding: 10pt;
            border-radius: 4pt;
        }}
        .dimension-name {{
            font-weight: bold;
            margin-bottom: 3pt;
        }}
        .dimension-score {{
            color: #3b82f6;
            font-weight: bold;
        }}
        .dimension-comment {{
            font-size: 9pt;
            color: #666;
        }}
        .pros-cons {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15pt;
            margin: 15pt 0;
        }}
        .pros {{
            background: #ecfdf5;
            padding: 12pt;
            border-radius: 6pt;
        }}
        .cons {{
            background: #fef2f2;
            padding: 12pt;
            border-radius: 6pt;
        }}
        .suggestions {{
            background: #fffbeb;
            padding: 12pt;
            border-radius: 6pt;
            margin-top: 15pt;
        }}
        .round-section {{
            margin-top: 20pt;
            page-break-inside: avoid;
        }}
        .critic-content, .defender-content {{
            background: #f9fafb;
            padding: 10pt;
            margin: 8pt 0;
            border-radius: 4pt;
            border-left: 3pt solid #6b7280;
            font-size: 9pt;
        }}
        .critic-content {{
            border-left-color: #ef4444;
        }}
        .defender-content {{
            border-left-color: #22c55e;
        }}
        .agent-name {{
            font-weight: bold;
            margin-bottom: 5pt;
        }}
        /* Markdown rendered content */
        .critic-content table, .defender-content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10pt 0;
            font-size: 8pt;
        }}
        .critic-content th, .defender-content th {{
            background: #e5e7eb;
            padding: 4pt;
            border: 1pt solid #d1d5db;
            text-align: left;
        }}
        .critic-content td, .defender-content td {{
            padding: 4pt;
            border: 1pt solid #d1d5db;
        }}
        .critic-content pre, .defender-content pre {{
            background: #f3f4f6;
            padding: 8pt;
            border-radius: 4pt;
            overflow-x: auto;
            font-size: 8pt;
        }}
        .critic-content code, .defender-content code {{
            background: #f3f4f6;
            padding: 1pt 3pt;
            border-radius: 2pt;
            font-size: 8pt;
        }}
        .critic-content ul, .critic-content ol,
        .defender-content ul, .defender-content ol {{
            margin: 6pt 0;
            padding-left: 18pt;
        }}
        .critic-content li, .defender-content li {{
            margin: 3pt 0;
        }}
        .critic-content strong, .defender-content strong {{
            color: #1f2937;
        }}
        ul, ol {{
            margin: 8pt 0;
            padding-left: 20pt;
        }}
        li {{
            margin: 4pt 0;
        }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 9pt;
            margin-top: 30pt;
            padding-top: 10pt;
            border-top: 1pt solid #e5e7eb;
        }}
    </style>
</head>
<body>
    <h1>📊 AI Readers 辩论评审报告</h1>
    
    <div class="meta">
        <p><strong>项目名称：</strong>{project_data.get('title', '未命名')}</p>
        <p><strong>创建时间：</strong>{created_at or 'N/A'}</p>
        <p><strong>辩论配置：</strong>{config.get('rounds', 1)}轮 | {len(config.get('critics', []))}位批评者 | {len(config.get('defenders', []))}位辩护者</p>
    </div>
    
    <h2>📝 文章内容</h2>
    <div class="article-content">{article[:2000]}{'...' if len(article) > 2000 else ''}</div>
"""
    ]
    
    # 添加最终报告
    if final_report:
        score = final_report.get('score', 0)
        dimensions = final_report.get('dimensions', [])
        pros = final_report.get('pros', [])
        cons = final_report.get('cons', [])
        suggestions = final_report.get('suggestions', {})
        
        html_parts.append(f"""
    <div class="score-section">
        <div class="score">{score}</div>
        <div class="score-label">综合评分</div>
    </div>
    
    <h2>📈 多维度分析</h2>
    <div class="dimensions">
""")
        for dim in dimensions:
            html_parts.append(f"""
        <div class="dimension">
            <div class="dimension-name">{dim.get('name', 'N/A')}</div>
            <div class="dimension-score">评分: {dim.get('score', 0)}</div>
            <div class="dimension-comment">{dim.get('comment', '')}</div>
        </div>
""")
        html_parts.append("    </div>")
        
        # 优点缺点
        html_parts.append("""
    <div class="pros-cons">
        <div class="pros">
            <h3>✅ 优点</h3>
            <ul>
""")
        for pro in pros:
            html_parts.append(f"        <li>{pro}</li>\n")
        html_parts.append("""
            </ul>
        </div>
        <div class="cons">
            <h3>❌ 缺点</h3>
            <ul>
""")
        for con in cons:
            html_parts.append(f"        <li>{con}</li>\n")
        html_parts.append("""
            </ul>
        </div>
    </div>
""")
        
        # 建议
        if suggestions:
            must_list = suggestions.get('must', [])
            should_list = suggestions.get('should', [])
            optional_list = suggestions.get('optional', [])
            
            if any([must_list, should_list, optional_list]):
                html_parts.append("""
    <div class="suggestions">
        <h3>💡 改进建议</h3>
""")
                if must_list:
                    html_parts.append("<h4>【必须修改】</h4><ul>")
                    for item in must_list:
                        html_parts.append(f"<li>{item}</li>")
                    html_parts.append("</ul>")
                if should_list:
                    html_parts.append("<h4>【建议修改】</h4><ul>")
                    for item in should_list:
                        html_parts.append(f"<li>{item}</li>")
                    html_parts.append("</ul>")
                if optional_list:
                    html_parts.append("<h4>【可选优化】</h4><ul>")
                    for item in optional_list:
                        html_parts.append(f"<li>{item}</li>")
                    html_parts.append("</ul>")
                html_parts.append("    </div>")
    
    # 辩论过程
    if rounds:
        html_parts.append("""
    <h2>🔄 辩论过程</h2>
""")
        for round_data in rounds:
            round_num = round_data.get('round_num', round_data.get('roundNum', 1))
            html_parts.append(f"""
    <div class="round-section">
        <h3>第 {round_num} 轮</h3>
""")
            
            # 批评者 - 支持 dict 和 list 两种格式
            critics = round_data.get('critics', {})
            if critics:
                html_parts.append("<h4>👥 批评者观点</h4>")
                # dict 格式: {name: content}
                if isinstance(critics, dict):
                    for name, content in critics.items():
                        content_html = markdown_to_html(content)
                        html_parts.append(f"""
        <div class="critic-content">
            <div class="agent-name">🔴 {name}</div>
            <div>{content_html}</div>
        </div>
""")
                # list 格式: [{name, content}]
                elif isinstance(critics, list):
                    for critic in critics:
                        if isinstance(critic, dict):
                            name = critic.get('name', '批评者')
                            content = critic.get('content', '')
                            content_html = markdown_to_html(content)
                            html_parts.append(f"""
        <div class="critic-content">
            <div class="agent-name">🔴 {name}</div>
            <div>{content_html}</div>
        </div>
""")
            
            # 辩护者 - 支持 dict 和 list 两种格式
            defenders = round_data.get('defenders', {})
            if defenders:
                html_parts.append("<h4>👥 辩护者观点</h4>")
                # dict 格式: {name: content}
                if isinstance(defenders, dict):
                    for name, content in defenders.items():
                        content_html = markdown_to_html(content)
                        html_parts.append(f"""
        <div class="defender-content">
            <div class="agent-name">🟢 {name}</div>
            <div>{content_html}</div>
        </div>
""")
                # list 格式: [{name, content}]
                elif isinstance(defenders, list):
                    for defender in defenders:
                        if isinstance(defender, dict):
                            name = defender.get('name', '辩护者')
                            content = defender.get('content', '')
                            content_html = markdown_to_html(content)
                            html_parts.append(f"""
        <div class="defender-content">
            <div class="agent-name">🟢 {name}</div>
            <div>{content_html}</div>
        </div>
""")
            
            html_parts.append("    </div>")
    
    # 页脚
    html_parts.append(f"""
    <div class="footer">
        <p>本报告由 AI Readers 自动生成</p>
    </div>
</body>
</html>
""")
    
    return ''.join(html_parts)
