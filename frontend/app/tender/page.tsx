"use client";

import Link from "next/link";
import { ChangeEvent, useMemo, useState } from "react";

import AppShell from "@/components/app-shell";
import EmptyState from "@/components/ui/empty-state";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import StatusTimeline from "@/components/ui/status-timeline";
import { cn } from "@/lib/cn";
import { extractTender, generateTender, judgeTender, parseTender, uploadTenderFile } from "@/lib/api";
import { StepState, TenderFlowSnapshot } from "@/types/tender";

type StepKey = "upload" | "parse" | "extract" | "judge" | "generate";

const stepLabels: Record<StepKey, string> = {
  upload: "文件上传",
  parse: "文本解析",
  extract: "字段抽取",
  judge: "投标判断",
  generate: "初稿生成"
};

const initialSteps: Record<StepKey, StepState> = {
  upload: { status: "pending", message: "等待上传文件" },
  parse: { status: "pending", message: "等待解析" },
  extract: { status: "pending", message: "等待抽取" },
  judge: { status: "pending", message: "等待判断" },
  generate: { status: "pending", message: "等待生成" }
};

const workflowOrder: StepKey[] = ["upload", "parse", "extract", "judge", "generate"];

const stepBadgeClassMap = {
  pending: "border-line/80 bg-surface text-subtle",
  loading: "border-warning/20 bg-warning-soft text-warning",
  success: "border-success/20 bg-success-soft text-success",
  error: "border-danger/20 bg-danger-soft text-danger"
} as const;

const stepStatusTextMap = {
  pending: "待处理",
  loading: "进行中",
  success: "已完成",
  error: "失败"
} as const;

const workflowStepDescriptions: Record<StepKey, string> = {
  upload: "保存原文件并建立处理入口",
  parse: "读取文本内容并生成可审阅预览",
  extract: "抽取项目名称、预算、截止时间等关键字段",
  judge: "结合规则与知识资料生成投标建议",
  generate: "生成标书目录和初稿内容"
};

