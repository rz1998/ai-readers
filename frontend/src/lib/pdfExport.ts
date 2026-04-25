import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import type { Project, FinalReport } from '@/types';

/**
 * 导出辩论报告为PDF（使用html2canvas确保中文正常显示）
 */
export async function exportReportToPDF(project: Project): Promise<void> {
  // 创建临时HTML容器
  const container = document.createElement('div');
  container.style.cssText = 'position: absolute; left: -9999px; top: 0; width: 800px; background: white; padding: 40px; font-family: "Microsoft YaHei", "PingFang SC", sans-serif;';
  container.innerHTML = generateHTMLReport(project);
  document.body.appendChild(container);
  
  try {
    // 使用html2canvas将HTML转为图片
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
    });
    
    // 创建PDF
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    
    // 计算图片尺寸以适应页面
    const imgWidth = pageWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    
    // 添加图片到PDF，多页面处理
    let heightLeft = imgHeight;
    let position = 0;
    const imgData = canvas.toDataURL('image/png');
    
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;
    
    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }
    
    // 保存PDF
    const filename = `辩论报告_${project.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}_${Date.now()}.pdf`;
    pdf.save(filename);
  } finally {
    // 清理临时容器
    document.body.removeChild(container);
  }
}

/**
 * 导出辩论报告为PDF（旧版本，直接使用jsPDF，中文会乱码，保留备用）
 */
