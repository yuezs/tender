"use client";

import Link from "next/link";
import { CSSProperties, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import AppShell from "@/components/app-shell";
import AppModal from "@/components/ui/app-modal";
import EmptyState from "@/components/ui/empty-state";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import { cn } from "@/lib/cn";
import {
  generateTender,
  generateTenderFullDocument,
  generateTenderSection,
  getLatestTenderResult,
  getTenderResult,
  getTenderSectionContent,
  resolveApiUrl
} from "@/lib/api";
import {
  KnowledgeUsedItem,
  StepStatus,
  TenderFlowSnapshot,
  TenderResultSnapshot,
  TenderSectionContent,
  TenderSectionContentResponse
} from "@/types/tender";

type DisplayOutlineChild = {
  section_id: string;
  parent_section_id: string;
  title: string;
  purpose: string;
  writing_points: string[];
};

type DisplayOutlineChapter = {
  section_id: string;
  title: string;
  purpose: string;
  children: DisplayOutlineChild[];
};

type ContentModalState = TenderSectionContentResponse & {
  isLoading: boolean;
};

type BatchGenerationState = {
  running: boolean;
  total: number;
  completed: number;
  currentTitle: string;
  failedCount: number;
};

const statusTextMap: Record<StepStatus, string> = {
  pending: "待生成",
  loading: "生成中",
  success: "已完成",
  error: "生成失败"
};

const statusClassMap: Record<StepStatus, string> = {
  pending: "border-line bg-surface text-subtle",
  loading: "border-warning/20 bg-warning-soft text-warning",
  success: "border-success/20 bg-success-soft text-success",
  error: "border-danger/20 bg-danger-soft text-danger"
};

const stepLabelMap = {
  upload: "文件上传",
  parse: "文本解析",
  extract: "字段抽取",
  judge: "投标判断",
  generate: "目录生成"
} as const;

const TEN_LINE_CLAMP_STYLE: CSSProperties = {
  display: "-webkit-box",
  WebkitBoxOrient: "vertical",
  WebkitLineClamp: 10,
  overflow: "hidden"
};

function normalizeLegacySnapshot(snapshot: TenderFlowSnapshot): TenderResultSnapshot {
  return {
    uploaded_at: snapshot.uploadedAt,
    updated_at: snapshot.uploadedAt,
    upload: snapshot.upload,
    steps: {
      upload: { status: "success", message: "文件已上传" },
      parse: { status: "success", message: "文本解析完成" },
      extract: { status: "success", message: "字段抽取完成" },
      judge: { status: "success", message: "投标判断完成" },
      generate: { status: "success", message: "标书目录生成完成" }
    },
    parse: snapshot.parse,
    extract: snapshot.extract,
    judge: snapshot.judge,
    generate: {
      ...snapshot.generate,
      proposal_outline: snapshot.generate.proposal_outline ?? [],
      section_contents: snapshot.generate.section_contents ?? {}
    }
  };
}

function normalizeStringArray(value: unknown, limit = 5): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => String(item ?? "").trim())
    .filter(Boolean)
    .slice(0, limit);
}

function normalizeOutlineChild(raw: unknown, parentSectionId: string, index: number): DisplayOutlineChild | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }

  const payload = raw as Record<string, unknown>;
  const title = String(payload.title ?? "").trim();
  if (!title) {
    return null;
  }

  const sectionId = String(payload.section_id ?? `${parentSectionId}.${index + 1}`).trim() || `${parentSectionId}.${index + 1}`;
  return {
    section_id: sectionId,
    parent_section_id: parentSectionId,
    title,
    purpose: String(payload.purpose ?? "").trim() || "按当前小节目标生成对应正文。",
    writing_points: normalizeStringArray(payload.writing_points)
  };
}

function buildDisplayOutline(generate: TenderResultSnapshot["generate"]): {
  chapters: DisplayOutlineChapter[];
  supportsSectionGeneration: boolean;
} {
  const rawOutline = Array.isArray(generate.proposal_outline) ? (generate.proposal_outline as unknown[]) : [];
  const structuredChapters = rawOutline
    .map((raw, index) => {
      if (!raw || typeof raw !== "object") {
        return null;
      }

      const payload = raw as Record<string, unknown>;
      const title = String(payload.title ?? "").trim();
      if (!title) {
        return null;
      }

      const sectionId = String(payload.section_id ?? String(index + 1)).trim() || String(index + 1);
      const children = Array.isArray(payload.children)
        ? payload.children
            .map((child, childIndex) => normalizeOutlineChild(child, sectionId, childIndex))
            .filter((item): item is DisplayOutlineChild => Boolean(item))
        : [];

      return {
        section_id: sectionId,
        title,
        purpose: String(payload.purpose ?? "").trim() || "按当前目录逐节生成正文。",
        children
      };
    })
    .filter((item): item is DisplayOutlineChapter => Boolean(item));

  if (structuredChapters.length && structuredChapters.some((chapter) => chapter.children.length > 0)) {
    return {
      chapters: structuredChapters,
      supportsSectionGeneration: true
    };
  }

  const fallbackSections = [
    { section_id: "1", title: "公司介绍与能力响应", raw: generate.company_intro },
    { section_id: "2", title: "类似项目经验", raw: generate.project_cases },
    { section_id: "3", title: "技术实施方案", raw: generate.implementation_plan },
    { section_id: "4", title: "商务响应与附件", raw: generate.business_response }
  ];

  const fallbackChapters = fallbackSections.map((section) => ({
    section_id: section.section_id,
    title: section.title,
    purpose: "当前结果仍是旧版目录结构，请重新生成目录后再按小节生成正文。",
    children: [
      {
        section_id: `${section.section_id}.1`,
        parent_section_id: section.section_id,
        title: `${section.title}正文`,
        purpose: "当前内容仅用于展示旧结果摘要。",
        writing_points: section.raw
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean)
          .slice(0, 4)
      }
    ]
  }));

  return {
    chapters: fallbackChapters,
    supportsSectionGeneration: false
  };
}

