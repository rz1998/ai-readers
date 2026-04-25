import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { projectApi } from '@/services/api';
import { useProjectStore } from '@/store/projectStore';
import { formatDate, cn, getScoreColor } from '@/lib/utils';
import {
  ArrowLeft,
  BookOpen,
  MessageSquare,
  Star,
  AlertTriangle,
  CheckCircle2,
  Lightbulb,
  Scale,
  ChevronDown,
  ChevronUp,
  Filter,
  X,
  User,
  Shield,
  Radar,
  Clock,
  Download,
  Trash2,
  RotateCcw,
  Play,
} from 'lucide-react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar as RechartsRadar,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import type { Project, AgentView, FilterRound, FilterAgent, FinalReport } from '@/types';
import { exportReportToPDF, exportFullReportHTML } from '@/lib/pdfExport';

function AgentCard({ agent, type }: { agent: AgentView; type: 'critic' | 'defender' }) {
  const [expanded, setExpanded] = useState(true);
  const isCritic = type === 'critic';

  return (
    <div
      className={cn(
        'rounded-xl border overflow-hidden',
        isCritic
          ? 'border-critic-500/30 bg-critic-500/5'
          : 'border-defender-500/30 bg-defender-500/5'
      )}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'w-full flex items-center justify-between p-4 text-left transition-colors',
          isCritic ? 'hover:bg-critic-500/10' : 'hover:bg-defender-500/10'
        )}
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'w-8 h-8 rounded-lg flex items-center justify-center',
              isCritic ? 'bg-critic-500/20' : 'bg-defender-500/20'
            )}
          >
            {isCritic ? (
              <AlertTriangle size={14} className="text-critic-400" />
            ) : (
              <Shield size={14} className="text-defender-400" />
            )}
          </div>
          <div>
            <p className="font-medium text-sm">{agent.name}</p>
            <p className="text-xs text-muted-foreground">{agent.role}</p>
          </div>
        </div>
        {expanded ? (
          <ChevronUp size={16} className="text-muted-foreground" />
        ) : (
          <ChevronDown size={16} className="text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-4">
          <div className="prose-content text-sm whitespace-pre-wrap">{agent.content}</div>
        </div>
      )}
    </div>
  );
}

function DebateRound({
  round,
  project,
  filterAgent,
}: {
  round: Project['rounds'][0];
  project: Project;
  filterAgent: FilterAgent;
}) {
  const filteredCritics =
    filterAgent === 'all'
      ? round.critics
      : round.critics.filter((c) => c.name === filterAgent || c.role === filterAgent);
  const filteredDefenders =
    filterAgent === 'all'
      ? round.defenders
      : round.defenders.filter((d) => d.name === filterAgent || d.role === filterAgent);

  return (
    <div className="space-y-4">
      {/* Round header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center">
          <span className="text-white font-bold text-sm">{round.roundNum}</span>
        </div>
        <div>
          <h3 className="font-semibold">第 {round.roundNum} 轮</h3>
          <p className="text-xs text-muted-foreground">
            {round.critics.length} 位批评者 · {round.defenders.length} 位辩护者
          </p>
        </div>
      </div>

      {/* Critics */}
      {filteredCritics.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-critic-400 text-sm font-medium">
            <AlertTriangle size={14} />
            <span>批评者观点</span>
          </div>
          {filteredCritics.map((critic) => (
            <AgentCard key={critic.name} agent={critic} type="critic" />
          ))}
        </div>
      )}

      {/* Defenders */}
      {filteredDefenders.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-defender-400 text-sm font-medium">
            <Shield size={14} />
            <span>辩护者观点</span>
          </div>
          {filteredDefenders.map((defender) => (
            <AgentCard key={defender.name} agent={defender} type="defender" />
          ))}
        </div>
      )}
    </div>
  );
}

function RadarChartSection({ dimensions }: { dimensions: FinalReport['dimensions'] }) {
  const data = dimensions.map((d) => ({
    subject: d.name,
    score: d.score,
    fullMark: 100,
  }));

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
          />
          <RechartsRadar
            name="评分"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.3}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            formatter={(value: number) => [`${value}分`, '评分']}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