async function exportReportToPDFLegacy(project: Project): Promise<void> {
  // 创建PDF
  const pdf = new jsPDF('p', 'mm', 'a4');
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 15;
  let yPos = margin;

  // 标题
  pdf.setFontSize(20);
  pdf.setFont('helvetica', 'bold');
  pdf.text('AI Readers 辩论评审报告', pageWidth / 2, yPos, { align: 'center' });
  yPos += 12;

  // 项目信息
  pdf.setFontSize(10);
  pdf.setFont('helvetica', 'normal');
  pdf.setTextColor(100);
  pdf.text(`项目：${project.title}`, margin, yPos);
  yPos += 5;
  pdf.text(`创建时间：${new Date(project.createdAt).toLocaleString('zh-CN')}`, margin, yPos);
  yPos += 5;
  pdf.text(`辩论配置：${project.config.rounds}轮 | ${project.config.critics.length}批评者 | ${project.config.defenders.length}辩护者`, margin, yPos);
  yPos += 10;

  // 分隔线
  pdf.setDrawColor(200);
  pdf.line(margin, yPos, pageWidth - margin, yPos);
  yPos += 10;

  // 文章内容
  pdf.setFontSize(14);
  pdf.setFont('helvetica', 'bold');
  pdf.setTextColor(0);
  pdf.text('文章内容', margin, yPos);
  yPos += 7;

  pdf.setFontSize(9);
  pdf.setFont('helvetica', 'normal');
  const articleLines = pdf.splitTextToSize(project.article.substring(0, 1000) + (project.article.length > 1000 ? '...' : ''), pageWidth - 2 * margin);
  pdf.text(articleLines, margin, yPos);
  yPos += articleLines.length * 4 + 10;

  // 如果有最终报告
  if (project.finalReport) {
    const report = project.finalReport;

    // 检查是否需要分页
    if (yPos > pageHeight - 60) {
      pdf.addPage();
      yPos = margin;
    }

    // 综合评分
    pdf.setFontSize(16);
    pdf.setFont('helvetica', 'bold');
    pdf.text('综合评分', margin, yPos);
    yPos += 8;

    pdf.setFontSize(36);
    pdf.text(`${report.score}`, margin, yPos);
    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'normal');
    pdf.text('分', margin + 25, yPos);
    yPos += 15;

    // 雷达图维度评分
    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'bold');
    pdf.text('各维度评分', margin, yPos);
    yPos += 8;

    pdf.setFontSize(9);
    pdf.setFont('helvetica', 'normal');
    report.dimensions.forEach((dim) => {
      if (yPos > pageHeight - 20) {
        pdf.addPage();
        yPos = margin;
      }
      pdf.text(`${dim.name}：${dim.score}/10`, margin, yPos);
      yPos += 5;
    });
    yPos += 5;

    // 优点
    if (yPos > pageHeight - 40) {
      pdf.addPage();
      yPos = margin;
    }
    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'bold');
    pdf.text('核心优点', margin, yPos);
    yPos += 6;
    pdf.setFontSize(9);
    pdf.setFont('helvetica', 'normal');
    report.pros.slice(0, 3).forEach((pro, i) => {
      const lines = pdf.splitTextToSize(`${i + 1}. ${pro}`, pageWidth - 2 * margin);
      lines.forEach((line: string) => {
        if (yPos > pageHeight - 10) {
          pdf.addPage();
          yPos = margin;
        }
        pdf.text(line, margin, yPos);
        yPos += 4;
      });
    });
    yPos += 5;

    // 问题
    if (yPos > pageHeight - 40) {
      pdf.addPage();
      yPos = margin;
    }
    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'bold');
    pdf.text('主要问题', margin, yPos);
    yPos += 6;
    pdf.setFontSize(9);
    pdf.setFont('helvetica', 'normal');
    report.cons.slice(0, 3).forEach((con, i) => {
      const lines = pdf.splitTextToSize(`${i + 1}. ${con}`, pageWidth - 2 * margin);
      lines.forEach((line: string) => {
        if (yPos > pageHeight - 10) {
          pdf.addPage();
          yPos = margin;
        }
        pdf.text(line, margin, yPos);
        yPos += 4;
      });
    });
    yPos += 5;

    // 修改建议
    if (report.suggestions.must.length > 0) {
      if (yPos > pageHeight - 30) {
        pdf.addPage();
        yPos = margin;
      }
      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'bold');
      pdf.text('修改建议（必须）', margin, yPos);
      yPos += 6;
      pdf.setFontSize(9);
      pdf.setFont('helvetica', 'normal');
      report.suggestions.must.forEach((s, i) => {
        const lines = pdf.splitTextToSize(`${i + 1}. ${s}`, pageWidth - 2 * margin);
        lines.forEach((line: string) => {
          if (yPos > pageHeight - 10) {
            pdf.addPage();
            yPos = margin;
          }
          pdf.text(line, margin, yPos);
          yPos += 4;
        });
      });
    }
  }

  // 辩论过程（简略版）
  if (yPos > pageHeight - 30) {
    pdf.addPage();
    yPos = margin;
  }
  pdf.addPage();
  yPos = margin;

  pdf.setFontSize(14);
  pdf.setFont('helvetica', 'bold');
  pdf.text('辩论过程', margin, yPos);
  yPos += 8;

  project.rounds.forEach((round) => {
    if (yPos > pageHeight - 40) {
      pdf.addPage();
      yPos = margin;
    }

    pdf.setFontSize(11);
    pdf.setFont('helvetica', 'bold');
    pdf.text(`Round ${round.roundNum}`, margin, yPos);
    yPos += 6;

    pdf.setFontSize(8);
    pdf.setFont('helvetica', 'normal');

    // 批评者观点（简略）
    round.critics.forEach((critic) => {
      const summary = critic.content.substring(0, 200) + (critic.content.length > 200 ? '...' : '');
      const lines = pdf.splitTextToSize(`【批评者 ${critic.name}】${summary}`, pageWidth - 2 * margin);
      lines.forEach((line: string) => {
        if (yPos > pageHeight - 10) {
          pdf.addPage();
          yPos = margin;
        }
        pdf.text(line, margin, yPos);
        yPos += 3;
      });
      yPos += 2;
    });

    // 辩护者观点（简略）
    round.defenders.forEach((defender) => {
      const summary = defender.content.substring(0, 200) + (defender.content.length > 200 ? '...' : '');
      const lines = pdf.splitTextToSize(`【辩护者 ${defender.name}】${summary}`, pageWidth - 2 * margin);
      lines.forEach((line: string) => {
        if (yPos > pageHeight - 10) {
          pdf.addPage();
          yPos = margin;
        }
        pdf.text(line, margin, yPos);
        yPos += 3;
      });
      yPos += 2;
    });

    yPos += 5;
  });

  // 保存PDF
  const filename = `辩论报告_${project.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}_${Date.now()}.pdf`;
  pdf.save(filename);
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
