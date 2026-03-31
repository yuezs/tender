import Link from "next/link";

import AppShell from "@/components/app-shell";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import StatusTimeline from "@/components/ui/status-timeline";
import { StepState } from "@/types/tender";

const capabilityModules = [
  {
    title: "招标处理主链路",
    description: "围绕单个招标文件完成上传、解析、抽取、判断与生成。"
  },
  {
    title: "结果评审与引用知识",
    description: "将投标建议、标书初稿和知识引用整理为可审阅结果。"
  },
  {
    title: "企业资料中心",
    description: "围绕公司介绍、资质、案例和模板做轻量知识沉淀与检索。"
  }
];

const workflowSteps: Array<{
  key: string;
  label: string;
  state: StepState;
}> = [
  {
    key: "upload",
    label: "上传招标文件",
    state: { status: "success", message: "已支持 txt / docx 上传，pdf 入口已预留。" }
  },
  {
    key: "parse",
    label: "解析与字段抽取",
    state: { status: "success", message: "支持文本解析和基础结构化抽取。" }
  },
  {
    key: "judge",
    label: "结合知识生成判断",
    state: { status: "success", message: "judge_agent 已通过 orchestrator 使用 qualifications 与 project_cases。" }
  },
  {
    key: "generate",
    label: "结合知识生成初稿",
    state: { status: "success", message: "generate_agent 已通过 orchestrator 使用 company_profile、templates 与 project_cases。" }
  }
];

export default function HomePage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Internal Tender Desk"
        title="辅助投标工作台"
        description="面向投标专员、商务人员和项目经理的内部工作台。当前版本重点保证招标主链路和企业知识引用稳定可用，而不是做复杂的外部展示。"
        actions={
          <>
            <Link className="ui-button-primary" href="/tender">
              进入招标处理
            </Link>
            <Link className="ui-button-secondary" href="/knowledge">
              查看资料中心
            </Link>
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="当前版本" value="MVP" helper="主链路已跑通" tone="accent" />
            <MetricCard label="知识类型" value="4 类" helper="公司 / 资质 / 案例 / 模板" />
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_360px]">
        <div className="space-y-6">
          <PanelCard
            title="今日可执行工作"
            description="当前前端以文档工作台为核心组织方式，优先服务单个招标文件的处理、评审与结果阅读。"
          >
            <div className="grid gap-4 md:grid-cols-3">
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/tender">
                <p className="ui-field-label">主入口</p>
                <p className="mt-3 text-base font-semibold text-ink">处理招标文件</p>
                <p className="ui-help mt-2">从上传开始，依次完成解析、判断与生成。</p>
              </Link>
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/results">
                <p className="ui-field-label">结果阅读</p>
                <p className="mt-3 text-base font-semibold text-ink">查看评审结果</p>
                <p className="ui-help mt-2">聚合抽取结果、投标建议、初稿内容与知识引用。</p>
              </Link>
              <Link className="ui-panel-muted px-4 py-4 transition hover:border-accent/40 hover:bg-accent-soft/60" href="/knowledge">
                <p className="ui-field-label">资料维护</p>
                <p className="mt-3 text-base font-semibold text-ink">管理企业资料</p>
                <p className="ui-help mt-2">围绕资质、案例和模板构建轻量知识沉淀。</p>
              </Link>
            </div>
          </PanelCard>

          <PanelCard
            title="当前系统能力"
            description="这版重点在于把招标处理和知识引用串起来，让用户能稳定看到输入、过程、结论和证据。"
          >
            <div className="grid gap-4 md:grid-cols-3">
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
          <PanelCard title="处理链路" description="当前工作流围绕单个招标任务组织，适合内部业务人员快速推进。">
            <StatusTimeline steps={workflowSteps} />
          </PanelCard>

          <PanelCard title="当前边界" description="本阶段保持系统简单可控，优先把流程和证据链做扎实。">
            <ul className="space-y-3 text-sm leading-6 text-muted">
              <li>不做复杂权限与多人协作。</li>
              <li>不做向量检索、rerank 和外部网盘同步。</li>
              <li>当前生成链路使用 mock Agent 输出，但知识检索和上下文拼装是真实流程。</li>
            </ul>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