export default function TenderPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFileId, setUploadedFileId] = useState("");
  const [steps, setSteps] = useState(initialSteps);
  const [latestResult, setLatestResult] = useState<TenderFlowSnapshot | null>(null);
  const [pageMessage, setPageMessage] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  const canRun = useMemo(() => Boolean(selectedFile) && !isRunning, [selectedFile, isRunning]);
  const completedSteps = useMemo(
    () => (Object.values(steps) as StepState[]).filter((step) => step.status === "success").length,
    [steps]
  );
  const hasError = useMemo(
    () => (Object.values(steps) as StepState[]).some((step) => step.status === "error"),
    [steps]
  );
  const currentBannerTone = hasError ? "danger" : latestResult ? "success" : selectedFile ? "accent" : "default";
  const latestFileId = latestResult?.upload.file_id || uploadedFileId;
  const resultsHref = latestFileId ? `/results?file_id=${latestFileId}` : "/results";
  const progressPercent = Math.round((completedSteps / 5) * 100);

  function updateStep(step: StepKey, nextState: StepState) {
    setSteps((current) => ({
      ...current,
      [step]: nextState
    }));
  }

  function resetFollowingSteps(from: Exclude<StepKey, "generate">) {
    const order: StepKey[] = ["upload", "parse", "extract", "judge", "generate"];
    const index = order.indexOf(from);
    setSteps((current) => {
      const next = { ...current };
      for (let i = index + 1; i < order.length; i += 1) {
        next[order[i]] = initialSteps[order[i]];
      }
      return next;
    });
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setUploadedFileId("");
    setLatestResult(null);
    localStorage.removeItem("latestTenderFlow");
    setPageMessage(file ? `已选择文件：${file.name}` : "");
    setSteps(initialSteps);
  }

  async function ensureUploadedFile() {
    if (uploadedFileId) {
      return uploadedFileId;
    }

    if (!selectedFile) {
      throw new Error("请先选择一个 txt、docx 或 pdf 文件。");
    }

    updateStep("upload", { status: "loading", message: "正在上传文件..." });
    const uploadResult = await uploadTenderFile(selectedFile);
    setUploadedFileId(uploadResult.file_id);
    updateStep("upload", {
      status: "success",
      message: `上传成功：${uploadResult.file_name}`
    });
    return uploadResult.file_id;
  }

  async function handleUploadOnly() {
    setPageMessage("");
    setIsRunning(true);

    try {
      await ensureUploadedFile();
      resetFollowingSteps("upload");
      setPageMessage("文件已上传。现在可以继续执行解析、判断和生成链路。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "上传失败";
      updateStep("upload", { status: "error", message });
      setPageMessage(message);
    } finally {
      setIsRunning(false);
    }
  }

  async function handleRunPipeline() {
    setPageMessage("");
    setIsRunning(true);
    let activeStep: StepKey = "upload";
    resetFollowingSteps("upload");
    setLatestResult(null);
    localStorage.removeItem("latestTenderFlow");

    try {
      const fileId = await ensureUploadedFile();

      activeStep = "parse";
      updateStep("parse", { status: "loading", message: "正在解析文本..." });
      const parseResult = await parseTender(fileId);
      updateStep("parse", { status: "success", message: "文本解析完成" });

      activeStep = "extract";
      updateStep("extract", { status: "loading", message: "正在抽取关键字段..." });
      const extractResult = await extractTender(fileId);
      updateStep("extract", { status: "success", message: "字段抽取完成" });

      activeStep = "judge";
      updateStep("judge", { status: "loading", message: "正在生成投标建议..." });
      const judgeResult = await judgeTender(fileId);
      updateStep("judge", { status: "success", message: "投标建议已生成" });

      activeStep = "generate";
      updateStep("generate", { status: "loading", message: "正在生成标书初稿..." });
      const generateResult = await generateTender(fileId);
      updateStep("generate", { status: "success", message: "标书初稿已生成" });

      const snapshot: TenderFlowSnapshot = {
        uploadedAt: new Date().toISOString(),
        upload: {
          file_id: fileId,
          file_name: selectedFile?.name ?? "unknown",
          source_type: "upload",
          extension: selectedFile ? selectedFile.name.split(".").pop() ?? "" : ""
        },
        parse: parseResult,
        extract: extractResult,
        judge: judgeResult,
        generate: generateResult
      };

      localStorage.setItem("latestTenderFlow", JSON.stringify(snapshot));
      setLatestResult(snapshot);
      setPageMessage("主链路执行完成，可以进入结果页继续审阅结构化结果、投标结论和初稿内容。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "主链路执行失败";
      updateStep(activeStep, { status: "error", message });
      setPageMessage(message);
    } finally {
      setIsRunning(false);
    }
  }

  function bannerClassName() {
    if (currentBannerTone === "danger") {
      return "border-danger/20 bg-danger-soft text-danger";
    }
    if (currentBannerTone === "success") {
      return "border-success/20 bg-success-soft text-success";
    }
    if (currentBannerTone === "accent") {
      return "border-accent/20 bg-accent-soft text-accent";
    }
    return "border-line/70 bg-surface text-muted";
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Tender Executive Demo"
        title="招标处理工作台"
        description="围绕单个招标文件完成上传、解析、字段抽取、投标判断与初稿生成。当前页面用于发起主链路、确认处理状态，并衔接到结果审阅。"
        actions={
          <>
            <Link className="ui-button-secondary" href={resultsHref}>
              查看结果页
            </Link>
            <button className="ui-button-primary" type="button" onClick={handleRunPipeline} disabled={!canRun}>
              {isRunning ? "处理中..." : uploadedFileId ? "继续执行主链路" : "上传并运行主链路"}
            </button>
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="主链路进度" value={`${completedSteps}/5`} helper="固定处理顺序" tone="accent" />
            <MetricCard
              label="当前文件"
              value={selectedFile ? selectedFile.name.split(".").pop()?.toUpperCase() ?? "已选择" : "未选择"}
              helper={selectedFile ? selectedFile.name : "请选择招标文件"}
              tone={selectedFile ? "default" : "warning"}
            />
          </div>
        }
      />

      <div aria-live="polite" className={cn("ui-page-note", bannerClassName())}>
        {pageMessage || "请选择招标文件后发起处理。主链路会按上传、解析、抽取、判断、生成的固定顺序执行。"}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_360px]">
        <div className="space-y-6">
          <PanelCard
            title="当前任务"
            description="先选文件，再直接开始主链路。这里保留一个主操作和两个次操作，不再堆叠重复说明。"
          >
            <div className="space-y-5">
              <label
                htmlFor="tender-file"
                className="block cursor-pointer rounded-2xl border border-dashed border-accent/35 bg-accent-soft px-6 py-7 transition-colors duration-200 hover:border-accent/55 hover:bg-panel"
              >
                <input id="tender-file" className="sr-only" type="file" accept=".txt,.docx,.pdf" onChange={handleFileChange} />
                <div className="space-y-3">
                  <p className="ui-field-label">文件选择</p>
                  <p className="text-[28px] font-semibold leading-9 text-ink">
                    {selectedFile ? `已选择：${selectedFile.name}` : "点击选择招标文件"}
                  </p>
                  <p className="text-sm leading-6 text-muted">
                    {selectedFile
                      ? `文件大小约 ${(selectedFile.size / 1024).toFixed(1)} KB。上传后会继续进入解析、抽取、判断和生成。`
                      : "支持 txt / docx / pdf。演示优先推荐 txt、docx，以保证处理结果更稳定。"}
                  </p>
                  <div className="flex flex-wrap gap-2 pt-1">
                    <span className="rounded-full border border-line/70 bg-panel px-2.5 py-1 text-xs text-muted">TXT / DOCX / PDF</span>
                    <span className="rounded-full border border-line/70 bg-panel px-2.5 py-1 text-xs text-muted">
                      {isRunning ? "主链路执行中" : uploadedFileId ? "已上传，可继续处理" : "等待上传"}
                    </span>
                    {uploadedFileId ? (
                      <span className="rounded-full border border-line/70 bg-panel px-2.5 py-1 text-xs text-muted">
                        文件 ID：{uploadedFileId}
                      </span>
                    ) : null}
                  </div>
                </div>
              </label>

              <div className="rounded-2xl border border-line/70 bg-panel px-5 py-5 shadow-panel">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="ui-field-label">主操作</p>
                    <p className="mt-2 text-base font-semibold text-ink">
                      {selectedFile ? "上传文件并直接开始主链路" : "先选文件，再一键开始处理"}
                    </p>
                    <p className="mt-2 text-sm leading-6 text-muted">
                      主按钮会优先执行完整主链路；“仅上传”只用于先留档后处理。
                    </p>
                  </div>
                  <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap lg:justify-end">
                    <button className="ui-button-primary min-w-[220px]" type="button" onClick={handleRunPipeline} disabled={!canRun}>
                      {isRunning ? "处理中..." : "上传文件并开始处理"}
                    </button>
                    <button className="ui-button-secondary" type="button" onClick={handleUploadOnly} disabled={!canRun}>
                      仅上传
                    </button>
                    <Link className="ui-button-ghost" href={resultsHref}>
                      查看结果
                    </Link>
                  </div>
                </div>
              </div>

              <div className="space-y-3 border-t border-line/70 pt-5">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <p className="ui-field-label">主链路顺序</p>
                  <p className="ui-help">上传 → 解析 → 抽取 → 判断 → 生成</p>
                </div>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                  {workflowOrder.map((stepKey) => {
                    const state = steps[stepKey];
                    return (
                      <div key={stepKey} className="rounded-2xl border border-line/70 bg-panel px-4 py-4 shadow-panel">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm font-semibold text-ink">{stepLabels[stepKey]}</p>
                          <span className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${stepBadgeClassMap[state.status]}`}>
                            {stepStatusTextMap[state.status]}
                          </span>
                        </div>
                        <p className="mt-2 text-xs leading-5 text-subtle">{workflowStepDescriptions[stepKey]}</p>
                        <p className="mt-3 text-xs leading-5 text-subtle">{state.message}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </PanelCard>

          <PanelCard
            title="最近一次处理摘要"
            description="用于快速判断这份文件是否已经具备继续进入结果页审阅的条件。"
          >
            {latestResult ? (
              <div className="space-y-5">
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <MetricCard label="项目名称" value={latestResult.extract.project_name || "待识别"} helper="来自字段抽取结果" tone="accent" />
                  <MetricCard
                    label="投标建议"
                    value={latestResult.judge.should_bid ? "建议推进" : "谨慎评估"}
                    helper={latestResult.judge.reason}
                    tone={latestResult.judge.should_bid ? "success" : "warning"}
                  />
                  <MetricCard label="风险数量" value={String(latestResult.judge.risks.length)} helper="用于人工复核" />
                  <MetricCard
                    label="知识引用"
                    value={String(latestResult.generate.knowledge_used?.length ?? 0)}
                    helper="judge / generate 汇总"
                    tone="accent"
                  />
                </div>

                <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
                  <div className="ui-summary-card-accent">
                    <p className="ui-field-label">当前摘要</p>
                    <p className="mt-3 text-xl font-semibold leading-8 text-ink">
                      主链路已完成，可以直接切入结果审阅。
                    </p>
                    <p className="mt-3 text-sm leading-6 text-muted">
                      当前已经拿到项目名称、投标建议、风险提示与知识引用数量。下一步建议进入结果页，集中查看解析文本、结构化字段、投标结论、目录与正文内容。
                    </p>
                    <div className="mt-5 rounded-2xl border border-line/60 bg-panel px-4 py-4 shadow-panel">
                      <p className="ui-field-label">当前文件</p>
                      <p className="mt-2 text-sm font-semibold text-ink">{latestResult.upload.file_name}</p>
                      <p className="mt-2 text-xs leading-5 text-subtle">文件 ID：{latestResult.upload.file_id}</p>
                    </div>
                  </div>

                  <div className="ui-summary-card">
                    <p className="ui-field-label">下一步</p>
                    <p className="mt-2 text-base font-semibold text-ink">进入结果页继续审阅</p>
                    <p className="mt-3 text-sm leading-6 text-muted">
                      当前页负责发起主链路和确认整体进度；处理完成后，建议在结果页集中审阅字段、结论和初稿内容。
                    </p>
                    <div className="mt-5">
                      <Link className="ui-button-primary w-full" href={resultsHref}>
                        前往结果页
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState
                title="还没有可用结果"
                description="完成一次主链路后，这里会汇总项目名称、投标建议、风险数量和知识引用，方便你决定是否进入结果页。"
              />
            )}
          </PanelCard>
        </div>

        <div className="space-y-6">
          <PanelCard
            title="主链路进度"
            description="用于持续确认当前文件在主链路中的推进情况，并帮助判断下一步该继续处理还是转入审阅。"
          >
            <div className="space-y-5">
              <div className="ui-summary-card">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="ui-field-label">整体进度</p>
                    <p className="mt-2 text-lg font-semibold text-ink">{completedSteps} / 5 步已完成</p>
                  </div>
                  <p className="text-lg font-semibold text-ink">{progressPercent}%</p>
                </div>
                <div className="mt-4 h-2 rounded-full bg-inset">
                  <div className="h-2 rounded-full bg-accent transition-all duration-200" style={{ width: `${progressPercent}%` }} />
                </div>
              </div>

              <StatusTimeline
                steps={workflowOrder.map((step) => ({
                  key: step,
                  label: stepLabels[step],
                  state: steps[step]
                }))}
              />
            </div>
          </PanelCard>

          <PanelCard
            title="使用说明"
            description="保持连续操作时，优先看输入边界、结果去向和按钮状态。"
            muted
          >
            <div className="divide-y divide-line/70">
              <div className="pb-4">
                <p className="text-sm font-semibold text-ink">输入边界</p>
                <p className="mt-2 text-sm leading-6 text-muted">
                  优先上传内容结构清晰的 txt 或 docx 文件。pdf 当前也可上传，但解析结果更适合作为预留展示。
                </p>
              </div>
              <div className="py-4">
                <p className="text-sm font-semibold text-ink">结果去向</p>
                <p className="mt-2 text-sm leading-6 text-muted">
                  当前页负责发起主链路和确认整体进度；处理完成后，建议进入结果页集中审阅字段、结论和初稿内容。
                </p>
              </div>
              <div className="pt-4">
                <p className="text-sm font-semibold text-ink">按钮状态</p>
                <p className="mt-2 text-sm leading-6 text-muted">
                  {!selectedFile
                    ? "未选择文件时，执行按钮保持禁用。"
                    : isRunning
                      ? "处理进行中时，按钮保持禁用，避免重复提交。"
                      : "当前可以继续上传，或直接执行完整主链路。"}
                </p>
              </div>
            </div>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
