import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { projectApi } from '@/services/api';
import { useProjectStore } from '@/store/projectStore';
import { formatRelativeTime, getStatusColor, getStatusLabel } from '@/lib/utils';
import {
  BookOpen,
  Plus,
  Clock,
  MessageSquare,
  Star,
  Upload,
  X,
  FileText,
  ChevronRight,
  Sparkles,
  Trash2,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Project } from '@/types';

function ProjectCard({ project, onDelete }: { project: Project; onDelete: (id: string) => void }) {
  const [showConfirm, setShowConfirm] = useState(false);
  const score = project.finalReport?.score;

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowConfirm(true);
  };

  const confirmDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onDelete(project.id);
    setShowConfirm(false);
  };

  return (
    <>
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowConfirm(false)} />
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
              确定要删除项目&quot;{project.title}&quot;吗？辩论历史和报告都将被永久删除。
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={(e) => { e.preventDefault(); setShowConfirm(false); }}
                className="flex-1 px-4 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm font-medium"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 px-4 py-2.5 rounded-lg bg-red-500 hover:bg-red-600 transition-colors text-sm font-medium"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}


      <div className="relative group">
        {/* Delete button */}
        <button
          onClick={handleDelete}
          className="absolute top-3 right-3 p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/20 hover:opacity-100 transition-all text-muted-foreground hover:text-red-400 z-30 pointer-events-auto"
          title="删除项目"
        >
          <Trash2 size={16} />
        </button>

        <Link
          to={`/projects/${project.id}`}
          className="block"
        >
          <div className="glass-dark rounded-xl p-5 hover:bg-white/10 transition-all duration-300 hover:shadow-lg hover:shadow-brand-500/10 hover:-translate-y-0.5">

            {/* Header */}
            <div className="flex items-start justify-between mb-3 pr-8">
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-foreground group-hover:text-brand-400 transition-colors line-clamp-2 mb-1">
                  {project.title}
                </h3>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock size={12} />
                  <span>{formatRelativeTime(project.createdAt)}</span>
                </div>
              </div>
              <span
                className={cn(
                  'px-2 py-0.5 rounded-full text-xs font-medium ml-2 shrink-0',
                  getStatusColor(project.status)
                )}
              >
                {getStatusLabel(project.status)}
              </span>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <MessageSquare size={14} className="text-brand-400" />
                <span>{project.config.rounds}轮辩论</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ChevronRight size={14} className="text-defender-400" />
                <span>{project.config.critics.length}位批评者</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ChevronRight size={14} className="text-critic-400" />
                <span>{project.config.defenders.length}位辩护者</span>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mt-3">
              {project.status === 'pending' && (
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-yellow-500/50 rounded-full" style={{ width: '5%' }} />
                </div>
              )}
              {project.status === 'debating' && (
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '50%' }} />
                </div>
              )}
              {project.status === 'completed' && (
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: '100%' }} />
                </div>
              )}
            </div>

            {/* Score badge */}
            {score !== undefined && (
              <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Star size={14} className="text-yellow-400" />
                  <span className="text-sm text-muted-foreground">综合评分</span>
                </div>
                <div
                  className={cn(
                    'text-2xl font-bold',
                    score >= 80
                      ? 'text-green-400'
                      : score >= 60
                      ? 'text-yellow-400'
                      : 'text-red-400'
                  )}
                >
                  {score}
                </div>
              </div>
            )}
          </div>
        </Link>
      </div>
    </>
  );
}