function buildFallbackSectionContents(generate: TenderResultSnapshot["generate"]): Record<string, TenderSectionContent> {
  const contents = generate.section_contents ?? {};
  if (Object.keys(contents).length) {
    return contents;
  }

  const fallbackSections = [
    { section_id: "1.1", parent_section_id: "1", title: "公司介绍与能力响应正文", content: generate.company_intro },
    { section_id: "2.1", parent_section_id: "2", title: "类似项目经验正文", content: generate.project_cases },
    { section_id: "3.1", parent_section_id: "3", title: "技术实施方案正文", content: generate.implementation_plan },
    { section_id: "4.1", parent_section_id: "4", title: "商务响应与附件正文", content: generate.business_response }
  ];

  return fallbackSections.reduce<Record<string, TenderSectionContent>>((accumulator, section) => {
    if (!section.content.trim()) {
      return accumulator;
    }

    accumulator[section.section_id] = {
      section_id: section.section_id,
      parent_section_id: section.parent_section_id,
      title: section.title,
      status: "success",
      content: section.content,
      error_message: "",
      updated_at: "",
      knowledge_used: [],
      prompt_preview: ""
    };
    return accumulator;
  }, {});
}

function calculateProgress(chapters: DisplayOutlineChapter[], sectionContents: Record<string, TenderSectionContent>) {
  const total = chapters.reduce((sum, chapter) => sum + chapter.children.length, 0);
  const completed = chapters.reduce(
    (sum, chapter) => sum + chapter.children.filter((child) => sectionContents[child.section_id]?.status === "success").length,
    0
  );

  return {
    completed,
    total,
    percent: total ? Math.round((completed / total) * 100) : 0
  };
}

function calculateChapterProgress(chapter: DisplayOutlineChapter, sectionContents: Record<string, TenderSectionContent>) {
  const total = chapter.children.length;
  const completed = chapter.children.filter((child) => sectionContents[child.section_id]?.status === "success").length;
  const percent = total ? Math.round((completed / total) * 100) : 0;
  return { completed, total, percent };
}

function dedupeKnowledge(items: KnowledgeUsedItem[]) {
  return items.filter(
    (item, index, source) =>
      source.findIndex(
        (candidate) =>
          candidate.category === item.category &&
          candidate.document_title === item.document_title &&
          candidate.section_title === item.section_title
      ) === index
  );
}