function FinalReportSection({ report }: { report: FinalReport }) {
  return (
    <div className="space-y-6">
      {/* Score */}
      <div className="text-center py-6">
        <p className="text-sm text-muted-foreground mb-2">综合评分</p>
        <div className={cn('text-6xl font-bold', getScoreColor(report.score))}>
          {report.score}
        </div>
        <p className="text-xs text-muted-foreground mt-1">满分100分</p>
      </div>

      {/* Radar chart */}
      <RadarChartSection dimensions={report.dimensions} />

      {/* Dimensions detail */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {report.dimensions.map((dim) => (
          <div key={dim.name} className="glass-dark rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">{dim.name}</span>
              <span className={cn('text-sm font-bold', getScoreColor(dim.score))}>
                {dim.score}
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-1.5 mb-2">
              <div
                className={cn('h-full rounded-full transition-all', getScoreColor(dim.score).replace('text-', 'bg-'))}
                style={{ width: `${dim.score}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground">{dim.comment}</p>
          </div>
        ))}
      </div>

      {/* Pros */}
      <div className="glass-dark rounded-xl p-4">
        <div className="flex items-center gap-2 text-green-400 mb-3">
          <CheckCircle2 size={16} />
          <span className="font-medium text-sm">优点</span>
        </div>
        <ul className="space-y-2">
          {report.pros.map((pro, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="text-green-400 mt-0.5">✓</span>
              <span className="text-muted-foreground">{pro}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Cons */}
      <div className="glass-dark rounded-xl p-4">
        <div className="flex items-center gap-2 text-critic-400 mb-3">
          <AlertTriangle size={16} />
          <span className="font-medium text-sm">问题</span>
        </div>
        <ul className="space-y-2">
          {report.cons.map((con, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="text-critic-400 mt-0.5">!</span>
              <span className="text-muted-foreground">{con}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Suggestions */}
      <div className="glass-dark rounded-xl p-4">
        <div className="flex items-center gap-2 text-yellow-400 mb-4">
          <Lightbulb size={16} />
          <span className="font-medium text-sm">修改建议</span>
        </div>

        {report.suggestions.must.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-red-400 uppercase tracking-wide mb-2">必须修改</p>
            <ul className="space-y-1.5">
              {report.suggestions.must.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-red-400 font-bold">●</span>
                  <span className="text-muted-foreground">{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {report.suggestions.should.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-yellow-400 uppercase tracking-wide mb-2">建议修改</p>
            <ul className="space-y-1.5">
              {report.suggestions.should.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-yellow-400 font-bold">●</span>
                  <span className="text-muted-foreground">{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {report.suggestions.optional.length > 0 && (
          <div>
            <p className="text-xs font-medium text-blue-400 uppercase tracking-wide mb-2">可选优化</p>
            <ul className="space-y-1.5">
              {report.suggestions.optional.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-blue-400 font-bold">●</span>
                  <span className="text-muted-foreground">{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Verdicts */}
      {report.verdicts.length > 0 && (
        <div className="glass-dark rounded-xl p-4">
          <div className="flex items-center gap-2 text-brand-400 mb-4">
            <Scale size={16} />
            <span className="font-medium text-sm">裁决结果</span>
          </div>
          <div className="space-y-4">
            {report.verdicts.map((v, i) => (
              <div key={i} className="border-l-2 border-border pl-4">
                <p className="text-sm font-medium mb-2">{v.issue}</p>
                <div className="space-y-2 text-xs">
                  <p>
                    <span className="text-critic-400 font-medium">批评者：</span>
                    <span className="text-muted-foreground ml-1">{v.critic}</span>
                  </p>
                  <p>
                    <span className="text-defender-400 font-medium">辩护者：</span>
                    <span className="text-muted-foreground ml-1">{v.defender}</span>
                  </p>
                  <p className="mt-2 p-2 rounded bg-brand-500/10 border border-brand-500/20">
                    <span className="text-brand-400 font-medium">裁决：</span>
                    <span className="text-muted-foreground ml-1">{v.ruling}</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { currentProject, setCurrentProject, setLoading, loading, filterRound, filterAgent, setFilterRound, setFilterAgent } =
    useProjectStore();
  const [articleExpanded, setArticleExpanded] = useState(false);
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExportPDF = async () => {
    if (!currentProject) return;
    setIsExporting(true);
    setShowDownloadMenu(false);
    try {
      await exportReportToPDF(currentProject);
    } catch (err) {
      console.error('Failed to export PDF:', err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportHTML = async () => {
    if (!currentProject) return;
    setShowDownloadMenu(false);
    try {
      await exportFullReportHTML(currentProject);
    } catch (err) {
      console.error('Failed to export HTML:', err);
    }
  };

  // Delete functionality
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!currentProject) return;
    setIsDeleting(true);
    try {
      await projectApi.deleteProject(currentProject.id);
      window.location.href = '/';
    } catch (err) {
      console.error('Failed to delete project:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  // Restart debate functionality
  const [showRestartConfirm, setShowRestartConfirm] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);

  const handleRestart = async () => {
    if (!currentProject) return;
    setIsRestarting(true);
    try {
      // Call the debate API to restart
      await projectApi.startDebate(currentProject.id);
      // Refresh the project data
      const data = await projectApi.getProject(currentProject.id);
      setCurrentProject(data);
    } catch (err) {
      console.error('Failed to restart debate:', err);
    } finally {
      setIsRestarting(false);
      setShowRestartConfirm(false);
    }
  };

  useEffect(() => {
    if (!id) return;
    const fetchProject = async () => {
      setLoading(true);
      try {
        const data = await projectApi.getProject(id);
        setCurrentProject(data);
      } catch (err) {
        console.error('Failed to fetch project:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProject();
  }, [id, setCurrentProject, setLoading]);

  const filteredRounds = useMemo(() => {
    if (!currentProject?.rounds) return [];
    if (filterRound === 'all') return currentProject.rounds;
    return currentProject.rounds.filter((r) => r.roundNum === filterRound);
  }, [currentProject?.rounds, filterRound]);

  const allAgents = useMemo(() => {
    if (!currentProject) return [];
    const agents: { name: string; role: string }[] = [];
    currentProject.config.critics.forEach((c) => {
      if (!agents.find((a) => a.role === c)) agents.push({ name: c, role: c });
    });
    currentProject.config.defenders.forEach((d) => {
      if (!agents.find((a) => a.role === d)) agents.push({ name: d, role: d });
    });
    return agents;
  }, [currentProject]);

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
        </div>
      </AppLayout>
    );
  }

  if (!currentProject) {
    return (
      <AppLayout>
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-4">
          <AlertTriangle size={48} className="text-muted-foreground mb-4" />
          <h2 className="text-lg font-medium mb-2">项目不存在</h2>
          <p className="text-sm text-muted-foreground mb-4">无法找到该辩论项目</p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 transition-colors text-sm font-medium"
          >
            <ArrowLeft size={16} />
            返回列表
          </Link>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="animate-fade-in">
        {/* Header */}
        <div className="border-b border-border p-4 lg:p-6">
          <div className="max-w-6xl mx-auto">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
            >
              <ArrowLeft size={14} />
              返回项目列表
            </Link>

            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
              <div>
                <h1 className="text-xl lg:text-2xl font-bold mb-2">{currentProject.title}</h1>
                <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <BookOpen size={14} />
                    {formatDate(currentProject.createdAt)}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <MessageSquare size={14} />
                    {currentProject.config.rounds}轮辩论
                  </span>
                  {currentProject.finalReport && (
                    <span className="flex items-center gap-1.5">
                      <Star size={14} className="text-yellow-400" />
                      综合评分 {currentProject.finalReport.score}
                    </span>
                  )}
                </div>
              </div>

              {/* Download Button */}
              <div className="relative">
                <button
                  onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                  disabled={isExporting}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 transition-all text-sm font-medium shadow-lg shadow-brand-500/25"
                >
                  {isExporting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      导出中...
                    </>
                  ) : (
                    <>
                      <Download size={16} />
                      导出报告
                    </>
                  )}
                </button>

                {showDownloadMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setShowDownloadMenu(false)}
                    />
                    <div className="absolute right-0 top-full mt-2 w-48 bg-card border border-border rounded-xl shadow-xl z-20 overflow-hidden">
                      <button
                        onClick={handleExportPDF}
                        className="w-full flex items-center gap-3 px-4 py-3 text-sm hover:bg-accent transition-colors text-left"
                      >
                        <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
                          <span className="text-red-500 text-xs font-bold">PDF</span>
                        </div>
                        <div>
                          <p className="font-medium">导出 PDF</p>
                          <p className="text-xs text-muted-foreground">适合打印和分享</p>
                        </div>
                      </button>
                      <button
                        onClick={handleExportHTML}
                        className="w-full flex items-center gap-3 px-4 py-3 text-sm hover:bg-accent transition-colors text-left border-t border-border"
                      >
                        <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                          <span className="text-blue-500 text-xs font-bold">HTML</span>
                        </div>
                        <div>
                          <p className="font-medium">导出 HTML</p>
                          <p className="text-xs text-muted-foreground">完整报告，可用浏览器打开</p>
                        </div>
                      </button>
                    </div>
                  </>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2">
                {/* Start/Restart button */}
                {currentProject.status === 'pending' ? (
                  <button
                    onClick={handleRestart}
                    disabled={isRestarting}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 text-white transition-all text-sm font-medium disabled:opacity-50"
                    title="开始辩论"
                  >
                    {isRestarting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        启动中...
                      </>
                    ) : (
                      <>
                        <Play size={14} />
                        开始辩论
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    onClick={() => setShowRestartConfirm(true)}
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-400 transition-all text-sm font-medium"
                    title="重新辩论"
                  >
                    <RotateCcw size={14} />
                    重新辩论
                  </button>
                )}

                {/* Delete button */}
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 transition-all text-sm font-medium"
                  title="删除项目"
                >
                  <Trash2 size={14} />
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowDeleteConfirm(false)} />
            <div className="relative bg-card rounded-2xl shadow-2xl p-6 max-w-sm w-full animate-slide-up border border-border">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center">
                  <AlertTriangle size={24} className="text-red-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">删除项目</h3>
                  <p className="text-sm text-muted-foreground">此操作不可撤销</p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mb-6">
                确定要删除项目&quot;{currentProject.title}&quot;吗？辩论历史和报告都将被永久删除。
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm font-medium"
                >
                  取消
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-red-500 hover:bg-red-600 transition-colors text-sm font-medium disabled:opacity-50"
                >
                  {isDeleting ? '删除中...' : '删除'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Restart Confirmation Modal */}
        {showRestartConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowRestartConfirm(false)} />
            <div className="relative bg-card rounded-2xl shadow-2xl p-6 max-w-sm w-full animate-slide-up border border-border">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                  <RotateCcw size={24} className="text-blue-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">重新辩论</h3>
                  <p className="text-sm text-muted-foreground">将重新运行辩论流程</p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mb-6">
                确定要重新对项目&quot;{currentProject.title}&quot;进行辩论吗？这将替换当前的辩论结果。
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowRestartConfirm(false)}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm font-medium"
                >
                  取消
                </button>
                <button
                  onClick={handleRestart}
                  disabled={isRestarting}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-blue-500 hover:bg-blue-600 transition-colors text-sm font-medium disabled:opacity-50"
                >
                  {isRestarting ? '重新辩论中...' : '确定'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-4 lg:p-6 max-w-6xl mx-auto">
          {/* Filters */}
          <div className="glass-dark rounded-xl p-4 mb-6">
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-2 text-sm">
                <Filter size={14} className="text-muted-foreground" />
                <span className="text-muted-foreground">筛选：</span>
              </div>

              {/* Round filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-muted-foreground">轮次：</span>
                <select
                  value={filterRound}
                  onChange={(e) =>
                    setFilterRound(e.target.value === 'all' ? 'all' : Number(e.target.value))
                  }
                  className="bg-white/5 border border-border rounded-lg px-2 py-1 text-xs outline-none focus:border-brand-500"
                >
                  <option value="all">全部</option>
                  {currentProject.rounds.map((r) => (
                    <option key={r.roundNum} value={r.roundNum}>
                      第{r.roundNum}轮
                    </option>
                  ))}
                </select>
              </div>

              {/* Agent filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-muted-foreground">Agent：</span>
                <select
                  value={filterAgent}
                  onChange={(e) => setFilterAgent(e.target.value)}
                  className="bg-white/5 border border-border rounded-lg px-2 py-1 text-xs outline-none focus:border-brand-500"
                >
                  <option value="all">全部</option>
                  {allAgents.map((a) => (
                    <option key={a.role} value={a.role}>
                      {a.role}
                    </option>
                  ))}
                </select>
              </div>

              {(filterRound !== 'all' || filterAgent !== 'all') && (
                <button
                  onClick={() => {
                    setFilterRound('all');
                    setFilterAgent('all');
                  }}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X size={12} />
                  清除筛选
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Main content - 2/3 */}
            <div className="xl:col-span-2 space-y-6">
              {/* Article section */}
              <div className="glass-dark rounded-xl overflow-hidden">
                <button
                  onClick={() => setArticleExpanded(!articleExpanded)}
                  className="w-full flex items-center justify-between p-4 text-left hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <BookOpen size={16} className="text-brand-400" />
                    <span className="font-medium">文章原文</span>
                  </div>
                  {articleExpanded ? (
                    <ChevronUp size={16} className="text-muted-foreground" />
                  ) : (
                    <ChevronDown size={16} className="text-muted-foreground" />
                  )}
                </button>
                {articleExpanded && (
                  <div className="px-4 pb-4 border-t border-white/5">
                    <div className="prose-content text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                      {currentProject.article || '文章内容未加载'}
                    </div>
                  </div>
                )}
              </div>

              {/* Debate rounds */}
              {filteredRounds.length > 0 && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold flex items-center gap-2">
                    <MessageSquare size={18} className="text-brand-400" />
                    辩论流程
                  </h2>
                  {filteredRounds.map((round, idx) => (
                    <div key={round.roundNum}>
                      {idx > 0 && <div className="h-px bg-border my-6" />}
                      <DebateRound
                        round={round}
                        project={currentProject}
                        filterAgent={filterAgent}
                      />
                    </div>
                  ))}
                </div>
              )}

              {filteredRounds.length === 0 && currentProject.status !== 'pending' && (
                <div className="text-center py-12 text-muted-foreground">
                  <MessageSquare size={32} className="mx-auto mb-3 opacity-50" />
                  <p>没有符合筛选条件的辩论记录</p>
                </div>
              )}

              {currentProject.status === 'pending' && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
                    <Clock size={28} className="text-muted-foreground" />
                  </div>
                  <h3 className="font-medium mb-1">辩论尚未开始</h3>
                  <p className="text-sm text-muted-foreground">等待系统启动辩论流程...</p>
                </div>
              )}
            </div>

            {/* Sidebar - 1/3 */}
            <div className="space-y-6">
              {/* Report */}
              {currentProject.finalReport && (
                <div className="glass-dark rounded-xl p-4">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <Radar size={16} className="text-brand-400" />
                    评审报告
                  </h3>
                  <FinalReportSection report={currentProject.finalReport} />
                </div>
              )}

              {/* Project info */}
              <div className="glass-dark rounded-xl p-4">
                <h3 className="font-semibold text-sm mb-3">项目信息</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">状态</span>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded-full text-xs',
                        currentProject.status === 'completed'
                          ? 'bg-green-500/20 text-green-400'
                          : currentProject.status === 'debating'
                          ? 'bg-blue-500/20 text-blue-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      )}
                    >
                      {currentProject.status === 'completed'
                        ? '已完成'
                        : currentProject.status === 'debating'
                        ? '辩论中'
                        : '待开始'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">辩论轮次</span>
                    <span>{currentProject.config.rounds}轮</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">批评者</span>
                    <span>{currentProject.config.critics.join('、')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">辩护者</span>
                    <span>{currentProject.config.defenders.join('、')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">创建时间</span>
                    <span>{formatDate(currentProject.createdAt)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
