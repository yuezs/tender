import Link from "next/link";

import AppShell from "@/components/app-shell";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import StatusTimeline from "@/components/ui/status-timeline";
import { StepState } from "@/types/tender";

const capabilityModules = [
  {
    title: "项目发现",
    description: "手动采集单站公开项目，形成内部线索池并给出推荐结果。"
  },
  {
    title: "招标处理主链路",
    description: "围绕单个招标文件执行上传、解析、抽取、判断和初稿生成。"
  },
  {
    title: "结果评审",
    description: "集中查看结构化字段、投标建议、初稿内容和知识引用。"
  },
  {
    title: "企业资料中心",
    description: "维护公司介绍、资质、案例和模板，为推荐和写标提供支撑。"
  }
];

const workflowSteps: Array<{
  key: string;
  label: string;
  state: StepState;
}> = [
  {
    key: "discover",
    label: "项目发现与筛选",
    state: { status: "success", message: "手动采集 ggzy 项目，先看推荐再决定是否推进。" }
  },
  {
    key: "upload",
    label: "上传招标文件",
    state: { status: "success", message: "现有主链路保持不变，继续支持上传处理。" }
  },
  {
    key: "parse",
    label: "解析与字段抽取",
    state: { status: "success", message: "支持解析文本并抽取核心字段。" }
  },
  {
    key: "judge",
    label: "投标判断",
    state: { status: "success", message: "结合知识库生成判断和风险提示。" }
  },
  {
    key: "generate",
    label: "初稿生成",
    state: { status: "success", message: "在主链路中继续生成标书初稿。" }
  }
];

export default function HomePage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Internal Tender Desk"
        title="AI 招投标助手"
        description="当前版本在现有写标书主链路前增加了“项目发现”层。用户先在系统内筛项目、看推荐，再决定是否进入正式写标流程。"
        actions={
          <>
            <Link className="ui-button-primary" href="/discovery">
              进入项目发现
            </Link>
            <Link className="ui-button-secondary" href="/tender">
              进入招标处理
            </Link>
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="当前版本" value="MVP" helper="发现层 + 主链路" tone="accent" />
            <MetricCard label="数据源" value="1 个站点" helper="ggzy 手动采集" />
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_360px]">
        <div className="space-y-6">
          <PanelCard
            title="今日入口"
            description="当前推荐先从项目发现进入，筛出值得跟进的项目后，再转到现有写标书主链路。"
          >
            <div className="grid gap-4 md:grid-cols-3">
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/discovery">
                <p className="ui-field-label">前置层</p>
                <p className="mt-3 text-base font-semibold text-ink">项目发现</p>
                <p className="ui-help mt-2">手动采集、筛选项目、查看推荐分和理由。</p>
              </Link>
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/tender">
                <p className="ui-field-label">主链路</p>
                <p className="mt-3 text-base font-semibold text-ink">招标处理</p>
                <p className="ui-help mt-2">上传文件并依次执行解析、判断和初稿生成。</p>
              </Link>
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/knowledge">
                <p className="ui-field-label">资料维护</p>
                <p className="mt-3 text-base font-semibold text-ink">企业资料中心</p>
                <p className="ui-help mt-2">补充资质、案例和模板，提升推荐与生成质量。</p>
              </Link>
            </div>
          </PanelCard>

          <PanelCard
            title="当前能力"
            description="这一版重点是把项目发现、知识库支撑和写标书主链路衔接起来，但不扩大到多站聚合或自动附件处理。"
          >
            <div className="grid gap-4 md:grid-cols-2">
              {capabilityModules.map((item) => (
                <article key={item.title} className="ui-panel-muted px-4 py-4">
                  <p className="text-base font-semibold text-ink">{item.title}</p>
                  <p className="ui-copy mt-2">{item.description}</p>
                </article>
              ))}
            </div>
          </PanelCard>
        </div>

        <div className="space-y-6">
          <PanelCard title="流程总览" description="系统当前围绕“先发现，再写标”的顺序组织。">
            <StatusTimeline steps={workflowSteps} />
          </PanelCard>

          <PanelCard title="当前边界" description="这期有意控制范围，优先把流程跑通。">
            <ul className="space-y-3 text-sm leading-6 text-muted">
              <li>只做单站 ggzy 手动采集，不做多站聚合。</li>
              <li>不下载附件，不解析附件，不自动进入写标书链路。</li>
              <li>推荐逻辑优先使用规则评分和现有知识库，不增加新的评分 agent。</li>
            </ul>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
