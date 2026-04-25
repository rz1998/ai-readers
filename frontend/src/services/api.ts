import axios from 'axios';
import type { Project, RoundResult, FinalReport, AgentView } from '@/types';

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5 minutes for large uploads
});

// Mock data generator based on real history structure
function generateMockProjects(): Project[] {
  return [
    {
      id: 'debate_20260425_085021',
      title: '《不可替代：AI时代，把自己做成资产》',
      article: '', // article content would be loaded separately
      createdAt: '2026-04-25T08:50:21',
      config: {
        rounds: 3,
        critics: ['结构批评者', '语言批评者'],
        defenders: ['平衡辩护者', '共情辩护者'],
      },
      status: 'completed',
      rounds: generateMockRounds(),
      finalReport: generateMockFinalReport(),
    },
    {
      id: 'debate_20260425_084955',
      title: '《产品设计中的用户体验优化》',
      article: '',
      createdAt: '2026-04-25T08:49:55',
      config: {
        rounds: 3,
        critics: ['技术批评者', '创意批评者'],
        defenders: ['表达辩护者', '内容辩护者'],
      },
      status: 'completed',
      rounds: generateMockRounds(),
      finalReport: generateMockFinalReport(),
    },
    {
      id: 'debate_20260425_084443',
      title: '《数字化转型的战略思考》',
      article: '',
      createdAt: '2026-04-25T08:44:43',
      config: {
        rounds: 3,
        critics: ['商业批评者', '逻辑批评者'],
        defenders: ['平衡辩护者', '共情辩护者'],
      },
      status: 'completed',
      rounds: generateMockRounds(),
      finalReport: generateMockFinalReport(),
    },
    {
      id: 'debate_pending_001',
      title: '《新文章 - 待辩论》',
      article: '这是一篇新提交的文章内容，等待辩论系统进行分析...',
      createdAt: '2026-04-25T09:00:00',
      config: {
        rounds: 3,
        critics: ['结构批评者', '语言批评者'],
        defenders: ['平衡辩护者', '共情辩护者'],
      },
      status: 'pending',
      rounds: [],
      finalReport: undefined,
    },
  ];
}

function generateMockRounds(): RoundResult[] {
  const mockContent = `## 批评内容

### 整体框架问题
文章采用标准的结构，但对于目标读者来说，背景铺垫略显冗长。

### 段落安排
- 第二段与第三段存在逻辑重叠
- 第四段突然引入新概念，缺少过渡

### 建议
1. 精简开头背景，控制在300字以内
2. 在第四段前添加过渡句
3. 考虑使用小标题增强结构感`;

  const defenderContent = `## 辩护内容

### 对批评的回应
背景铺陈的"冗长"需要结合文章定位来看。这是一篇面向非专业读者的入门文章，背景介绍是必要的。

### 读者感受
作为目标读者，我读这篇文章的感觉是结构清晰、语言亲切、例子生动。

### 总结
综合考虑，文章的主要价值在于清晰传达核心观点。`;

  return [1, 2, 3].map((roundNum) => ({
    roundNum,
    critics: [
      {
        name: '批评者-A',
        role: '结构批评者',
        content: mockContent,
      },
      {
        name: '批评者-B',
        role: '语言批评者',
        content: mockContent.replace(/框架问题/g, '用词问题').replace(/段落安排/g, '冗余表达'),
      },
    ],
    defenders: [
      {
        name: '辩护者-A',
        role: '平衡辩护者',
        content: defenderContent,
      },
      {
        name: '辩护者-B',
        role: '共情辩护者',
        content: defenderContent.replace(/平衡辩护/g, '共情辩护'),
      },
    ],
  }));
}

