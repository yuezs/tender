"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import AppShell from "@/components/app-shell";
import EmptyState from "@/components/ui/empty-state";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import { generateTender, resolveApiUrl } from "@/lib/api";
import { TenderFlowSnapshot } from "@/types/tender";

export default function ResultsPage() {
  const [snapshot, setSnapshot] = useState<TenderFlowSnapshot | null>(null);
  const [isPreparingDownload, setIsPreparingDownload] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("latestTenderFlow");
    if (!raw) {
      return;
    }

    try {
      setSnapshot(JSON.parse(raw) as TenderFlowSnapshot);
    } catch {
      localStorage.removeItem("latestTenderFlow");
    }
  }, []);

  const extractSummary = snapshot
    ? [
        { label: "项目名称", value: snapshot.extract.project_name || "未识别" },
        { label: "招标单位", value: snapshot.extract.tender_company || "未识别" },
        { label: "预算金额", value: snapshot.extract.budget || "未识别" },
        { label: "截止时间", value: snapshot.extract.deadline || "未识别" }
      ]
    : [];

  const combinedKnowledge = snapshot
    ? [...(snapshot.judge.knowledge_used ?? []), ...(snapshot.generate.knowledge_used ?? [])].filter(
        (item, index, items) =>
          items.findIndex(
            (candidate) =>
              candidate.category === item.category &&
              candidate.document_title === item.document_title &&
              candidate.section_title === item.section_title
          ) === index
      )
    : [];

  const uploadedAt = snapshot ? new Date(snapshot.uploadedAt).toLocaleString("zh-CN") : "";
  const downloadUrl =
    snapshot?.generate.download_ready && snapshot.generate.download_url
      ? resolveApiUrl(snapshot.generate.download_url)
      : "";

  async function handleDownloadDraft() {
    if (!snapshot || isPreparingDownload) {
      return;
    }

    if (downloadUrl) {
      window.open(downloadUrl, "_blank", "noopener,noreferrer");
      return;
    }

    setIsPreparingDownload(true);
    try {
      const nextGenerate = await generateTender(snapshot.upload.file_id);
      const nextSnapshot: TenderFlowSnapshot = {
        ...snapshot,
        generate: nextGenerate
      };

      localStorage.setItem("latestTenderFlow", JSON.stringify(nextSnapshot));
      setSnapshot(nextSnapshot);

      const nextUrl =
        nextGenerate.download_ready && nextGenerate.download_url
          ? resolveApiUrl(nextGenerate.download_url)
          : "";

      if (!nextUrl) {
        throw new Error("标书已重新生成，但下载地址仍不可用。");
      }

      window.open(nextUrl, "_blank", "noopener,noreferrer");
    } catch (error) {
      const message = error instanceof Error ? error.message : "标书下载准备失败";
      window.alert(message);
    } finally {
      setIsPreparingDownload(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Review Workspace"
        title="结果评审页"
        description="围绕最近一次执行结果做评审阅读。页面会先给结论摘要，再展开抽取结果、投标建议、标书初稿与引用知识。"
        actions={
          <div className="flex flex-wrap gap-3">
            {snapshot ? (
              <button
                className="ui-button-primary"
                type="button"
                onClick={handleDownloadDraft}
                disabled={isPreparingDownload}
              >
                {isPreparingDownload ? "准备下载中..." : "下载标书初稿"}
              </button>
            ) : null}
            <Link className="ui-button-secondary" href="/tender">
              返回招标处理
            </Link>
          </div>
        }
      />

      {!snapshot ? (
        <PanelCard title="暂无结果" description="当前还没有可审阅的执行结果。">
          <EmptyState
            title="请先执行一次主链路"
            description="上传页在完成上传、解析、抽取、判断和生成之后，会把最新结果写入本地缓存并在这里展示。"
            action={
              <Link className="ui-button-primary" href="/tender">
                前往招标处理
              </Link>
            }
          />
        </PanelCard>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="项目名称" value={snapshot.extract.project_name || "待识别"} helper="最近一次执行结果" tone="accent" />
            <MetricCard
              label="投标建议"
              value={snapshot.judge.should_bid ? "建议推进" : "谨慎评估"}
              helper={snapshot.judge.reason}
              tone={snapshot.judge.should_bid ? "success" : "warning"}
            />
            <MetricCard label="风险数量" value={String(snapshot.judge.risks.length)} helper="用于人工复核" />
            <MetricCard
              label="下载状态"
              value={downloadUrl ? "已就绪" : "可补生成"}
              helper={snapshot.generate.document_file_name || `执行时间：${uploadedAt}`}
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_360px]">
            <div className="space-y-6">
              <PanelCard title="标书初稿" description="初稿内容以文档阅读形式呈现，便于继续人工修改和补充。">
                <div className="space-y-5">
                  <section>
                    <p className="ui-field-label">公司介绍</p>
                    <pre className="ui-document-block mt-3">{snapshot.generate.company_intro}</pre>
                  </section>
                  <section>
                    <p className="ui-field-label">类似项目经验</p>
                    <pre className="ui-document-block mt-3">{snapshot.generate.project_cases}</pre>
                  </section>
                  <section>
                    <p className="ui-field-label">实施方案概述</p>
                    <pre className="ui-document-block mt-3">{snapshot.generate.implementation_plan}</pre>
                  </section>
                  <section>
                    <p className="ui-field-label">商务响应草稿</p>
                    <pre className="ui-document-block mt-3">{snapshot.generate.business_response}</pre>
                  </section>
                </div>
              </PanelCard>

              <PanelCard title="解析文本预览" description="用于核对原始文本解析结果，辅助判断抽取是否准确。">
                <pre className="ui-document-block">{snapshot.parse.text}</pre>
              </PanelCard>
            </div>

            <div className="space-y-6">
              <PanelCard title="核心字段抽取" description="先看结构化字段，再回到长文本核对抽取结果。">
                <div className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                    {extractSummary.map((item) => (
                      <div key={item.label} className="rounded-2xl border bg-surface px-4 py-4">
                        <p className="ui-field-label">{item.label}</p>
                        <p className="mt-3 text-sm font-semibold leading-6 text-ink">{item.value}</p>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-3 rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted">
                    <p>
                      <span className="font-semibold text-ink">资质要求：</span>
                      {snapshot.extract.qualification_requirements.join("；") || "未识别"}
                    </p>
                    <p>
                      <span className="font-semibold text-ink">交付要求：</span>
                      {snapshot.extract.delivery_requirements.join("；") || "未识别"}
                    </p>
                    <p>
                      <span className="font-semibold text-ink">评分重点：</span>
                      {snapshot.extract.scoring_focus.join("；") || "未识别"}
                    </p>
                  </div>
                </div>
              </PanelCard>

              <PanelCard title="投标建议" description="建议结果和风险提示应作为阅读初稿前的第一层判断依据。">
                <div className="space-y-4">
                  <div className="rounded-2xl border bg-surface px-4 py-4">
                    <p className="ui-field-label">建议结论</p>
                    <p className="mt-3 text-base font-semibold text-ink">
                      {snapshot.judge.should_bid ? "建议投标" : "建议谨慎评估"}
                    </p>
                    <p className="ui-copy mt-2">{snapshot.judge.reason}</p>
                  </div>
                  <div className="rounded-2xl border bg-surface px-4 py-4">
                    <p className="ui-field-label">风险提示</p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                      {(snapshot.judge.risks.length ? snapshot.judge.risks : ["暂无风险提示"]).map((risk) => (
                        <li key={risk}>- {risk}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </PanelCard>

              <PanelCard title="引用知识" description="作为判断和生成的证据区，便于确认当前结论引用了哪些资料片段。">
                {combinedKnowledge.length ? (
                  <div className="space-y-3">
                    {combinedKnowledge.map((item) => (
                      <article key={`${item.category}-${item.document_title}-${item.section_title}`} className="rounded-2xl border bg-surface px-4 py-4">
                        <p className="ui-field-label">{item.category}</p>
                        <p className="mt-3 text-sm font-semibold text-ink">{item.document_title}</p>
                        <p className="ui-help mt-1">{item.section_title}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="当前没有命中知识片段"
                    description="如果希望 judge 与 generate 输出更贴近企业实际，可以先去资料中心上传并处理相关文档。"
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
