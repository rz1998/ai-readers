"""PDF生成工具 - 使用reportlab + 中文字体，支持标准Markdown格式"""

import os
import re
from pathlib import Path

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


def clean_article_content(content: str) -> str:
    """清理文章内容中的文件路径和无关信息"""
    if not content:
        return ''
    # 移除文件路径
    content = re.sub(r'ﬁle:///[^•\n]*', '', content)
    content = re.sub(r'file:///[^•\n]*', '', content)
    # 移除页码标记如 "1/146"
    content = re.sub(r'\d+/\d+\s*$', '', content, flags=re.MULTILINE)
    # 移除CJK兼容区中很少使用的字符（ radic als, etc）
    # 这些字符在大多数字体中不支持
    content = re.sub(r'[\u2E80-\u2EFF\u2F00-\u2FD5]', '', content)
    # 移除回车符
    content = content.replace('\r', '')
    # 移除多余的空白行
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def parse_markdown_to_paragraphs(md_content: str) -> list:
    """将Markdown内容解析为带有样式的段落列表"""
    paragraphs = []
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 跳过水平线
        if re.match(r'^---+$', line.strip()) or re.match(r'^\*\*\*+$', line.strip()):
            i += 1
            continue
        
        # H1 标题
        if line.startswith('# '):
            paragraphs.append(('h1', line[2:].strip()))
        
        # H2 标题
        elif line.startswith('## '):
            paragraphs.append(('h2', line[3:].strip()))
        
        # H3 标题
        elif line.startswith('### '):
            paragraphs.append(('h3', line[4:].strip()))
        
        # H4 标题
        elif line.startswith('#### '):
            paragraphs.append(('h4', line[5:].strip()))
        
        # 表格行
        elif line.startswith('|'):
            table_rows = [line]
            while i + 1 < len(lines) and lines[i + 1].startswith('|'):
                i += 1
                table_rows.append(lines[i])
            if len(table_rows) >= 2:  # 需要表头和数据行
                paragraphs.append(('table', table_rows))
        
        # 无序列表
        elif re.match(r'^[\-\*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^[\-\*]\s+', lines[i]):
                item_text = re.sub(r'^[\-\*]\s+', '', lines[i])
                items.append(item_text)
                i += 1
            paragraphs.append(('ul', items))
            continue  # 跳过 i += 1
        
        # 有序列表
        elif re.match(r'^\d+\.\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                item_text = re.sub(r'^\d+\.\s+', '', lines[i])
                items.append(item_text)
                i += 1
            paragraphs.append(('ol', items))
            continue
        
        # 引用块
        elif line.startswith('> '):
            quotes = []
            while i < len(lines) and lines[i].startswith('> '):
                quotes.append(lines[i][2:].strip())
                i += 1
            paragraphs.append(('quote', '\n'.join(quotes)))
            continue
        
        # 代码块
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            paragraphs.append(('code', '\n'.join(code_lines)))
        
        # 普通文本
        elif line.strip():
            # 处理行内样式 **bold**
            text = line
            paragraphs.append(('p', text))
        
        i += 1
    
    return paragraphs


def generate_pdf_from_markdown(markdown_content: str, output_path: str, final_report: dict = None) -> bool:
    """
    从Markdown内容生成PDF
    
    Args:
        markdown_content: Markdown字符串
        output_path: 输出PDF文件路径
        final_report: 可选的最终报告数据（包含分数等）
        
    Returns:
        bool: 是否成功
    """
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        
        # 注册中文字体
        font_path = '/app/LXGWWenKai-Regular.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('LXGWWenKai', font_path))
            pdfmetrics.registerFont(TTFont('LXGWWenKai-Bold', font_path))
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
        styles = {}
        
        styles['h1'] = ParagraphStyle(
            'H1',
            fontName='LXGWWenKai-Bold',
            fontSize=20,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#1a1a1a'),
            leading=24,
        )
        
        styles['h2'] = ParagraphStyle(
            'H2',
            fontName='LXGWWenKai-Bold',
            fontSize=16,
            spaceBefore=16,
            spaceAfter=10,
            textColor=colors.HexColor('#1e40af'),
            leading=20,
        )
        
        styles['h3'] = ParagraphStyle(
            'H3',
            fontName='LXGWWenKai-Bold',
            fontSize=13,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor('#374151'),
            leading=16,
        )
        
        styles['h4'] = ParagraphStyle(
            'H4',
            fontName='LXGWWenKai-Bold',
            fontSize=11,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor('#4b5563'),
            leading=14,
        )
        
        styles['p'] = ParagraphStyle(
            'P',
            fontName='LXGWWenKai',
            fontSize=10,
            leading=15,
            spaceBefore=4,
            spaceAfter=4,
        )
        
        styles['bold_p'] = ParagraphStyle(
            'BoldP',
            fontName='LXGWWenKai-Bold',
            fontSize=10,
            leading=15,
            spaceBefore=4,
            spaceAfter=4,
        )
        
        styles['small'] = ParagraphStyle(
            'Small',
            fontName='LXGWWenKai',
            fontSize=9,
            leading=13,
            spaceBefore=2,
            spaceAfter=2,
            textColor=colors.HexColor('#666666'),
        )
        
        styles['table_header'] = ParagraphStyle(
            'TableHeader',
            fontName='LXGWWenKai-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.white,
        )
        
        styles['table_cell'] = ParagraphStyle(
            'TableCell',
            fontName='LXGWWenKai',
            fontSize=8,
            leading=11,
        )
        
        styles['quote'] = ParagraphStyle(
            'Quote',
            fontName='LXGWWenKai',
            fontSize=10,
            leading=14,
            leftIndent=20,
            rightIndent=20,
            textColor=colors.HexColor('#666666'),
            borderColor=colors.HexColor('#cccccc'),
            borderWidth=0,
            borderPadding=5,
        )
        
        styles['code'] = ParagraphStyle(
            'Code',
            fontName='LXGWWenKai',
            fontSize=9,
            leading=13,
            backColor=colors.HexColor('#f5f5f5'),
        )
        
        styles['li'] = ParagraphStyle(
            'LI',
            fontName='LXGWWenKai',
            fontSize=10,
            leading=14,
            leftIndent=20,
            bulletIndent=10,
        )
        
        # 故事元素
        story = []
        
        # ===== Part 0: 最终报告（评分）=====
        if final_report:
            # 综合评分
            score = final_report.get('score', 0)
            story.append(Paragraph('📋 评审报告', styles['h1']))
            story.append(Spacer(1, 10))
            
            # 评分展示
            story.append(Paragraph(f'综合评分：{score} 分', styles['h2']))
            story.append(Spacer(1, 10))
            
            # 各维度评分
            if 'dimensions' in final_report:
                story.append(Paragraph('各维度评分', styles['h3']))
                for dim in final_report['dimensions']:
                    dim_name = dim.get('name', '')
                    dim_score = dim.get('score', 0)
                    dim_comment = dim.get('comment', '')
                    story.append(Paragraph(
                        f'• {dim_name}：{dim_score}分 - {dim_comment}',
                        styles['li']
                    ))
            
            # 优点
            if 'pros' in final_report and final_report['pros']:
                story.append(Spacer(1, 10))
                story.append(Paragraph('优点', styles['h3']))
                for pro in final_report['pros']:
                    story.append(Paragraph(f'✓ {pro}', styles['li']))
            
            # 问题
            if 'cons' in final_report and final_report['cons']:
                story.append(Spacer(1, 10))
                story.append(Paragraph('主要问题', styles['h3']))
                for con in final_report['cons']:
                    story.append(Paragraph(f'• {con}', styles['li']))
            
            # 修改建议
            if 'suggestions' in final_report:
                suggestions = final_report['suggestions']
                if suggestions.get('must'):
                    story.append(Spacer(1, 10))
                    story.append(Paragraph('必须修改', styles['h3']))
                    for s in suggestions['must']:
                        story.append(Paragraph(f'• {s}', styles['li']))
                if suggestions.get('should'):
                    story.append(Spacer(1, 10))
                    story.append(Paragraph('建议修改', styles['h3']))
                    for s in suggestions['should']:
                        story.append(Paragraph(f'• {s}', styles['li']))
            
            story.append(Spacer(1, 20))
        
        # ===== Part 1: 完整辩论记录 =====
        # 解析Markdown，分两部分处理
        clean_content = clean_article_content(markdown_content)
        paragraphs = parse_markdown_to_paragraphs(clean_content)
        
        # 跳过文章内容部分（代码块）
        filtered_paragraphs = []
        skip_article = False
        in_summary = False  # 标记是否进入总结报告部分
        debate_paragraphs = []  # 辩论记录部分
        summary_paragraphs = []  # 总结报告部分
        
        for p_type, content in paragraphs:
            # 检测总结报告开始
            if p_type == 'h1' and '📊 文章评审总结' in str(content):
                in_summary = True
                continue
            # 跳过文章原文部分
            if p_type == 'h2' and '文章原文' in str(content):
                skip_article = True
                continue
            if p_type == 'h2' and skip_article:
                skip_article = False
                continue
            if skip_article and p_type == 'code':
                continue
            # 跳过分隔线后的表格行
            if p_type == 'table':
                continue
            
            if in_summary:
                summary_paragraphs.append((p_type, content))
            else:
                debate_paragraphs.append((p_type, content))
        
        # 添加辩论记录部分
        for p_type, content in debate_paragraphs:
            if p_type == 'h1':
                story.append(Paragraph(content, styles['h1']))
            elif p_type == 'h2':
                story.append(Paragraph(content, styles['h2']))
            elif p_type == 'h3':
                story.append(Paragraph(content, styles['h3']))
            elif p_type == 'h4':
                story.append(Paragraph(content, styles['h4']))
            elif p_type == 'p':
                # 处理 **bold** 文本
                parts = re.split(r'\*\*(.+?)\*\*', content)
                if len(parts) > 1:
                    # 有粗体文本
                    text_parts = []
                    for idx, part in enumerate(parts):
                        if idx % 2 == 1:  # 粗体部分
                            text_parts.append(f"<b>{part}</b>")
                        elif part.strip():
                            text_parts.append(part)
                    story.append(Paragraph(''.join(text_parts), styles['p']))
                else:
                    story.append(Paragraph(content, styles['p']))
            elif p_type == 'table':
                # 解析表格
                table_data = []
                for row_idx, row in enumerate(content):
                    # 移除首尾 | 并分割
                    cells = [c.strip() for c in row.strip('|').split('|')]
                    # 跳过分隔行 (|---|---|)
                    if cells and not all(re.match(r'^-+$', c) for c in cells):
                        row_data = []
                        for cell in cells:
                            # 处理单元格内的粗体
                            cell_parts = re.split(r'\*\*(.+?)\*\*', cell)
                            if len(cell_parts) > 1:
                                cell_texts = []
                                for idx, part in enumerate(cell_parts):
                                    if idx % 2 == 1:
                                        cell_texts.append(f"<b>{part}</b>")
                                    elif part.strip():
                                        cell_texts.append(part)
                                row_data.append(''.join(cell_texts))
                            else:
                                row_data.append(cell)
                        table_data.append(row_data)
                
                if len(table_data) >= 2:
                    # 创建表格
                    col_count = len(table_data[0])
                    table = Table(table_data, colWidths=[None] * col_count)
                    
                    # 设置样式
                    style_commands = [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'LXGWWenKai-Bold'),
                        ('FONTNAME', (0, 1), (-1, -1), 'LXGWWenKai'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]
                    table.setStyle(TableStyle(style_commands))
                    story.append(table)
                    story.append(Spacer(1, 10))
            elif p_type == 'ul':
                for item in content:
                    # 处理粗体
                    item_parts = re.split(r'\*\*(.+?)\*\*', item)
                    if len(item_parts) > 1:
                        text_parts = []
                        for idx, part in enumerate(item_parts):
                            if idx % 2 == 1:
                                text_parts.append(f"<b>{part}</b>")
                            elif part.strip():
                                text_parts.append(part)
                        story.append(Paragraph('• ' + ''.join(text_parts), styles['li']))
                    else:
                        story.append(Paragraph('• ' + item, styles['li']))
            elif p_type == 'ol':
                for idx, item in enumerate(content, 1):
                    # 处理粗体
                    item_parts = re.split(r'\*\*(.+?)\*\*', item)
                    if len(item_parts) > 1:
                        text_parts = []
                        for idx2, part in enumerate(item_parts):
                            if idx2 % 2 == 1:
                                text_parts.append(f"<b>{part}</b>")
                            elif part.strip():
                                text_parts.append(part)
                        story.append(Paragraph(f'{idx}. ' + ''.join(text_parts), styles['li']))
                    else:
                        story.append(Paragraph(f'{idx}. ' + item, styles['li']))
            elif p_type == 'quote':
                story.append(Paragraph(content, styles['quote']))
            elif p_type == 'code':
                for line in content.split('\n'):
                    story.append(Paragraph(line, styles['code']))
        
        # ===== Part 2: 文章评审总结 =====
        if summary_paragraphs:
            story.append(Spacer(1, 20))
            story.append(PageBreak())
            for p_type, content in summary_paragraphs:
                if p_type == 'h1':
                    story.append(Paragraph(content, styles['h1']))
                elif p_type == 'h2':
                    story.append(Paragraph(content, styles['h2']))
                elif p_type == 'h3':
                    story.append(Paragraph(content, styles['h3']))
                elif p_type == 'h4':
                    story.append(Paragraph(content, styles['h4']))
                elif p_type == 'p':
                    parts = re.split(r'\*\*(.+?)\*\*', content)
                    if len(parts) > 1:
                        text_parts = []
                        for idx, part in enumerate(parts):
                            if idx % 2 == 1:
                                text_parts.append(f"<b>{part}</b>")
                            elif part.strip():
                                text_parts.append(part)
                        story.append(Paragraph(''.join(text_parts), styles['p']))
                    else:
                        story.append(Paragraph(content, styles['p']))
                elif p_type == 'ul':
                    for item in content:
                        story.append(Paragraph('• ' + item, styles['li']))
                elif p_type == 'ol':
                    for idx, item in enumerate(content, 1):
                        story.append(Paragraph(f'{idx}. ' + item, styles['li']))
                elif p_type == 'quote':
                    story.append(Paragraph(content, styles['quote']))
        
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
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_pdf_from_html(html_content: str, output_path: str) -> bool:
    """
    从HTML内容生成PDF（兼容性函数）
    """
    # 先将HTML转换为Markdown
    try:
        from html2text import HTML2Text
        h2t = HTML2Text()
        h2t.body_width = 0  # 不换行
        md = h2t.handle(html_content)
        return generate_pdf_from_markdown(md, output_path)
    except ImportError:
        # 如果没有html2text，直接从HTML提取纯文本
        text = re.sub(r'<[^>]+>', '', html_content)
        return generate_pdf_from_markdown(text, output_path)


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
    created_at = project_data.get('created_at', project_data.get('createdAt', ''))
    
    # 格式化创建时间
    if created_at and created_at != 'N/A':
        try:
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
        body {{
            font-family: "Droid Sans Fallback", "Noto Sans CJK SC", sans-serif;
            font-size: 11pt;
            line-height: 1.8;
            color: #333;
            padding: 2cm;
        }}
        h1 {{ font-size: 22pt; text-align: center; color: #1a1a1a; margin-bottom: 20pt; }}
        h2 {{ font-size: 14pt; color: #1e40af; margin-top: 20pt; margin-bottom: 10pt; }}
        h3 {{ font-size: 12pt; color: #374151; margin-top: 15pt; margin-bottom: 8pt; }}
        .meta {{ text-align: center; color: #666; font-size: 10pt; margin-bottom: 20pt; }}
        .article-content {{ background: #f9fafb; padding: 15pt; border-radius: 6pt; margin-bottom: 20pt; white-space: pre-wrap; font-size: 10pt; }}
        .critic-content, .defender-content {{ background: #f9fafb; padding: 10pt; margin: 8pt 0; border-radius: 4pt; border-left: 3pt solid #6b7280; font-size: 9pt; }}
        .critic-content {{ border-left-color: #ef4444; }}
        .defender-content {{ border-left-color: #22c55e; }}
        .footer {{ text-align: center; color: #999; font-size: 9pt; margin-top: 30pt; border-top: 1pt solid #e5e7eb; padding-top: 10pt; }}
    </style>
</head>
<body>
    <h1>📊 AI Readers 辩论评审报告</h1>
    <div class="meta">
        <p><strong>项目名称：</strong>{project_data.get('title', '未命名')}</p>
        <p><strong>创建时间：</strong>{created_at or 'N/A'}</p>
        <p><strong>辩论配置：</strong>{config.get('rounds', 1)}轮 | {len(config.get('critics', []))}位批评者 | {len(config.get('defenders', []))}位辩护者</p>
    </div>
"""
    ]
    
    # 文章内容
    html_parts.append(f"""
    <h2>📝 文章内容</h2>
    <div class="article-content">{article[:2000]}{'...' if len(article) > 2000 else ''}</div>
""")
    
    # 辩论过程
    if rounds:
        html_parts.append("""
    <h2>🔄 辩论过程</h2>
""")
        for round_data in rounds:
            round_num = round_data.get('round_num', round_data.get('roundNum', 1))
            html_parts.append(f"""
    <h3>第 {round_num} 轮</h3>
""")
            
            # 批评者
            critics = round_data.get('critics', {})
            if critics:
                html_parts.append("<h4>👥 批评者观点</h4>")
                if isinstance(critics, dict):
                    for name, content in critics.items():
                        html_parts.append(f"""
    <div class="critic-content">
        <div><strong>🔴 {name}</strong></div>
        <div>{content}</div>
    </div>
""")
                elif isinstance(critics, list):
                    for critic in critics:
                        if isinstance(critic, dict):
                            name = critic.get('name', '批评者')
                            content = critic.get('content', '')
                            html_parts.append(f"""
    <div class="critic-content">
        <div><strong>🔴 {name}</strong></div>
        <div>{content}</div>
    </div>
""")
            
            # 辩护者
            defenders = round_data.get('defenders', {})
            if defenders:
                html_parts.append("<h4>👥 辩护者观点</h4>")
                if isinstance(defenders, dict):
                    for name, content in defenders.items():
                        html_parts.append(f"""
    <div class="defender-content">
        <div><strong>🟢 {name}</strong></div>
        <div>{content}</div>
    </div>
""")
                elif isinstance(defenders, list):
                    for defender in defenders:
                        if isinstance(defender, dict):
                            name = defender.get('name', '辩护者')
                            content = defender.get('content', '')
                            html_parts.append(f"""
    <div class="defender-content">
        <div><strong>🟢 {name}</strong></div>
        <div>{content}</div>
    </div>
""")
    
    html_parts.append("""
    <div class="footer">
        <p>本报告由 AI Readers 自动生成</p>
    </div>
</body>
</html>
""")
    
    return ''.join(html_parts)
