"""
重新设计的 PDF 生成器
结构：
1. 完整辩论记录
2. 文章评审总结
3. 评审报告（评分）
"""

import re
import os


def parse_markdown_to_paragraphs(content: str):
    """解析 Markdown 为段落列表"""
    paragraphs = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
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
            if len(table_rows) >= 2:
                paragraphs.append(('table', table_rows))
        # 无序列表
        elif re.match(r'^[\-\*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^[\-\*]\s+', lines[i]):
                item_text = re.sub(r'^[\-\*]\s+', '', lines[i])
                items.append(item_text)
                i += 1
            paragraphs.append(('ul', items))
            continue
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
        # 分隔线
        elif re.match(r'^---+\s*$', line):
            paragraphs.append(('hr', '---'))
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
            paragraphs.append(('p', line))
        
        i += 1
    
    return paragraphs


def generate_pdf_redesigned(markdown_content: str, output_path: str, final_report: dict = None) -> bool:
    """重新设计的 PDF 生成"""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, 
                                         Table, TableStyle, PageBreak, HRFlowable)
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        
        # 注册字体
        font_path = '/app/LXGWWenKai-Regular.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('LXGWWenKai', font_path))
            # 注册粗体（使用同一字体文件）
            pdfmetrics.registerFont(TTFont('LXGWWenKai-Bold', font_path))
            pdfmetrics.registerFont(TTFont('LXGWWenKai-Oblique', font_path))
        else:
            # 尝试本地路径（开发环境）
            local_font = '/home/rz1998/workspace/ai-readers/backend/LXGWWenKai-Regular.ttf'
            if os.path.exists(local_font):
                pdfmetrics.registerFont(TTFont('LXGWWenKai', local_font))
                pdfmetrics.registerFont(TTFont('LXGWWenKai-Bold', local_font))
                pdfmetrics.registerFont(TTFont('LXGWWenKai-Oblique', local_font))
            else:
                print(f"Font not found: {font_path}")
                return False
        
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
        
        styles['h1'] = ParagraphStyle('H1', fontName='LXGWWenKai-Bold', fontSize=18, leading=24, spaceAfter=12, textColor=colors.HexColor('#1a1a2e'))
        styles['h2'] = ParagraphStyle('H2', fontName='LXGWWenKai-Bold', fontSize=14, leading=20, spaceAfter=10, spaceBefore=16, textColor=colors.HexColor('#16213e'))
        styles['h3'] = ParagraphStyle('H3', fontName='LXGWWenKai-Bold', fontSize=12, leading=16, spaceAfter=8, spaceBefore=12, textColor=colors.HexColor('#0f3460'))
        styles['h4'] = ParagraphStyle('H4', fontName='LXGWWenKai-Bold', fontSize=11, leading=14, spaceAfter=6, spaceBefore=8, textColor=colors.HexColor('#333333'))
        styles['p'] = ParagraphStyle('P', fontName='LXGWWenKai', fontSize=10, leading=15, spaceAfter=6)
        styles['li'] = ParagraphStyle('LI', fontName='LXGWWenKai', fontSize=10, leading=14, leftIndent=16, spaceAfter=4)
        styles['quote'] = ParagraphStyle('Quote', fontName='LXGWWenKai-Oblique', fontSize=10, leading=14, leftIndent=20, textColor=colors.HexColor('#555555'))
        styles['code'] = ParagraphStyle('Code', fontName='Courier', fontSize=8, leading=12, backColor=colors.HexColor('#f5f5f5'))
        styles['small'] = ParagraphStyle('Small', fontName='LXGWWenKai', fontSize=8, leading=12, textColor=colors.grey)
        
        # 配色
        PRIMARY_BLUE = colors.HexColor('#3b82f6')
        DARK_BLUE = colors.HexColor('#1e3a5f')
        LIGHT_BG = colors.HexColor('#f8fafc')
        
        story = []
        
        # ===== 清理和解析内容 =====
        content = markdown_content.strip()
        paragraphs = parse_markdown_to_paragraphs(content)
        
        # 分类内容
        skip_article = False
        skip_summary = False
        
        # 标记各部分起始位置
        debate_start = 0
        summary_start = None
        score_start = None
        
        for idx, (p_type, p_content) in enumerate(paragraphs):
            # 检测文章评审总结开始
            if p_type == 'h1' and ('📊' in p_content or '评审总结' in p_content or '文章评审' in p_content):
                summary_start = idx
                break
        
        # 辩论记录部分（跳过已有的第一标题，避免重复）
        debate_paragraphs = paragraphs[:summary_start] if summary_start else paragraphs
        
        # 跳过第一个 H1 标题（避免与我们的页眉重复）
        if debate_paragraphs and debate_paragraphs[0][0] == 'h1':
            debate_paragraphs = debate_paragraphs[1:]
        
        # ===== Part 1: 完整辩论记录 =====
        story.append(PageBreak())
        story.append(Paragraph("📚 完整辩论记录", styles['h1']))
        story.append(Spacer(1, 8))
        
        # 添加分隔线
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_BLUE, spaceAfter=12))
        
        # 添加辩论记录内容
        for p_type, p_content in debate_paragraphs:
            if p_type == 'h1':
                story.append(Paragraph(p_content, styles['h1']))
            elif p_type == 'h2':
                story.append(Paragraph(p_content, styles['h2']))
            elif p_type == 'h3':
                story.append(Paragraph(p_content, styles['h3']))
            elif p_type == 'h4':
                story.append(Paragraph(p_content, styles['h4']))
            elif p_type == 'p':
                # 处理粗体
                parts = re.split(r'\*\*(.+?)\*\*', p_content)
                if len(parts) > 1:
                    text_parts = []
                    for i2, part in enumerate(parts):
                        if i2 % 2 == 1:
                            text_parts.append(f"<b>{part}</b>")
                        elif part.strip():
                            text_parts.append(part)
                    story.append(Paragraph(''.join(text_parts), styles['p']))
                else:
                    story.append(Paragraph(p_content, styles['p']))
            elif p_type == 'ul':
                for item in p_content:
                    story.append(Paragraph(f"• {item}", styles['li']))
            elif p_type == 'ol':
                for i2, item in enumerate(p_content, 1):
                    story.append(Paragraph(f"{i2}. {item}", styles['li']))
            elif p_type == 'quote':
                story.append(Paragraph(p_content, styles['quote']))
        
        # ===== Part 2: 文章评审总结 =====
        if summary_start:
            story.append(PageBreak())
            story.append(Paragraph("📋 文章评审总结", styles['h1']))
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_BLUE, spaceAfter=12))
            
            summary_paragraphs = paragraphs[summary_start:]
            for p_type, p_content in summary_paragraphs:
                if p_type == 'h1':
                    story.append(Paragraph(p_content, styles['h1']))
                elif p_type == 'h2':
                    story.append(Paragraph(p_content, styles['h2']))
                elif p_type == 'h3':
                    story.append(Paragraph(p_content, styles['h3']))
                elif p_type == 'h4':
                    story.append(Paragraph(p_content, styles['h4']))
                elif p_type == 'p':
                    parts = re.split(r'\*\*(.+?)\*\*', p_content)
                    if len(parts) > 1:
                        text_parts = []
                        for i2, part in enumerate(parts):
                            if i2 % 2 == 1:
                                text_parts.append(f"<b>{part}</b>")
                            elif part.strip():
                                text_parts.append(part)
                        story.append(Paragraph(''.join(text_parts), styles['p']))
                    else:
                        story.append(Paragraph(p_content, styles['p']))
                elif p_type == 'ul':
                    for item in p_content:
                        story.append(Paragraph(f"• {item}", styles['li']))
                elif p_type == 'ol':
                    for i2, item in enumerate(p_content, 1):
                        story.append(Paragraph(f"{i2}. {item}", styles['li']))
                elif p_type == 'table':
                    # 解析表格
                    table_data = []
                    for row in p_content:
                        cells = [c.strip() for c in row.strip('|').split('|')]
                        if cells and not all(re.match(r'^-+$', c) for c in cells):
                            table_data.append(cells)
                    
                    if len(table_data) >= 2:
                        col_count = len(table_data[0])
                        t = Table(table_data, colWidths=[None] * col_count)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('FONTNAME', (0, 0), (-1, 0), 'LXGWWenKai-Bold'),
                            ('FONTNAME', (0, 1), (-1, -1), 'LXGWWenKai'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 10))
        
        # ===== Part 3: 评审报告（评分）=====
        if final_report:
            story.append(PageBreak())
            story.append(Paragraph("📊 评审报告", styles['h1']))
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_BLUE, spaceAfter=16))
            
            # 综合评分
            score = final_report.get('score', 0)
            story.append(Paragraph(f"综合评分：<b>{score}</b> 分", styles['h2']))
            story.append(Spacer(1, 12))
            
            # 各维度评分条
            if 'dimensions' in final_report:
                story.append(Paragraph("各维度评分", styles['h3']))
                for dim in final_report['dimensions']:
                    dim_name = dim.get('name', '')
                    dim_score = dim.get('score', 0)
                    dim_comment = dim.get('comment', '')
                    
                    # 创建评分条
                    bar_text = f"{dim_name}：{dim_score}分"
                    bar_percent = dim_score
                    
                    # 简单文本评分条
                    story.append(Paragraph(bar_text, styles['p']))
                    story.append(Spacer(1, 4))
            
            story.append(Spacer(1, 12))
            
            # 优点
            if 'pros' in final_report and final_report['pros']:
                story.append(Paragraph("✅ 优点", styles['h3']))
                for pro in final_report['pros']:
                    story.append(Paragraph(f"✓ {pro}", styles['li']))
                story.append(Spacer(1, 8))
            
            # 问题
            if 'cons' in final_report and final_report['cons']:
                story.append(Paragraph("⚠️ 主要问题", styles['h3']))
                for con in final_report['cons']:
                    story.append(Paragraph(f"• {con}", styles['li']))
                story.append(Spacer(1, 8))
            
            # 修改建议
            if 'suggestions' in final_report:
                suggestions = final_report['suggestions']
                if suggestions.get('must'):
                    story.append(Paragraph("🔴 必须修改", styles['h3']))
                    for s in suggestions['must']:
                        story.append(Paragraph(f"• {s}", styles['li']))
                    story.append(Spacer(1, 6))
                if suggestions.get('should'):
                    story.append(Paragraph("🟡 建议修改", styles['h3']))
                    for s in suggestions['should']:
                        story.append(Paragraph(f"• {s}", styles['li']))
        
        # 页脚
        story.append(Spacer(1, 30))
        story.append(Paragraph("本报告由 AI Readers 自动生成", styles['small']))
        
        # 生成 PDF
        doc.build(story)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试
    import sys
    if len(sys.argv) > 2:
        md_file = sys.argv[1]
        output_file = sys.argv[2]
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        success = generate_pdf_redesigned(md_content, output_file, {'score': 75, 'dimensions': [{'name': '结构', 'score': 72, 'comment': 'ok'}]})
        print(f"Success: {success}")
