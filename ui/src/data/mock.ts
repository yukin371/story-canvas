export type WorkspaceStat = {
  label: string;
  value: string;
  detail: string;
};

export type ChapterCard = {
  id: string;
  title: string;
  status: string;
  summary: string;
  reviewScore: number;
  updatedAt: string;
  issues: string[];
};

export type IllustrationJob = {
  title: string;
  mode: "text-to-image" | "image-to-image";
  target: string;
  status: string;
  provider: string;
  updatedAt: string;
};

export const workspaceStats: WorkspaceStat[] = [
  {
    label: "活跃项目",
    value: "4",
    detail: "样例与真实写作工程共用一个协议层",
  },
  {
    label: "待处理审查",
    value: "12",
    detail: "优先聚焦章节审查、Scene review 和 workflow gate",
  },
  {
    label: "插画资产",
    value: "37",
    detail: "文生图、图生图和 provider 记录将统一归档",
  },
  {
    label: "本轮目标",
    value: "v1.0.x",
    detail: "稳定核心协议，同时提前推进视觉壳与图片能力",
  },
];

export const chapters: ChapterCard[] = [
  {
    id: "chapter-001",
    title: "夜港仓门",
    status: "需要修订",
    summary: "开篇钩子成立，但场景推进略平，章节尾部的 suspense thread 还不够硬。",
    reviewScore: 76,
    updatedAt: "2026-04-26 21:10",
    issues: ["角色处境已立住", "主线钩子不足", "scene 2 连续性偏弱"],
  },
  {
    id: "chapter-002",
    title: "账册余烬",
    status: "审查中",
    summary: "世界规则交代更清楚，但伏笔兑现节奏仍需要压缩。",
    reviewScore: 82,
    updatedAt: "2026-04-26 20:35",
    issues: ["设定兑现变好", "说明段略多"],
  },
  {
    id: "chapter-003",
    title: "空棺夜巡",
    status: "已通过",
    summary: "节奏与情绪契约基本贴合，适合作为后续长篇样例的一章基线。",
    reviewScore: 89,
    updatedAt: "2026-04-26 18:42",
    issues: ["可以进入导出", "建议补插画参考"],
  },
];

export const illustrationJobs: IllustrationJob[] = [
  {
    title: "chapter-001 scene key art",
    mode: "text-to-image",
    target: "章节 chapter-001",
    status: "已生成",
    provider: "OpenAI / compatible gateway",
    updatedAt: "2026-04-26 22:15",
  },
  {
    title: "linzhou portrait variant",
    mode: "image-to-image",
    target: "角色 char-linzhou",
    status: "待确认",
    provider: "OpenAI / compatible gateway",
    updatedAt: "2026-04-26 21:48",
  },
  {
    title: "urban occult moodboard",
    mode: "text-to-image",
    target: "项目 mood pack",
    status: "排队中",
    provider: "OpenAI / compatible gateway",
    updatedAt: "2026-04-26 21:21",
  },
];
