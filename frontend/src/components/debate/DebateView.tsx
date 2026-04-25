import React from 'react';
import { Filter, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Project, FilterRound, FilterAgent } from '@/types';

interface DebateViewProps {
  project: Project;
  filteredRounds: Project['rounds'];
  filterRound: FilterRound;
  filterAgent: FilterAgent;
  onFilterRoundChange: (filter: FilterRound) => void;
  onFilterAgentChange: (filter: FilterAgent) => void;
  expandedRounds: Set<number>;
  onToggleRound: (round: number) => void;
}

export function DebateView({
  project,
  filteredRounds,
  filterRound,
  filterAgent,
  onFilterRoundChange,
  onFilterAgentChange,
  expandedRounds,
  onToggleRound,
}: DebateViewProps) {
  const allAgents = React.useMemo(() => {
    const agents = new Set<string>();
    project.rounds.forEach((round) => {
      round.critics.forEach((c) => agents.add(c.name));
      round.defenders.forEach((d) => agents.add(d.name));
    });
    return Array.from(agents);
  }, [project.rounds]);

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="glass-dark rounded-xl p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2 text-sm">
            <Filter size={14} className="text-muted-foreground" />
            <span className="text-muted-foreground">筛选：</span>
          </div>

          {/* Round filter */}
          <select
            value={filterRound}
            onChange={(e) =>
              onFilterRoundChange(
                e.target.value === 'all' ? 'all' : Number(e.target.value)
              )
            }
            className="bg-white/5 border border-border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="all">全部轮次</option>
            {project.rounds.map((_, i) => (
              <option key={i} value={i + 1}>
                第 {i + 1} 轮
              </option>
            ))}
          </select>

          {/* Agent filter */}
          <select
            value={filterAgent}
            onChange={(e) => onFilterAgentChange(e.target.value)}
            className="bg-white/5 border border-border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="all">全部角色</option>
            {allAgents.map((agent) => (
              <option key={agent} value={agent}>
                {agent}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Rounds */}
      {filteredRounds.length === 0 && project.status !== 'pending' && (
        <div className="text-center py-12">
          <MessageSquare size={32} className="mx-auto mb-3 opacity-50" />
          <p>没有符合筛选条件的辩论记录</p>
        </div>
      )}

      {filteredRounds.map((round, idx) => (
        <div key={idx} className="glass-dark rounded-xl p-6 mb-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">
              第 {round.roundNum} 轮辩论
            </h3>
            <button
              onClick={() => onToggleRound(round.roundNum)}
              className="text-sm text-brand-400 hover:text-brand-300"
            >
              {expandedRounds.has(round.roundNum) ? '收起' : '展开'}
            </button>
          </div>

          {/* Critics */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-red-400 mb-3">👥 批评者</h4>
            <div className="space-y-3">
              {round.critics
                .filter(
                  (c) =>
                    filterAgent === 'all' ||
                    c.name === filterAgent
                )
                .map((critic) => (
                  <div
                    key={critic.name}
                    className={cn(
                      'bg-white/5 rounded-lg p-4',
                      expandedRounds.has(round.roundNum) || filterAgent !== 'all'
                        ? 'block'
                        : 'hidden'
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-red-400">
                        {critic.name}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                      {critic.content}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Defenders */}
          <div>
            <h4 className="text-sm font-medium text-green-400 mb-3">🛡️ 辩护者</h4>
            <div className="space-y-3">
              {round.defenders
                .filter(
                  (d) =>
                    filterAgent === 'all' ||
                    d.name === filterAgent
                )
                .map((defender) => (
                  <div
                    key={defender.name}
                    className={cn(
                      'bg-white/5 rounded-lg p-4',
                      expandedRounds.has(round.roundNum) || filterAgent !== 'all'
                        ? 'block'
                        : 'hidden'
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-green-400">
                        {defender.name}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                      {defender.content}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      ))}

      {/* Pending state */}
      {project.status === 'pending' && (
        <div className="text-center py-12">
          <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
            <Clock size={28} className="text-muted-foreground" />
          </div>
          <h3 className="font-medium mb-1">辩论尚未开始</h3>
          <p className="text-sm text-muted-foreground">等待系统启动辩论流程...</p>
        </div>
      )}
    </div>
  );
}

function Clock({ size, className }: { size: number; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}
