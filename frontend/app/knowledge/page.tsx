import AppShell from "@/components/app-shell";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";

const categories = [
  {
    title: "公司介绍",
    code: "company_profile",
    description: "沉淀公司概况、核心能力、服务优势和行业定位。"
  },
  {
    title: "资质证书",
    code: "qualifications",
    description: "沉淀营业执照、行业资质、认证和可复用资质描述。"
  },
  {
    title: "项目案例",
    code: "project_cases",
    description: "沉淀历史中标项目、实施成果和可复用案例段落。"
  },
  {
    title: "模板素材",
    code: "templates",
    description: "沉淀技术方案、商务响应和交付承诺的模板内容。"
  }
];

export default function KnowledgePage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Knowledge Workspace"
        title="企业资料中心"
        description="围绕公司介绍、资质、案例与模板做轻量资料沉淀。当前页面仍是第一版空壳，但已明确后续会承载上传、处理、检索和引用链路。"
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="资料类型" value="4 类" helper="固定分类，不扩散" tone="accent" />
            <MetricCard label="检索方式" value="LIKE" helper="分类 + tags + 关键词" />
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.22fr)_360px]">
        <PanelCard
          title="资料分类"
          description="分类名称面向业务使用，英文 code 仅作为系统辅助标识。"
        >
          <div className="grid gap-4 md:grid-cols-2">
            {categories.map((category) => (
              <article key={category.code} className="ui-panel-muted px-4 py-4">
                <p className="ui-field-label">{category.code}</p>
                <p className="mt-3 text-base font-semibold text-ink">{category.title}</p>
                <p className="ui-copy mt-2">{category.description}</p>
              </article>
            ))}
          </div>
        </PanelCard>

        <div className="space-y-6">
          <PanelCard
            title="处理方式"
            description="当前版本保持轻量流程，目的是给 judge 和 generate 稳定提供可追溯的知识片段。"
          >
            <ol className="space-y-3 text-sm leading-6 text-muted">
              <li>1. 上传资料文件，当前优先支持 txt / docx。</li>
              <li>2. 后端解析文本并切成规则片段。</li>
              <li>3. 片段写入 MySQL，供 orchestrator 按任务类型检索。</li>
              <li>4. Agent 只消费整理后的上下文，不直接访问数据库。</li>
            </ol>
          </PanelCard>

          <PanelCard
            title="后续入口"
            description="这版页面先作为资料中心框架，为后续上传、列表、处理和检索展示预留位置。"
          >
            <div className="space-y-4">
              <div className="rounded-2xl border border-dashed bg-surface px-4 py-4">
                <p className="text-sm font-semibold text-ink">上传区</p>
                <p className="ui-help mt-2">后续会在这里接入文档上传、分类和处理状态。</p>
              </div>
              <div className="rounded-2xl border border-dashed bg-surface px-4 py-4">
                <p className="text-sm font-semibold text-ink">检索区</p>
                <p className="ui-help mt-2">后续会在这里展示检索命中、引用次数和处理状态。</p>
              </div>
            </div>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
