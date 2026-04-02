"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import AppShell from "@/components/app-shell";
import EmptyState from "@/components/ui/empty-state";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import { getDiscoveryProjectDetail } from "@/lib/api";
import { DiscoveryProjectDetail } from "@/types/discovery";

function levelLabel(level: string) {
  if (level === "high") {
    return "高推荐";
  }
  if (level === "medium") {
    return "中推荐";
  }
  return "低推荐";
}

export default function DiscoveryDetailPage() {
  const params = useParams<{ leadId: string }>();
  const leadId = Array.isArray(params.leadId) ? params.leadId[0] : params.leadId;
  const [project, setProject] = useState<DiscoveryProjectDetail | null>(null);
  const [pageMessage, setPageMessage] = useState("加载中...");

  useEffect(() => {
    if (!leadId) {
      return;
    }

    async function loadProjectDetail() {
      try {
        const response = await getDiscoveryProjectDetail(leadId);
        setProject(response);
        setPageMessage("已加载项目详情，可查看方向命中、知识命中和风险说明。");
      } catch (error) {
        const message = error instanceof Error ? error.message : "加载项目详情失败";
        setPageMessage(message);
      }
    }

    void loadProjectDetail();
  }, [leadId]);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Discovery Detail"
        title={project?.title ?? "项目详情"}
        description="详情页会解释这个项目为什么值得关注：既展示知识支撑，也展示它与当前发现方向的匹配情况。"
        actions={
          <>
            <Link className="ui-button-secondary" href="/discovery">
              返回项目发现
            </Link>
            <Link className="ui-button-primary" href="/tender">
              去上传文件写标书
            </Link>
          </>
        }
      />

      {!project ? (
        <PanelCard title="项目详情" description="项目数据加载失败或尚未准备完成。">
          <EmptyState title="暂时无法显示项目详情" description={pageMessage} />
        </PanelCard>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="推荐分"
              value={String(project.match_result.recommendation_score)}
              helper={levelLabel(project.match_result.recommendation_level)}
              tone="accent"
            />
            <MetricCard
              label="方向命中分"
              value={String(project.match_result.targeting_match_score)}
              helper={project.match_result.profile_title || "未绑定方向"}
            />
            <MetricCard
              label="知识支撑分"
              value={String(project.match_result.knowledge_support_score)}
              helper={`${project.match_result.matched_knowledge.length} 条知识命中`}
            />
            <MetricCard
              label="招标单位"
              value={project.extract_result.tender_unit || "待识别"}
              helper={project.extract_result.budget_text || "待识别预算"}
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.28fr)_360px]">
            <div className="space-y-6">
              <PanelCard
                title="项目原文与入口"
                description="系统保留原文入口，用户确认项目后再手工进入招标处理流程。"
                actions={
                  <a className="ui-button-secondary" href={project.detail_url} target="_blank" rel="noreferrer">
                    查看原文
                  </a>
                }
              >
                <div className="space-y-4 rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted">
                  <p>标题：{project.title}</p>
                  <p>原文地址：{project.detail_url}</p>
                  <p>规范地址：{project.canonical_url}</p>
                  <p>{pageMessage}</p>
                </div>
              </PanelCard>

              <PanelCard title="详情正文" description="本期只展示采集到的正文文本，不处理附件。">
                <pre className="ui-document-block">{project.detail_text || "暂无详情正文"}</pre>
              </PanelCard>
            </div>

            <div className="space-y-6">
              <PanelCard title="为什么这是关键项目" description="先看它与当前发现方向的匹配，再看知识支撑是否足够。">
                <div className="space-y-4">
                  <div className="rounded-2xl border bg-surface px-4 py-4">
                    <p className="ui-field-label">方向命中</p>
                    <p className="mt-3 text-sm font-semibold text-ink">
                      {project.match_result.profile_title || "当前不是定向采集方向命中项目"}
                    </p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                      {project.match_result.targeting_reasons.map((item) => (
                        <li key={item}>- {item}</li>
                      ))}
                    </ul>
                    <div className="mt-3 space-y-2 text-xs text-subtle">
                      <p>命中关键词：{project.match_result.matched_keywords.join("、") || "无"}</p>
                      <p>命中地区：{project.match_result.matched_regions.join("、") || "无"}</p>
                      <p>
                        命中资质词：
                        {project.match_result.matched_qualification_terms.join("、") || "无"}
                      </p>
                      <p>命中行业词：{project.match_result.matched_industry_terms.join("、") || "无"}</p>
                    </div>
                  </div>

                  <div className="rounded-2xl border bg-surface px-4 py-4">
                    <p className="ui-field-label">知识支撑</p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                      {project.match_result.recommendation_reasons.length ? (
                        project.match_result.recommendation_reasons.map((item) => <li key={item}>- {item}</li>)
                      ) : (
                        <li>- 暂无推荐理由</li>
                      )}
                    </ul>
                  </div>

                  <div className="rounded-2xl border bg-surface px-4 py-4">
                    <p className="ui-field-label">资料缺口与风险</p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                      {project.match_result.knowledge_gaps.map((item) => (
                        <li key={item}>- {item}</li>
                      ))}
                      {project.match_result.risks.map((item) => (
                        <li key={item}>- {item}</li>
                      ))}
                      {!project.match_result.knowledge_gaps.length && !project.match_result.risks.length ? (
                        <li>- 暂无明显缺口或风险提示</li>
                      ) : null}
                    </ul>
                  </div>
                </div>
              </PanelCard>

              <PanelCard title="抽取字段" description="缺失字段不会阻断入池，但需要人工复核。">
                <div className="space-y-4">
                  <div className="rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted">
                    <p>项目名称：{project.extract_result.project_name || "待识别"}</p>
                    <p>项目编号：{project.extract_result.project_code || "待识别"}</p>
                    <p>地区：{project.extract_result.region || "待识别"}</p>
                    <p>预算：{project.extract_result.budget_text || "待识别"}</p>
                    <p>截止时间：{project.extract_result.deadline_text || "待识别"}</p>
                  </div>
                  <div className="rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted">
                    <p className="font-semibold text-ink">资格要求</p>
                    <ul className="mt-2 space-y-2">
                      {project.extract_result.qualification_requirements.length ? (
                        project.extract_result.qualification_requirements.map((item) => <li key={item}>- {item}</li>)
                      ) : (
                        <li>- 待人工判断</li>
                      )}
                    </ul>
                  </div>
                </div>
              </PanelCard>

              <PanelCard title="知识命中" description="用于解释系统为什么会给出当前推荐结论。">
                {project.match_result.matched_knowledge.length ? (
                  <div className="space-y-3">
                    {project.match_result.matched_knowledge.map((item) => (
                      <article
                        key={`${item.category}-${item.document_title}-${item.section_title}`}
                        className="rounded-2xl border bg-surface px-4 py-4"
                      >
                        <p className="ui-field-label">{item.category}</p>
                        <p className="mt-3 text-sm font-semibold text-ink">{item.document_title}</p>
                        <p className="ui-help mt-1">{item.section_title}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="没有命中知识片段"
                    description="可以先去资料中心补充资质、案例或公司介绍。"
                  />
                )}
              </PanelCard>
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}
