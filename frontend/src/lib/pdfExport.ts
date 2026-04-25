import type { Project } from '@/types';

/**
 * 导出辩论报告为PDF
 * 使用后端API生成，确保中文正常显示
 */
export async function exportReportToPDF(project: Project): Promise<void> {
  try {
    // 调用后端API生成PDF
    const response = await fetch(`/api/projects/${project.id}/pdf`, {
      method: 'GET',
      headers: {
        'Accept': 'application/pdf',
      },
    });
    
    // 检查内容类型
    const contentType = response.headers.get('content-type') || '';
    
    if (contentType.includes('application/json')) {
      // 服务器返回了错误/降级响应，使用HTML下载
      const data = await response.json();
      if (data.html_content) {
        console.log('PDF generation unavailable, offering HTML download instead');
        // 下载HTML报告
        const blob = new Blob([data.html_content], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `辩论报告_${project.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}_${Date.now()}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        return;
      }
      throw new Error(data.message || 'PDF generation failed');
    }
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // 获取PDF blob
    const blob = await response.blob();
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `辩论报告_${project.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}_${Date.now()}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to export PDF:', error);
    // 备用方案：使用浏览器打印
    console.log('Falling back to browser print...');
    fallbackToPrint(project);
  }
}

/**
 * 备用方案：使用浏览器打印
 */
function fallbackToPrint(project: Project): void {
  const htmlContent = generateHTMLReport(project);
  
  const iframe = document.createElement('iframe');
  iframe.style.cssText = 'position: absolute; width: 800px; height: 600px; left: -9999px; top: 0; border: none;';
  document.body.appendChild(iframe);
  
  iframe.onload = () => {
    iframe.contentWindow?.print();
    setTimeout(() => {
      document.body.removeChild(iframe);
    }, 1000);
  };
  
  iframe.srcdoc = htmlContent;
}

/**
 * 导出完整HTML报告（包含样式）
 */
export async function exportFullReportHTML(project: Project): Promise<void> {
  const htmlContent = generateHTMLReport(project);
  const blob = new Blob([htmlContent], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `辩论报告_${project.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}_${Date.now()}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function generateHTMLReport(project: Project): string {
  const report = project.finalReport;

  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>辩论评审报告 - ${project.title}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 40px 20px; }
    h1 { font-size: 24px; text-align: center; margin-bottom: 20px; }
    h2 { font-size: 18px; margin: 30px 0 15px; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; }
    h3 { font-size: 14px; margin: 20px 0 10px; }
    .meta { text-align: center; color: #666; font-size: 12px; margin-bottom: 30px; }
    .article { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 30px; white-space: pre-wrap; }
    .score-section { text-align: center; margin: 30px 0; }
    .score { font-size: 72px; font-weight: bold; color: #3b82f6; }
    .score-label { color: #666; }
    .dimensions { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 20px 0; }
    .dimension { background: #f5f5f5; padding: 12px; border-radius: 6px; }
    .dimension-name { font-weight: 600; margin-bottom: 4px; }
    .dimension-score { color: #3b82f6; font-weight: bold; }
    .pros, .cons, .suggestions { margin: 15px 0; }
    .pro-item, .con-item { padding: 8px 0; border-bottom: 1px solid #eee; }
    .pro-item:before { content: '✓ '; color: green; }
    .con-item:before { content: '! '; color: orange; }
    .must { color: #dc2626; }
    .should { color: #ca8a04; }
    .optional { color: #2563eb; }
    .round { margin: 30px 0; padding: 20px; background: #fafafa; border-radius: 8px; }
    .agent { margin: 15px 0; padding: 12px; border-radius: 6px; }
    .critic { background: #fef2f2; border-left: 3px solid #ef4444; }
    .defender { background: #f0fdf4; border-left: 3px solid #22c55e; }
    .agent-name { font-weight: 600; margin-bottom: 8px; }
    .agent-content { font-size: 13px; white-space: pre-wrap; }
    .verdict { background: #eff6ff; padding: 12px; border-radius: 6px; margin: 10px 0; }
    .print-btn { display: inline-block; padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; margin: 20px 0; }
    @media print { .print-btn { display: none; } }
  </style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">🖨️ 打印 / 保存为PDF</button>

  <h1>📊 AI Readers 辩论评审报告</h1>
  <div class="meta">
    <p><strong>${project.title}</strong></p>
    <p>创建时间：${new Date(project.createdAt).toLocaleString('zh-CN')}</p>
    <p>${project.config.rounds}轮辩论 | ${project.config.critics.length}位批评者 | ${project.config.defenders.length}位辩护者</p>
  </div>

  <h2>📄 文章内容</h2>
  <div class="article">${project.article}</div>

  ${report ? `
  <h2>📝 最终评审报告</h2>

  <div class="score-section">
    <div class="score">${report.score}</div>
    <div class="score-label">综合评分 (满分100分)</div>
  </div>

  <h3>各维度评分</h3>
  <div class="dimensions">
    ${report.dimensions.map(d => `
      <div class="dimension">
        <div class="dimension-name">${d.name}</div>
        <div class="dimension-score">${d.score}/10</div>
        <div style="font-size:12px;color:#666">${d.comment}</div>
      </div>
    `).join('')}
  </div>

  <h3>✅ 核心优点</h3>
  <div class="pros">
    ${report.pros.map(p => `<div class="pro-item">${p}</div>`).join('')}
  </div>

  <h3>⚠️ 主要问题</h3>
  <div class="cons">
    ${report.cons.map(c => `<div class="con-item">${c}</div>`).join('')}
  </div>

  <h3>💡 修改建议</h3>
  ${report.suggestions.must.length > 0 ? `
    <div class="must"><strong>必须修改：</strong></div>
    <ul style="margin-left:20px">
      ${report.suggestions.must.map(s => `<li>${s}</li>`).join('')}
    </ul>
  ` : ''}
  ${report.suggestions.should.length > 0 ? `
    <div class="should" style="margin-top:10px"><strong>建议修改：</strong></div>
    <ul style="margin-left:20px">
      ${report.suggestions.should.map(s => `<li>${s}</li>`).join('')}
    </ul>
  ` : ''}
  ${report.suggestions.optional.length > 0 ? `
    <div class="optional" style="margin-top:10px"><strong>可选优化：</strong></div>
    <ul style="margin-left:20px">
      ${report.suggestions.optional.map(s => `<li>${s}</li>`).join('')}
    </ul>
  ` : ''}

  ${report.verdicts.length > 0 ? `
  <h3>⚖️ 裁决结果</h3>
  ${report.verdicts.map(v => `
    <div class="verdict">
      <strong>争议点：</strong>${v.issue}<br>
      <strong>批评者：</strong>${v.critic}<br>
      <strong>辩护者：</strong>${v.defender}<br>
      <strong>裁决：</strong>${v.ruling}
    </div>
  `).join('')}
  ` : ''}
  ` : ''}

  <h2>🔄 辩论过程</h2>
  ${project.rounds.map(round => `
    <div class="round">
      <h3>Round ${round.roundNum}</h3>

      ${round.critics.map(c => `
        <div class="agent critic">
          <div class="agent-name">🔴 批评者：${c.name} (${c.role})</div>
          <div class="agent-content">${c.content}</div>
        </div>
      `).join('')}

      ${round.defenders.map(d => `
        <div class="agent defender">
          <div class="agent-name">🟢 辩护者：${d.name} (${d.role})</div>
          <div class="agent-content">${d.content}</div>
        </div>
      `).join('')}
    </div>
  `).join('')}

  <div style="text-align:center;color:#999;font-size:12px;margin-top:40px">
    <p>本报告由 AI Readers 多Agent辩论系统生成</p>
    <p>生成时间：${new Date().toLocaleString('zh-CN')}</p>
  </div>
</body>
</html>
  `;
}