function UploadModal({
  open,
  onClose,
  onSubmit,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { title: string; article?: string; config: { rounds: number; critics: string[]; defenders: string[] }; file?: File }) => void;
}) {
  const [title, setTitle] = useState('');
  const [article, setArticle] = useState('');
  const [inputMode, setInputMode] = useState<'text' | 'file'>('text');
  const [fileName, setFileName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Debate configuration
  const [rounds, setRounds] = useState(3);
  const [selectedCritics, setSelectedCritics] = useState<string[]>(['结构批评者', '语言批评者']);
  const [selectedDefenders, setSelectedDefenders] = useState<string[]>(['平衡辩护者', '共情辩护者']);

  const allCritics = ['结构批评者', '逻辑批评者', '语言批评者', '创意批评者', '技术批评者', '商业批评者'];
  const allDefenders = ['平衡辩护者', '共情辩护者', '内容辩护者', '表达辩护者'];

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadFile(file);
    setFileName(file.name);

    // Extract title from filename if empty
    if (!title) {
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
      setTitle(nameWithoutExt);
    }

    // For text files, read content; for binary, just store reference
    if (file.type.startsWith('text/') || file.name.match(/\.(txt|md|markdown)$/i)) {
      file.text().then(text => setArticle(text));
    } else {
      setArticle(''); // Don't read binary files into memory
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    if (inputMode === 'text' && !article.trim()) return;
    if (inputMode === 'file' && !uploadFile) return;
    
    setSubmitting(true);
    try {
      await onSubmit({
        title,
        article: inputMode === 'text' ? article : undefined,
        config: {
          rounds,
          critics: selectedCritics,
          defenders: selectedDefenders,
        },
        file: inputMode === 'file' ? uploadFile || undefined : undefined,
      });
    } catch (err) {
      console.error('Failed to create project:', err);
    } finally {
      setSubmitting(false);
      setTitle('');
      setArticle('');
      setFileName('');
      setUploadFile(null);
      setSelectedCritics(['结构批评者', '语言批评者']);
      setSelectedDefenders(['平衡辩护者', '共情辩护者']);
      setRounds(3);
      onClose();
    }
  };

  const handleClose = () => {
    setTitle('');
    setArticle('');
    setFileName('');
    setInputMode('text');
    setSelectedCritics(['结构批评者', '语言批评者']);
    setSelectedDefenders(['平衡辩护者', '共情辩护者']);
    setRounds(3);
    onClose();
  };

  const toggleCritic = (critic: string) => {
    setSelectedCritics((prev) =>
      prev.includes(critic) ? prev.filter((c) => c !== critic) : [...prev, critic]
    );
  };

  const toggleDefender = (defender: string) => {
    setSelectedDefenders((prev) =>
      prev.includes(defender) ? prev.filter((d) => d !== defender) : [...prev, defender]
    );
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleClose} />
      <div className="relative w-full max-w-2xl bg-card rounded-2xl shadow-2xl animate-slide-up">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center">
              <Upload size={18} className="text-white" />
            </div>
            <div>
              <h2 className="font-semibold">上传新文章</h2>
              <p className="text-xs text-muted-foreground">创建新的辩论项目</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">文章标题</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="输入文章标题"
              className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-border focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-all text-sm"
              required
            />
          </div>

          {/* Input mode selector */}
          <div>
            <label className="block text-sm font-medium mb-1.5">选择输入方式</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setInputMode('text')}
                className={`flex-1 px-4 py-2.5 rounded-lg border transition-all text-sm font-medium ${
                  inputMode === 'text'
                    ? 'bg-brand-500/20 border-brand-500 text-brand-400'
                    : 'bg-white/5 border-border hover:bg-white/10 text-muted-foreground'
                }`}
              >
                粘贴文本
              </button>
              <button
                type="button"
                onClick={() => setInputMode('file')}
                className={`flex-1 px-4 py-2.5 rounded-lg border transition-all text-sm font-medium ${
                  inputMode === 'file'
                    ? 'bg-brand-500/20 border-brand-500 text-brand-400'
                    : 'bg-white/5 border-border hover:bg-white/10 text-muted-foreground'
                }`}
              >
                上传文件
              </button>
            </div>
          </div>

          {/* Text input */}
          {inputMode === 'text' && (
            <div>
              <label className="block text-sm font-medium mb-1.5">文章内容</label>
              <textarea
                value={article}
                onChange={(e) => setArticle(e.target.value)}
                placeholder="粘贴文章内容..."
                rows={12}
                className="w-full px-4 py-3 rounded-lg bg-white/5 border border-border focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-all text-sm resize-none"
                required
              />
            </div>
          )}

          {/* File upload */}
          {inputMode === 'file' && (
            <div>
              <label className="block text-sm font-medium mb-1.5">上传文件</label>
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
                  fileName
                    ? 'border-green-500/50 bg-green-500/5'
                    : 'border-border hover:border-brand-500/50 hover:bg-brand-500/5'
                }`}
              >
                <input
                  type="file"
                  id="file-upload"
                  accept=".txt,.md,.pdf,.doc,.docx"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  {fileName ? (
                    <div className="flex flex-col items-center gap-2">
                      <FileText size={32} className="text-green-400" />
                      <p className="text-sm font-medium text-green-400">{fileName}</p>
                      <p className="text-xs text-muted-foreground">点击更换文件</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center">
                        <Upload size={24} className="text-muted-foreground" />
                      </div>
                      <p className="text-sm font-medium">点击上传文件</p>
                      <p className="text-xs text-muted-foreground">
                        支持 TXT, MD, PDF, DOC, DOCX
                      </p>
                    </div>
                  )}
                </label>
              </div>
              {fileName && (
                <p className="text-xs text-muted-foreground mt-2">
                  文件内容已加载，共 {article.length} 字符
                </p>
              )}
            </div>
          )}

          {/* Debate Configuration */}
          <div className="border-t border-border pt-4 mt-4">
            <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
              <Sparkles size={14} className="text-brand-400" />
              辩论配置
            </h3>

            {/* Rounds */}
            <div className="mb-4">
              <label className="block text-xs text-muted-foreground mb-2">辩论轮次</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setRounds(n)}
                    className={`w-10 h-10 rounded-lg border transition-all text-sm font-medium ${
                      rounds === n
                        ? 'bg-brand-500/20 border-brand-500 text-brand-400'
                        : 'bg-white/5 border-border hover:bg-white/10 text-muted-foreground'
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>

            {/* Critics */}
            <div className="mb-4">
              <label className="block text-xs text-muted-foreground mb-2">批评者角色</label>
              <div className="flex flex-wrap gap-2">
                {allCritics.map((critic) => (
                  <button
                    key={critic}
                    type="button"
                    onClick={() => toggleCritic(critic)}
                    className={`px-3 py-1.5 rounded-lg border transition-all text-xs font-medium ${
                      selectedCritics.includes(critic)
                        ? 'bg-red-500/20 border-red-500/50 text-red-400'
                        : 'bg-white/5 border-border hover:bg-white/10 text-muted-foreground'
                    }`}
                  >
                    {critic}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-1">已选 {selectedCritics.length} 个</p>
            </div>

            {/* Defenders */}
            <div className="mb-4">
              <label className="block text-xs text-muted-foreground mb-2">辩护者角色</label>
              <div className="flex flex-wrap gap-2">
                {allDefenders.map((defender) => (
                  <button
                    key={defender}
                    type="button"
                    onClick={() => toggleDefender(defender)}
                    className={`px-3 py-1.5 rounded-lg border transition-all text-xs font-medium ${
                      selectedDefenders.includes(defender)
                        ? 'bg-green-500/20 border-green-500/50 text-green-400'
                        : 'bg-white/5 border-border hover:bg-white/10 text-muted-foreground'
                    }`}
                  >
                    {defender}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-1">已选 {selectedDefenders.length} 个</p>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-4 border-t border-border">
            <button
              type="button"
              onClick={handleClose}
              className="px-5 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm font-medium"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={
                submitting ||
                !title.trim() ||
                (inputMode === 'text' && !article.trim()) ||
                (inputMode === 'file' && !uploadFile) ||
                selectedCritics.length === 0 ||
                selectedDefenders.length === 0
              }
              className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  创建中...
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  开始辩论
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function ProjectsPage() {
  const { projects, setProjects, loading, setLoading } = useProjectStore();
  const [uploadOpen, setUploadOpen] = useState(false);

  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      try {
        const data = await projectApi.getProjects();
        setProjects(data);
      } catch (err) {
        console.error('Failed to fetch projects:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, [setProjects, setLoading]);

  const handleCreateProject = async (data: { title: string; article?: string; config: { rounds: number; critics: string[]; defenders: string[] }; file?: File }) => {
    await projectApi.createProject({
      title: data.title,
      article: data.article,
      config: data.config,
      file: data.file,
    });
    const updated = await projectApi.getProjects();
    setProjects(updated);
  };

  const handleDeleteProject = async (id: string) => {
    await projectApi.deleteProject(id);
    const updated = await projectApi.getProjects();
    setProjects(updated);
  };

  return (
    <AppLayout>
      <div className="p-4 lg:p-8 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold mb-1">文章辩论项目</h1>
            <p className="text-muted-foreground text-sm">
              AI多Agent系统对文章进行多轮辩论评审
            </p>
          </div>
          <button
            onClick={() => setUploadOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 transition-all text-sm font-medium shadow-lg shadow-brand-500/25"
          >
            <Plus size={18} />
            上传文章
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          {[
            { label: '总项目', value: projects.length, icon: BookOpen, color: 'from-brand-500 to-brand-600' },
            { label: '已完成', value: projects.filter(p => p.status === 'completed').length, icon: Star, color: 'from-green-500 to-green-600' },
            { label: '辩论中', value: projects.filter(p => p.status === 'debating').length, icon: MessageSquare, color: 'from-blue-500 to-blue-600' },
            { label: '待开始', value: projects.filter(p => p.status === 'pending').length, icon: Clock, color: 'from-yellow-500 to-yellow-600' },
          ].map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="glass-dark rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <div className={cn('w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center', stat.color)}>
                    <Icon size={18} className="text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
          </div>
        )}

        {/* Projects grid */}
        {!loading && projects.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} onDelete={handleDeleteProject} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && projects.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
              <FileText size={28} className="text-muted-foreground" />
            </div>
            <h3 className="font-medium mb-1">暂无项目</h3>
            <p className="text-sm text-muted-foreground mb-4">上传第一篇文章开始辩论</p>
            <button
              onClick={() => setUploadOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 transition-colors text-sm font-medium"
            >
              <Plus size={16} />
              上传文章
            </button>
          </div>
        )}
      </div>

      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSubmit={handleCreateProject}
      />
    </AppLayout>
  );
}
