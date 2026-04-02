import Link from "next/link";

import AppShell from "@/components/app-shell";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import StatusTimeline from "@/components/ui/status-timeline";
import { StepState } from "@/types/tender";

const capabilityModules = [
  {
    title: "定向项目发现",
    description: "先基于企业知识库生成采集方向，再按方向去发现更关键的公开项目。"
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
    description: "维护公司介绍、资质、案例和模板，为发现与写标共同提供支撑。"
  }
];

const workflowSteps: Array<{
  key: string;
  label: string;
  state: StepState;
}> = [
  {
    key: "profile",
    label: "企业能力画像",
    state: { status: "success", message: "先用知识库资料生成推荐采集方向。" }
  },
  {
    key: "discover",
    label: "定向发现项目",
    state: { status: "success", message: "按方向发起定向采集，再决定是否跟进。" }
  },
  {
    key: "upload",
    label: "上传招标文件",
    state: { status: "success", message: "确认项目后，再进入现有招标处理主链路。" }
  },
  {
    key: "judge",
    label: "投标判断",
    state: { status: "success", message: "结合知识库继续完成判断和风险提示。" }
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
        description="当前版本把“项目发现”改成了基于企业知识库的定向发现入口。用户先看系统给出的能力画像方向，再定向采集项目，最后进入正式写标流程。"
        actions={
          <>
            <Link className="ui-button-primary" href="/discovery">
              按企业能力找项目
            </Link>
            <Link className="ui-button-secondary" href="/knowledge">
              去维护企业资料
            </Link>
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="当前版本" value="MVP" helper="定向发现 + 主链路" tone="accent" />
            <MetricCard label="发现模式" value="知识驱动" helper="不是盲搜项目" />
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_360px]">
        <div className="space-y-6">
          <PanelCard
            title="今日入口"
            description="优先从定向项目发现进入：先让系统给出推荐方向，再采集和评估项目，最后决定是否进入招标处理。"
          >
            <div className="grid gap-4 md:grid-cols-3">
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/discovery">
                <p className="ui-field-label">发现入口</p>
                <p className="mt-3 text-base font-semibold text-ink">按企业能力找项目</p>
                <p className="ui-help mt-2">先看推荐方向，再发起定向采集和项目筛选。</p>
              </Link>
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/tender">
                <p className="ui-field-label">主链路</p>
                <p className="mt-3 text-base font-semibold text-ink">招标处理</p>
                <p className="ui-help mt-2">上传文件并依次执行解析、判断和初稿生成。</p>
              </Link>
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/knowledge">
                <p className="ui-field-label">资料维护</p>
                <p className="mt-3 text-base font-semibold text-ink">企业资料中心</p>
                <p className="ui-help mt-2">补充资质、案例和模板，提升发现与生成质量。</p>
              </Link>
            </div>
          </PanelCard>

          <PanelCard
            title="当前能力"
            description="这一版重点是把知识库、项目发现和写标主链路真正串起来，但仍然保持 MVP 范围。"
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
          <PanelCard title="流程总览" description="系统当前围绕“先画像、再发现、后写标”的顺序组织。">
            <StatusTimeline steps={workflowSteps} />
          </PanelCard>

          <PanelCard title="当前边界" description="这一期继续控制范围，优先把定向发现跑通。">
            <ul className="space-y-3 text-sm leading-6 text-muted">
              <li>只做单站 ggzy 发现，不做多站聚合。</li>
              <li>不下载附件，不自动进入写标主链路。</li>
              <li>推荐方向完全基于现有知识库，不新增复杂配置后台。</li>
            </ul>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