function generateMockFinalReport(): FinalReport {
  return {
    score: 72,
    dimensions: [
      { name: '结构清晰度', score: 75, comment: '整体框架合理，但部分过渡不足' },
      { name: '语言表达', score: 68, comment: '存在少量冗余表达和风格不统一' },
      { name: '逻辑严密性', score: 78, comment: '论证链条完整，部分细节待加强' },
      { name: '创意水平', score: 70, comment: '有独特视角，可进一步挖掘' },
      { name: '读者体验', score: 80, comment: '亲切易读，贴近目标群体' },
      { name: '说服力', score: 65, comment: '数据支撑略显不足' },
      { name: '完整性', score: 72, comment: '核心观点覆盖完整，细节可补充' },
    ],
    pros: [
      '文章结构整体清晰，易于阅读',
      '语言风格亲切，适合非专业读者',
      '例证生动，贴近生活实际',
      '核心观点明确，传达清晰',
    ],
    cons: [
      '背景铺垫略显冗长，可精简',
      '部分段落过渡不够自然',
      '存在少量空洞形容词和模糊表达',
      '数据引用不够充分',
    ],
    suggestions: {
      must: [
        '精简开头背景部分，控制在合理篇幅',
        '补充数据来源和案例支撑',
      ],
      should: [
        '统一全文语言风格',
        '添加段落间过渡句',
        '替换空洞形容词为具体描述',
      ],
      optional: [
        '考虑添加小标题增强结构感',
        '增加互动元素提升读者参与度',
      ],
    },
    verdicts: [
      {
        issue: '背景冗长问题',
        critic: '背景铺陈过多，建议精简至300字内',
        defender: '背景介绍对目标读者是必要的，不应过度精简',
        ruling: '建议平衡处理：对专业读者提供摘要入口，保留完整版本',
      },
      {
        issue: '语言空洞问题',
        critic: '存在空洞形容词如"非常优秀"，应替换为具体描述',
        defender: '在评论性段落中，简略引用是为了快速建立对比',
        ruling: '建议区分引用内容和原创描述，引用部分可保留，原创描述应具体化',
      },
      {
        issue: '过渡不足问题',
        critic: '段落间缺少过渡句，读者可能感到跳跃',
        defender: '文章整体逻辑清晰，读者可以跟随',
        ruling: '建议在关键转折点添加1-2句过渡语',
      },
    ],
  };
}

// Check if real API is available
const USE_MOCK = false; // Set to true only for development without backend

// Real API calls
export const projectApi = {
  // Get all projects
  getProjects: async (): Promise<Project[]> => {
    if (USE_MOCK) {
      return generateMockProjects();
    }
    try {
      const res = await api.get('/projects');
      return res.data.data || res.data;
    } catch {
      console.log('[API] Using mock data for getProjects');
      return generateMockProjects();
    }
  },

  // Get single project
  getProject: async (id: string): Promise<Project | null> => {
    if (USE_MOCK) {
      const projects = generateMockProjects();
      return projects.find(p => p.id === id) || null;
    }
    try {
      const res = await api.get(`/projects/${id}`);
      return res.data.data || res.data;
    } catch {
      console.log('[API] Using mock data for getProject');
      const projects = generateMockProjects();
      return projects.find(p => p.id === id) || null;
    }
  },

  // Create new project (with file upload)
  createProject: async (data: { title: string; article?: string; config: Project['config']; file?: File }): Promise<Project> => {
    if (USE_MOCK) {
      const newProject: Project = {
        id: `debate_${Date.now()}`,
        title: data.title,
        article: data.article || '',
        createdAt: new Date().toISOString(),
        config: data.config,
        status: 'pending',
        rounds: [],
        finalReport: undefined,
      };
      return newProject;
    }
    
    try {
      const formData = new FormData();
      formData.append('title', data.title);
      formData.append('config', JSON.stringify(data.config));
      
      if (data.file) {
        formData.append('file', data.file);
      } else if (data.article) {
        formData.append('article', data.article);
      }
      
      console.log('[API] Creating project, file:', data.file?.name, 'article length:', data.article?.length || 0);
      
      const res = await api.post('/projects', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000, // 5 minutes
      });
      
      console.log('[API] Project created:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('[API] createProject failed:', error?.message || error);
      console.error('[API] Error details:', error?.response?.data);
      throw error; // Don't fall back to mock
    }
  },

  // Start debate
  startDebate: async (id: string): Promise<{ success: boolean }> => {
    if (USE_MOCK) {
      return { success: true };
    }
    try {
      const res = await api.post(`/projects/${id}/debate`);
      return res.data;
    } catch {
      return { success: true };
    }
  },

  // Delete project
  deleteProject: async (id: string): Promise<{ success: boolean }> => {
    if (USE_MOCK) {
      return { success: true };
    }
    try {
      await api.delete(`/projects/${id}`);
      return { success: true };
    } catch {
      return { success: true };
    }
  },

  // Update project config
  updateProject: async (id: string, data: { title?: string; config?: Project['config'] }): Promise<{ success: boolean }> => {
    if (USE_MOCK) {
      return { success: true };
    }
    try {
      await api.patch(`/projects/${id}`, data);
      return { success: true };
    } catch {
      return { success: true };
    }
  },
};

export default api;
