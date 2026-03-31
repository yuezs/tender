"use client";

import Link from "next/link";
import { ChangeEvent, useMemo, useState } from "react";

import AppShell from "@/components/app-shell";
import EmptyState from "@/components/ui/empty-state";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import StatusTimeline from "@/components/ui/status-timeline";
import { extractTender, generateTender, judgeTender, parseTender, uploadTenderFile } from "@/lib/api";
import { StepState, TenderFlowSnapshot } from "@/types/tender";

type StepKey = "upload" | "parse" | "extract" | "judge" | "generate";

const stepLabels: Record<StepKey, string> = {
  upload: "文件上传",
  parse: "文本解析",
  extract: "字段抽取",
  judge: "投标判断",
  generate: "标书生成"
};

const initialSteps: Record<StepKey, StepState> = {
  upload: { status: "pending", message: "等待上传文件" },
  parse: { status: "pending", message: "等待解析" },
  extract: { status: "pending", message: "等待抽取" },
  judge: { status: "pending", message: "等待判断" },
  generate: { status: "pending", message: "等待生成" }
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
      setPageMessage("文件已上传。现在可以继续执行解析和生成链路。");
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
      updateStep("extract", { status: "loading", message: "正在抽取核心字段..." });
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
      setPageMessage("主链路执行完成，可以进入结果页查看完整输出。");
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
    return "border-line bg-surface text-muted";
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Tender Workspace"
        title="招标处理工作台"
        description="围绕单个招标文件完成上传、解析、字段抽取、投标判断与标书初稿生成。当前重点是让动作反馈、流程状态和最近结果都足够清晰。"
        actions={
          <>
            <Link className="ui-button-secondary" href="/results">
              查看结果页
            </Link>
            <button className="ui-button-primary" type="button" onClick={handleRunPipeline} disabled={!canRun}>
              {isRunning ? "处理中..." : uploadedFileId ? "继续执行主链路" : "上传并运行主链路"}
            </button>
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="已完成步骤" value={`${completedSteps}/5`} helper="按固定主链路执行" tone="accent" />
            <MetricCard
              label="当前文件"
              value={selectedFile ? selectedFile.name.split(".").pop()?.toUpperCase() ?? "已选" : "未选择"}
              helper={selectedFile ? selectedFile.name : "请选择招标文件"}
              tone={selectedFile ? "default" : "warning"}
            />
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.32fr)_360px]">
        <div className="space-y-6">
          <PanelCard
            title="文件上传"
            description="当前优先支持 txt / docx，pdf 入口已保留但解析仍会返回预留提示。"
          >
            <div className="space-y-5">
              <label
                htmlFor="tender-file"
                className="block cursor-pointer rounded-3xl border border-dashed border-line-strong bg-surface p-5 transition hover:border-accent/40 hover:bg-accent-soft/40"
              >
                <input id="tender-file" className="sr-only" type="file" accept=".txt,.docx,.pdf" onChange={handleFileChange} />
                <p className="ui-field-label">文件选择</p>
                <p className="mt-3 text-base font-semibold text-ink">
                  {selectedFile ? `已选择：${selectedFile.name}` : "点击选择招标文件"}
                </p>
                <p className="ui-copy mt-2">
                  {selectedFile
                    ? `文件大小约 ${(selectedFile.size / 1024).toFixed(1)} KB。上传后会按固定主链路进入解析、判断与生成。`
                    : "建议先上传文本质量较好的招标文件，以便后续抽取和结果评审更稳定。"}
                </p>
              </label>

              <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
                <button className="ui-button-primary" type="button" onClick={handleRunPipeline} disabled={!canRun}>
                  {isRunning ? "处理中..." : "上传并运行主链路"}
                </button>
                <button className="ui-button-secondary" type="button" onClick={handleUploadOnly} disabled={!canRun}>
                  仅上传
                </button>
                <Link className="ui-button-ghost" href="/results">
                  查看结果
                </Link>
              </div>

              <div aria-live="polite" className={`rounded-2xl border px-4 py-3 text-sm leading-6 ${bannerClassName()}`}>
                {pageMessage || "尚未开始处理。选择文件后，系统会按固定顺序执行上传、解析、抽取、判断和生成。"}
              </div>
            </div>
          </PanelCard>

          <PanelCard
            title="最近一次执行摘要"
            description="用于快速判断是否需要进入结果页继续阅读或回到当前页重新处理。"
          >
            {latestResult ? (
              <div className="space-y-5">
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <MetricCard label="项目名称" value={latestResult.extract.project_name || "待识别"} helper="来自抽取结果" />
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
                <div className="rounded-2xl border bg-surface px-4 py-4">
                  <p className="ui-field-label">当前摘要</p>
                  <p className="ui-copy mt-3">
                    已完成最近一次主链路执行。你可以直接进入结果页继续审阅抽取结果、投标建议、标书初稿和知识引用。
                  </p>
                </div>
              </div>
            ) : (
              <EmptyState
                title="还没有可用结果"
                description="当前页面会在主链路完成后，把项目名称、投标建议、风险数量和知识引用摘要整理在这里。"
              />
            )}
          </PanelCard>
        </div>

        <div className="space-y-6">
          <PanelCard
            title="处理状态"
            description="状态轨道用于描述当前文件在固定主链路中的推进情况。未执行步骤会保持等待态。"
          >
            <StatusTimeline
              steps={(Object.keys(stepLabels) as StepKey[]).map((step) => ({
                key: step,
                label: stepLabels[step],
                state: steps[step]
              }))}
            />
          </PanelCard>

          <PanelCard
            title="工作提示"
            description="用于提醒当前页面的输入边界和结果阅读方式。"
            muted
          >
            <div className="space-y-4">
              <div className="rounded-2xl border bg-panel px-4 py-4">
                <p className="text-sm font-semibold text-ink">建议输入</p>
                <p className="ui-help mt-2">优先上传内容结构清晰的 txt / docx 文件。PDF 当前可上传，但解析接口仍会给出预留提示。</p>
              </div>
              <div className="rounded-2xl border bg-panel px-4 py-4">
                <p className="text-sm font-semibold text-ink">结果阅读</p>
                <p className="ui-help mt-2">处理完成后建议进入结果页审阅结论、风险、初稿文本与引用知识，而不是只看当前页摘要。</p>
              </div>
              <div className="rounded-2xl border bg-panel px-4 py-4">
                <p className="text-sm font-semibold text-ink">按钮状态</p>
                <p className="ui-help mt-2">{!selectedFile ? "未选择文件时，执行按钮保持禁用。" : isRunning ? "处理中时，按钮保持禁用，避免重复提交。" : "当前已可执行上传或完整主链路。"}</p>
              </div>
            </div>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
