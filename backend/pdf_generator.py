"""PDF生成工具 - 使用Playwright支持中文"""

import os
from pathlib import Path


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
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # 启动chromium浏览器
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 创建新的浏览器上下文和页面
            context = browser.new_context(
                viewport={'width': 794, 'height': 1123},  # A4 size in pixels at 96 DPI
            )
            page = context.new_page()
            
            # 设置HTML内容
            page.set_content(html_content, wait_until='networkidle')
            
            # 生成PDF
            page.pdf(
                path=output_path,
                format='A4',
                print_background=True,
                margin={'top': '2cm', 'bottom': '2cm', 'left': '2cm', 'right': '2cm'}
            )
            
            # 关闭
            context.close()
            browser.close()
            
        return True
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
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
            white-space: pre-wrap;
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
        <p><strong>创建时间：</strong>{project_data.get('created_at', 'N/A')}</p>
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
            round_num = round_data.get('round_num', 1)
            html_parts.append(f"""
    <div class="round-section">
        <h3>第 {round_num} 轮</h3>
""")
            
            # 批评者
            critics = round_data.get('critics', [])
            if critics:
                html_parts.append("<h4>👥 批评者观点</h4>")
                for critic in critics:
                    html_parts.append(f"""
        <div class="critic-content">
            <div class="agent-name">🔴 {critic.get('name', '批评者')}</div>
            <div>{critic.get('content', '')}</div>
        </div>
""")
            
            # 辩护者
            defenders = round_data.get('defenders', [])
            if defenders:
                html_parts.append("<h4>👥 辩护者观点</h4>")
                for defender in defenders:
                    html_parts.append(f"""
        <div class="defender-content">
            <div class="agent-name">🟢 {defender.get('name', '辩护者')}</div>
            <div>{defender.get('content', '')}</div>
        </div>
""")
            
            html_parts.append("    </div>")
    
    # 页脚
    html_parts.append(f"""
    <div class="footer">
        <p>本报告由 AI Readers 自动生成 | {project_data.get('created_at', '')}</p>
    </div>
</body>
</html>
""")
    
    return ''.join(html_parts)
