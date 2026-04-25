export interface Project {
  id: string;
  title: string;
  article: string;
  createdAt: string;
  config: {
    rounds: number;
    critics: string[];
    defenders: string[];
  };
  status: 'pending' | 'processing' | 'debating' | 'completed';
  rounds: RoundResult[];
  finalReport?: FinalReport;
}

export interface RoundResult {
  roundNum: number;
  critics: AgentView[];
  defenders: AgentView[];
}

export interface AgentView {
  name: string;    // 如"批评者-A"
  role: string;    // 如"结构批评者"
  content: string; // 评审/辩护内容
}

export interface FinalReport {
  score: number;
  dimensions: DimensionScore[];
  pros: string[];
  cons: string[];
  suggestions: Suggestions;
  verdicts: Verdict[];
}

export interface DimensionScore {
  name: string;
  score: number;
  comment: string;
}

export interface Suggestions {
  must: string[];
  should: string[];
  optional: string[];
}

export interface Verdict {
  issue: string;
  critic: string;
  defender: string;
  ruling: string;
}

export type FilterRound = number | 'all';
export type FilterAgent = string | 'all';