function ProgressBar({ completed, total }: { completed: number; total: number }) {
  const percent = total ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-muted">
        <span>
          已完成 {completed}/{total || 0}
        </span>
        <span>{percent}%</span>
      </div>
      <div className="h-2 rounded-full bg-panel">
        <div className="h-2 rounded-full bg-success transition-all" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function ResultsPageContent() {
  const searchParams = useSearchParams();
  const [snapshot, setSnapshot] = useState<TenderResultSnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPreparingDownload, setIsPreparingDownload] = useState(false);
  const [isPreparingFullDownload, setIsPreparingFullDownload] = useState(false);
  const [pageMessage, setPageMessage] = useState("");
  const [sectionActionId, setSectionActionId] = useState("");
  const [activeModal, setActiveModal] = useState<ContentModalState | null>(null);
  const [isParsePreviewOpen, setIsParsePreviewOpen] = useState(false);
  const [batchState, setBatchState] = useState<BatchGenerationState>({
    running: false,
    total: 0,
    completed: 0,
    currentTitle: "",
    failedCount: 0
  });

  const fileId = searchParams.get("file_id")?.trim() || "";

  useEffect(() => {
    async function loadSnapshot() {
      setIsLoading(true);
      try {
        const nextSnapshot = fileId ? await getTenderResult(fileId) : await getLatestTenderResult();
        setSnapshot(nextSnapshot);
        setPageMessage(fileId ? "已加载当前文件的招标处理结果。" : "已加载最近一次招标处理结果。");
      } catch (error) {
        const raw = localStorage.getItem("latestTenderFlow");
        if (raw) {
          try {
            const localSnapshot = normalizeLegacySnapshot(JSON.parse(raw) as TenderFlowSnapshot);
            setSnapshot(localSnapshot);
            setPageMessage("后端结果暂不可用，当前展示的是本地缓存结果。");
            return;
          } catch {
            localStorage.removeItem("latestTenderFlow");
          }
        }

        const message = error instanceof Error ? error.message : "结果加载失败";
        setSnapshot(null);
        setPageMessage(message);
      } finally {
        setIsLoading(false);
      }
    }

    void loadSnapshot();
  }, [fileId]);

  const outlineState = useMemo(() => {
    if (!snapshot) {
      return {
        chapters: [] as DisplayOutlineChapter[],
        sectionContents: {} as Record<string, TenderSectionContent>,
        supportsSectionGeneration: false
      };
    }

    const displayOutline = buildDisplayOutline(snapshot.generate);
    return {
      chapters: displayOutline.chapters,
      sectionContents: buildFallbackSectionContents(snapshot.generate),
      supportsSectionGeneration: displayOutline.supportsSectionGeneration
    };
  }, [snapshot]);

  const overallProgress = useMemo(
    () => calculateProgress(outlineState.chapters, outlineState.sectionContents),
    [outlineState]
  );
  const remainingSections = useMemo(
    () =>
      outlineState.chapters.flatMap((chapter) =>
        chapter.children
          .filter((child) => outlineState.sectionContents[child.section_id]?.status !== "success")
          .map((child) => ({ chapterId: chapter.section_id, child }))
      ),
    [outlineState]
  );

  const extractSummary = useMemo(
    () =>
      snapshot
        ? [
            { label: "项目名称", value: snapshot.extract.project_name || "待识别" },
            { label: "招标单位", value: snapshot.extract.tender_company || "待识别" },
            { label: "预算金额", value: snapshot.extract.budget || "待识别" },
            { label: "截止时间", value: snapshot.extract.deadline || "待识别" }
          ]
        : [],
    [snapshot]
  );

  const combinedKnowledge = useMemo(() => {
    if (!snapshot) {
      return [];
    }

    return dedupeKnowledge([...(snapshot.judge.knowledge_used ?? []), ...(snapshot.generate.knowledge_used ?? [])]);
  }, [snapshot]);

  const uploadedAt = snapshot ? new Date(snapshot.uploaded_at).toLocaleString("zh-CN") : "";
  const updatedAt = snapshot ? new Date(snapshot.updated_at || snapshot.uploaded_at).toLocaleString("zh-CN") : "";
  const downloadUrl =
    snapshot?.generate.download_ready && snapshot.generate.download_url
      ? resolveApiUrl(snapshot.generate.download_url)
      : "";

  async function refreshCurrentSnapshot(currentFileId: string) {
    const nextSnapshot = await getTenderResult(currentFileId);
    setSnapshot(nextSnapshot);
    return nextSnapshot;
  }

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
      await generateTender(snapshot.upload.file_id);
      const refreshedSnapshot = await refreshCurrentSnapshot(snapshot.upload.file_id);
      const nextUrl =
        refreshedSnapshot.generate.download_ready && refreshedSnapshot.generate.download_url
          ? resolveApiUrl(refreshedSnapshot.generate.download_url)
          : "";

      if (!nextUrl) {
        throw new Error("目录已重新生成，但下载地址仍不可用。");
      }

      window.open(nextUrl, "_blank", "noopener,noreferrer");
      setPageMessage("目录文档已准备完成，可以直接下载。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "目录下载准备失败";
      window.alert(message);
    } finally {
      setIsPreparingDownload(false);
    }
  }

  async function handleDownloadFullDocument() {
    if (!snapshot || isPreparingFullDownload) {
      return;
    }

    setIsPreparingFullDownload(true);
    try {
      const documentPayload = await generateTenderFullDocument(snapshot.upload.file_id);
      window.open(resolveApiUrl(documentPayload.download_url), "_blank", "noopener,noreferrer");
      setPageMessage("全文 Word 已生成，可以直接下载。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "全文 Word 生成失败";
      window.alert(message);
    } finally {
      setIsPreparingFullDownload(false);
    }
  }

  async function handleOpenSection(sectionId: string, title: string) {
    if (!snapshot) {
      return;
    }

    setActiveModal({
      section_id: sectionId,
      parent_section_id: "",
      title,
      scope: "section",
      status: "loading",
      content: "",
      completed_children: 0,
      total_children: 0,
      isLoading: true
    });

    try {
      const content = await getTenderSectionContent(snapshot.upload.file_id, sectionId);
      setActiveModal({
        ...content,
        isLoading: false
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "章节内容加载失败";
      setActiveModal({
        section_id: sectionId,
        parent_section_id: "",
        title,
        scope: "section",
        status: "error",
        content: message,
        completed_children: 0,
        total_children: 0,
        isLoading: false
      });
    }
  }

  async function handleGenerateSection(chapterId: string, child: DisplayOutlineChild) {
    if (!snapshot || sectionActionId || batchState.running) {
      return;
    }

    if (!outlineState.supportsSectionGeneration) {
      setPageMessage("当前仍是旧版目录结果，请先重新生成目录，再按小节生成正文。");
      return;
    }

    setSectionActionId(child.section_id);
    setPageMessage(`正在生成 ${child.section_id} ${child.title} 的正文...`);
    setSnapshot((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        generate: {
          ...current.generate,
          section_contents: {
            ...(current.generate.section_contents ?? {}),
            [child.section_id]: {
              section_id: child.section_id,
              parent_section_id: chapterId,
              title: child.title,
              status: "loading",
              content: current.generate.section_contents?.[child.section_id]?.content ?? "",
              error_message: "",
              updated_at: new Date().toISOString(),
              knowledge_used: current.generate.section_contents?.[child.section_id]?.knowledge_used ?? [],
              prompt_preview: current.generate.section_contents?.[child.section_id]?.prompt_preview ?? ""
            }
          }
        }
      };
    });

    try {
      await generateTenderSection(snapshot.upload.file_id, child.section_id);
      await refreshCurrentSnapshot(snapshot.upload.file_id);
      setPageMessage(`${child.section_id} ${child.title} 已生成完成。`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "小节正文生成失败";
      try {
        await refreshCurrentSnapshot(snapshot.upload.file_id);
      } catch {
        // ignore refresh error
      }
      setPageMessage(message);
    } finally {
      setSectionActionId("");
    }
  }

  async function handleGenerateAllSections() {
    if (!snapshot || batchState.running || sectionActionId) {
      return;
    }

    if (!outlineState.supportsSectionGeneration) {
      setPageMessage("当前仍是旧版目录结果，请先重新生成目录，再按小节生成正文。");
      return;
    }

    if (!remainingSections.length) {
      setPageMessage("当前所有小节都已经生成完成。");
      return;
    }

    let successCount = 0;
    let failedCount = 0;
    setBatchState({
      running: true,
      total: remainingSections.length,
      completed: 0,
      currentTitle: remainingSections[0].child.title,
      failedCount: 0
    });
    setPageMessage(`准备连续生成 ${remainingSections.length} 个小节正文。`);

    for (const [index, target] of remainingSections.entries()) {
      setBatchState((current) => ({
        ...current,
        currentTitle: `${target.child.section_id} ${target.child.title}`,
        completed: successCount,
        failedCount
      }));

      setSectionActionId(target.child.section_id);
      setSnapshot((current) => {
        if (!current) {
          return current;
        }

        return {
          ...current,
          generate: {
            ...current.generate,
            section_contents: {
              ...(current.generate.section_contents ?? {}),
              [target.child.section_id]: {
                section_id: target.child.section_id,
                parent_section_id: target.chapterId,
                title: target.child.title,
                status: "loading",
                content: current.generate.section_contents?.[target.child.section_id]?.content ?? "",
                error_message: "",
                updated_at: new Date().toISOString(),
                knowledge_used: current.generate.section_contents?.[target.child.section_id]?.knowledge_used ?? [],
                prompt_preview: current.generate.section_contents?.[target.child.section_id]?.prompt_preview ?? ""
              }
            }
          }
        };
      });

      try {
        await generateTenderSection(snapshot.upload.file_id, target.child.section_id);
        await refreshCurrentSnapshot(snapshot.upload.file_id);
        successCount += 1;
        setPageMessage(`已完成 ${index + 1}/${remainingSections.length}：${target.child.section_id} ${target.child.title}`);
      } catch (error) {
        failedCount += 1;
        try {
          await refreshCurrentSnapshot(snapshot.upload.file_id);
        } catch {
          // ignore refresh failure and continue
        }
        const message = error instanceof Error ? error.message : "小节正文生成失败";
        setPageMessage(`生成 ${target.child.section_id} ${target.child.title} 失败：${message}`);
      } finally {
        setSectionActionId("");
        setBatchState((current) => ({
          ...current,
          completed: successCount,
          failedCount
        }));
      }
    }

    setBatchState({
      running: false,
      total: remainingSections.length,
      completed: successCount,
      currentTitle: "",
      failedCount
    });
    if (failedCount) {
      setPageMessage(`连续生成已完成：成功 ${successCount} 个，失败 ${failedCount} 个。`);
      return;
    }
    setPageMessage(`连续生成已完成，${successCount} 个小节全部生成成功。`);
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="结果审阅工作台"
        title="招标处理结果"
        description="先确认是否建议继续投标，再审阅关键字段、风险提示和正文生成进度，并进入下一步处理。"
        footer={
          <div className="flex flex-wrap gap-3">
            {snapshot ? (
              <button
                className="ui-button-primary"
                type="button"
                onClick={handleDownloadDraft}
                disabled={isPreparingDownload}
              >
                {isPreparingDownload ? "准备目录下载中..." : "下载标书目录"}
              </button>
            ) : null}
            {snapshot ? (
              <button
                className="ui-button-secondary"
                type="button"
                onClick={handleDownloadFullDocument}
                disabled={isPreparingFullDownload}
              >
                {isPreparingFullDownload ? "生成全文中..." : "下载全文 Word"}
              </button>
            ) : null}
            <Link className="ui-button-secondary" href={snapshot ? `/tender?file_id=${snapshot.upload.file_id}` : "/tender"}>
              返回招标处理
            </Link>
          </div>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard
              label="投标建议"
              value={snapshot ? (snapshot.judge.should_bid ? "建议推进" : "谨慎评估") : "待加载"}
              helper={snapshot ? `更新时间：${updatedAt}` : "等待结果加载"}
              tone={snapshot?.judge.should_bid ? "success" : "warning"}
            />
            <MetricCard
              label="正文进度"
              value={`${overallProgress.completed}/${overallProgress.total || 0}`}
              helper={`${overallProgress.percent}% 已完成`}
              tone={overallProgress.completed > 0 ? "accent" : "default"}
            />
          </div>
        }
      />

      <div className="ui-page-note mt-6">
        <p className="ui-field-label">当前提示</p>
        <p className="mt-2 text-sm leading-6 text-muted">{pageMessage || "当前页面优先展示后端结果。"}</p>
      </div>

      {isLoading ? (
        <div className="mt-6">
          <PanelCard title="结果加载中" description="正在读取最近一次招标处理结果。">
            <div className="rounded-lg border border-line bg-panel px-4 py-6 text-sm text-muted">请稍候...</div>
          </PanelCard>
        </div>
      ) : !snapshot ? (
        <div className="mt-6">
          <PanelCard title="暂无结果" description="当前还没有可查看的处理结果。">
            <EmptyState
              title="请先完成一次招标处理"
              description="上传并跑通主链路后，这里才会展示审阅结论、目录进度和正文查看入口。"
              action={
                <Link className="ui-button-primary" href="/tender">
                  前往招标处理
                </Link>
              }
            />
          </PanelCard>
        </div>
      ) : (
        <>
          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="项目名称" value={snapshot.extract.project_name || "待识别"} helper="来自字段抽取结果" tone="accent" />
            <MetricCard
              label="风险提示"
              value={`${snapshot.judge.risks.length} 项`}
              helper={snapshot.judge.risks[0] || "当前没有明显风险提示"}
              tone={snapshot.judge.risks.length ? "warning" : "success"}
            />
            <MetricCard
              label="知识引用"
              value={`${combinedKnowledge.length} 条`}
              helper={combinedKnowledge[0]?.document_title || "当前未命中知识片段"}
              tone={combinedKnowledge.length ? "accent" : "default"}
            />
            <MetricCard
              label="文档导出"
              value={downloadUrl ? "已就绪" : "待准备"}
              helper={snapshot.generate.document_file_name || `上传时间：${uploadedAt}`}
              tone={downloadUrl ? "success" : "default"}
            />
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_340px]">
            <div className="space-y-6">
              <PanelCard title="审阅结论" description="首屏先看结论、风险和下一步动作，再决定继续处理方式。">
                <div className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_320px]">
                  <div className="space-y-4">
                    <div className="ui-summary-card-accent">
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0 flex-1">
                          <p className="ui-field-label">结论摘要</p>
                          <div className="mt-3 flex flex-wrap items-center gap-3">
                            <span
                              className={cn(
                                "rounded-full border px-3 py-1 text-xs font-semibold",
                                snapshot.judge.should_bid
                                  ? "border-success/20 bg-success-soft text-success"
                                  : "border-warning/20 bg-warning-soft text-warning"
                              )}
                            >
                              {snapshot.judge.should_bid ? "建议推进投标" : "建议谨慎评估"}
                            </span>
                            <span className="text-sm text-muted">{snapshot.extract.project_name || "项目名称待识别"}</span>
                          </div>
                          <p className="mt-4 text-base font-semibold leading-7 text-ink">{snapshot.judge.reason}</p>
                        </div>
                        <div className="shrink-0 text-sm text-muted">
                          <p>最近更新</p>
                          <p className="mt-1 font-medium text-ink">{updatedAt}</p>
                        </div>
                      </div>
                    </div>

                    <div className="grid gap-4 lg:grid-cols-2">
                      <div className="ui-summary-card">
                        <p className="ui-field-label">风险提示</p>
                        <ul className="mt-4 space-y-3 text-sm leading-6 text-muted">
                          {(snapshot.judge.risks.length ? snapshot.judge.risks : ["当前没有明显风险提示"]).map((risk) => (
                            <li key={risk} className="flex gap-2">
                              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-warning" />
                              <span>{risk}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="ui-summary-card">
                        <p className="ui-field-label">后续动作</p>
                        <p className="mt-4 text-sm leading-6 text-muted">
                          {!outlineState.supportsSectionGeneration
                            ? "当前结果仍是旧版目录，建议先回到主链路重新生成目录，再继续正文处理。"
                            : remainingSections.length
                              ? `还有 ${remainingSections.length} 个小节待生成，建议先连续生成，再集中抽查章节内容。`
                              : downloadUrl
                                ? "目录与全文文档均可导出，下一步建议做最终校对并整理投标材料。"
                                : "正文已基本准备完成，下一步建议导出全文并做最终校对。"}
                        </p>
                        <div className="mt-5 flex flex-wrap gap-2">
                          {!outlineState.supportsSectionGeneration ? (
                            <Link className="ui-button-primary" href={`/tender?file_id=${snapshot.upload.file_id}`}>
                              返回重生目录
                            </Link>
                          ) : remainingSections.length ? (
                            <button
                              type="button"
                              className="ui-button-primary"
                              disabled={batchState.running || Boolean(sectionActionId)}
                              onClick={() => void handleGenerateAllSections()}
                            >
                              {batchState.running
                                ? `连续生成中 ${batchState.completed}/${batchState.total}`
                                : `继续生成剩余 ${remainingSections.length} 节`}
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="ui-button-primary"
                              onClick={handleDownloadFullDocument}
                              disabled={isPreparingFullDownload}
                            >
                              {isPreparingFullDownload ? "生成全文中..." : "导出全文 Word"}
                            </button>
                          )}
                          <button type="button" className="ui-button-secondary" onClick={() => setIsParsePreviewOpen(true)}>
                            查看解析全文
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="ui-summary-card">
                    <p className="ui-field-label">当前状态</p>
                    <div className="mt-4 space-y-4">
                      <div>
                        <p className="text-sm font-semibold text-ink">正文生成进度</p>
                        <div className="mt-3">
                          <ProgressBar completed={overallProgress.completed} total={overallProgress.total} />
                        </div>
                      </div>
                      <div className="border-t border-line pt-4">
                        <p className="text-sm font-semibold text-ink">目录可用性</p>
                        <p className="mt-2 text-sm leading-6 text-muted">
                          {outlineState.supportsSectionGeneration ? "当前目录支持按小节连续生成正文。" : "当前仍是旧版目录结果，暂不支持新的按节生成流程。"}
                        </p>
                      </div>
                      <div className="border-t border-line pt-4">
                        <p className="text-sm font-semibold text-ink">导出准备</p>
                        <p className="mt-2 text-sm leading-6 text-muted">
                          {downloadUrl ? "目录文档已可下载，全文 Word 可继续导出。" : "目录文档尚未准备完成，可先继续正文生成或重新准备下载。"}
                        </p>
                      </div>
                      {batchState.running ? (
                        <div className="rounded-md border border-accent/20 bg-accent/5 px-4 py-3 text-sm text-accent">
                          正在连续生成：{batchState.currentTitle || "准备中"}，已完成 {batchState.completed}/{batchState.total}
                        </div>
                      ) : batchState.total ? (
                        <div className="rounded-md border border-line bg-surface px-4 py-3 text-sm text-muted">
                          最近一次连续生成：成功 {batchState.completed} 节，失败 {batchState.failedCount} 节。
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              </PanelCard>

              <PanelCard
                title="标书目录与正文生成"
                description="按目录逐章审阅，并在需要时继续生成或重生成小节正文。"
                actions={
                  !outlineState.supportsSectionGeneration ? (
                    <span className="rounded-full border border-warning/20 bg-warning-soft px-3 py-1 text-xs font-semibold text-warning">
                      旧版目录结果
                    </span>
                  ) : remainingSections.length ? (
                    <button
                      type="button"
                      className="ui-button-primary"
                      disabled={batchState.running || Boolean(sectionActionId)}
                      onClick={() => void handleGenerateAllSections()}
                    >
                      {batchState.running ? `连续生成中 ${batchState.completed}/${batchState.total}` : `生成剩余 ${remainingSections.length} 节`}
                    </button>
                  ) : (
                    <span className="rounded-full border border-success/20 bg-success-soft px-3 py-1 text-xs font-semibold text-success">
                      正文已全部生成
                    </span>
                  )
                }
              >
                <div className="space-y-4">
                  <div className="ui-inset grid gap-4 px-4 py-4 lg:grid-cols-[minmax(0,1fr)_260px]">
                    <div>
                      <p className="ui-field-label">目录处理说明</p>
                      <p className="mt-3 text-sm leading-6 text-muted">
                        先看章节目的和撰写要点，再按需查看正文或继续生成。主流程保持连续，不额外拆分业务步骤。
                      </p>
                    </div>
                    <div className="space-y-3">
                      <ProgressBar completed={overallProgress.completed} total={overallProgress.total} />
                      <p className="text-xs leading-5 text-muted">
                        {remainingSections.length
                          ? `当前还有 ${remainingSections.length} 个小节未完成。`
                          : "当前所有小节都已生成完成。"}
                      </p>
                    </div>
                  </div>

                  <div className="overflow-hidden rounded-lg border border-line bg-panel">
                    {outlineState.chapters.map((chapter, chapterIndex) => {
                      const chapterProgress = calculateChapterProgress(chapter, outlineState.sectionContents);

                      return (
                        <section
                          key={chapter.section_id}
                          className={cn("px-4 py-5 sm:px-5", chapterIndex > 0 && "border-t border-line")}
                        >
                          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                            <div className="min-w-0 flex-1">
                              <button
                                type="button"
                                className="cursor-pointer text-left"
                                onClick={() => void handleOpenSection(chapter.section_id, chapter.title)}
                              >
                                <p className="text-sm font-semibold leading-6 text-ink">
                                  {chapter.section_id} {chapter.title}
                                </p>
                              </button>
                              <p className="mt-2 text-sm leading-6 text-muted">{chapter.purpose}</p>
                            </div>
                            <div className="w-full lg:max-w-52">
                              <ProgressBar completed={chapterProgress.completed} total={chapterProgress.total} />
                            </div>
                          </div>

                          <div className="mt-4 overflow-hidden rounded-lg border border-line bg-surface">
                            {chapter.children.map((child, childIndex) => {
                              const sectionState = outlineState.sectionContents[child.section_id];
                              const sectionStatus = sectionState?.status ?? "pending";
                              const isSectionLoading = sectionActionId === child.section_id || sectionStatus === "loading";

                              return (
                                <div
                                  key={child.section_id}
                                  className={cn("px-4 py-4", childIndex > 0 && "border-t border-line")}
                                >
                                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                                    <div className="min-w-0 flex-1">
                                      <div className="flex flex-wrap items-center gap-2">
                                        <button
                                          type="button"
                                          className="cursor-pointer text-left text-sm font-semibold leading-6 text-ink"
                                          onClick={() => void handleOpenSection(child.section_id, child.title)}
                                        >
                                          {child.section_id} {child.title}
                                        </button>
                                        <span
                                          className={cn(
                                            "rounded-full border px-2.5 py-1 text-[11px] font-semibold",
                                            statusClassMap[sectionStatus]
                                          )}
                                        >
                                          {statusTextMap[sectionStatus]}
                                        </span>
                                      </div>
                                      <p className="mt-2 text-sm leading-6 text-muted">{child.purpose}</p>
                                      {child.writing_points.length ? (
                                        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                                          {child.writing_points.slice(0, 3).map((point) => (
                                            <li key={`${child.section_id}-${point}`} className="flex gap-2">
                                              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-line-strong" />
                                              <span>{point}</span>
                                            </li>
                                          ))}
                                        </ul>
                                      ) : null}
                                      {sectionState?.error_message ? (
                                        <p className="mt-3 text-xs leading-5 text-danger">{sectionState.error_message}</p>
                                      ) : null}
                                    </div>

                                    <div className="flex shrink-0 flex-wrap gap-2 xl:justify-end">
                                      <button
                                        type="button"
                                        className="ui-button-ghost"
                                        onClick={() => void handleOpenSection(child.section_id, child.title)}
                                      >
                                        查看正文
                                      </button>
                                      <button
                                        type="button"
                                        className="ui-button-primary"
                                        disabled={Boolean(sectionActionId) || batchState.running || !outlineState.supportsSectionGeneration}
                                        onClick={() => void handleGenerateSection(chapter.section_id, child)}
                                      >
                                        {isSectionLoading ? "生成中..." : sectionStatus === "success" ? "重新生成" : "生成正文"}
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </section>
                      );
                    })}
                  </div>
                </div>
              </PanelCard>

              <PanelCard title="解析文本预览" description="用于核对原始文本解析结果，辅助判断目录和关键字段是否可信。">
                <button
                  type="button"
                  className="block w-full text-left"
                  onClick={() => setIsParsePreviewOpen(true)}
                  title="点击查看全文"
                >
                  <pre className="ui-document-block transition hover:border-accent/30 hover:bg-panel" style={TEN_LINE_CLAMP_STYLE}>
                    {snapshot.parse.text}
                  </pre>
                </button>
                <p className="mt-3 text-sm leading-6 text-muted">默认仅展示前 10 行，点击文本区域可查看全文。</p>
              </PanelCard>
            </div>

            <div className="space-y-6">
              <PanelCard title="处理状态" description="用于快速确认各阶段是否成功完成，以及当前结果是否适合继续使用。">
                <div className="overflow-hidden rounded-lg border border-line bg-panel">
                  {(["upload", "parse", "extract", "judge", "generate"] as const).map((step, index) => (
                    <div
                      key={step}
                      className={cn("flex items-start justify-between gap-4 px-4 py-4", index > 0 && "border-t border-line")}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="ui-field-label">{stepLabelMap[step]}</p>
                        <p className="mt-2 text-sm leading-6 text-muted">{snapshot.steps[step].message}</p>
                      </div>
                      <span
                        className={cn(
                          "shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold",
                          statusClassMap[snapshot.steps[step].status]
                        )}
                      >
                        {statusTextMap[snapshot.steps[step].status]}
                      </span>
                    </div>
                  ))}
                </div>
              </PanelCard>

              <PanelCard title="核心字段" description="先核对结构化字段，再结合风险提示和正文内容做最终判断。">
                <div className="space-y-4">
                  <div className="overflow-hidden rounded-lg border border-line bg-panel">
                    {extractSummary.map((item, index) => (
                      <div key={item.label} className={cn("px-4 py-4", index > 0 && "border-t border-line")}>
                        <p className="ui-field-label">{item.label}</p>
                        <p className="mt-3 text-sm font-semibold leading-6 text-ink">{item.value}</p>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-lg border border-line bg-panel px-4 py-4">
                    <p className="ui-field-label">资质要求</p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                      {(snapshot.extract.qualification_requirements.length
                        ? snapshot.extract.qualification_requirements
                        : ["未识别"]).map((item) => (
                        <li key={item} className="flex gap-2">
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-line-strong" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-lg border border-line bg-panel px-4 py-4">
                    <p className="ui-field-label">交付要求</p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                      {(snapshot.extract.delivery_requirements.length ? snapshot.extract.delivery_requirements : ["未识别"]).map(
                        (item) => (
                          <li key={item} className="flex gap-2">
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-line-strong" />
                            <span>{item}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>

                  <div className="rounded-lg border border-line bg-panel px-4 py-4">
                    <p className="ui-field-label">评分重点</p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                      {(snapshot.extract.scoring_focus.length ? snapshot.extract.scoring_focus : ["未识别"]).map((item) => (
                        <li key={item} className="flex gap-2">
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-line-strong" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </PanelCard>

              <PanelCard title="引用知识" description="用于确认当前判断和正文生成引用了哪些企业资料片段。">
                {combinedKnowledge.length ? (
                  <div className="overflow-hidden rounded-lg border border-line bg-panel">
                    {combinedKnowledge.map((item, index) => (
                      <article
                        key={`${item.category}-${item.document_title}-${item.section_title}`}
                        className={cn("px-4 py-4", index > 0 && "border-t border-line")}
                      >
                        <p className="ui-field-label">{item.category}</p>
                        <p className="mt-2 text-sm font-semibold leading-6 text-ink">{item.document_title}</p>
                        <p className="mt-1 text-sm leading-6 text-muted">{item.section_title}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="当前没有命中知识片段"
                    description="如果希望目录和正文更贴近企业实际，可以先去资料中心上传并处理相关文档。"
                  />
                )}
              </PanelCard>
            </div>
          </div>
        </>
      )}

      <AppModal
        open={Boolean(activeModal)}
        onClose={() => setActiveModal(null)}
        eyebrow={activeModal?.scope === "chapter" ? "章节正文" : "小节正文"}
        title={activeModal?.title ?? ""}
        description={
          activeModal?.scope === "chapter"
            ? `已完成 ${activeModal.completed_children}/${activeModal.total_children} 个小节`
            : ""
        }
        maxWidthClassName="max-w-4xl"
        bodyClassName="max-h-[calc(90vh-96px)] overflow-y-auto px-6 py-5"
      >
        {activeModal?.isLoading ? (
          <div className="rounded-lg border border-line bg-panel px-4 py-6 text-sm text-muted">正在加载正文内容...</div>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={cn(
                  "rounded-full border px-2.5 py-1 text-[11px] font-semibold",
                  statusClassMap[activeModal?.status ?? "pending"]
                )}
              >
                {statusTextMap[activeModal?.status ?? "pending"]}
              </span>
            </div>
            <div className="whitespace-pre-wrap rounded-lg border border-line bg-panel px-4 py-4 text-sm leading-7 text-ink">
              {activeModal?.content ?? ""}
            </div>
          </div>
        )}
      </AppModal>

      <AppModal
        open={isParsePreviewOpen}
        onClose={() => setIsParsePreviewOpen(false)}
        eyebrow="解析文本全文"
        title="解析文本预览"
        maxWidthClassName="max-w-5xl"
      >
        <pre className="whitespace-pre-wrap break-words text-sm leading-7 text-muted">{snapshot?.parse.text ?? ""}</pre>
      </AppModal>
    </AppShell>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<AppShell><div /></AppShell>}>
      <ResultsPageContent />
    </Suspense>
  );
}
