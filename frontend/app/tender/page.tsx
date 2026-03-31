"use client";

import Link from "next/link";
import { ChangeEvent, useMemo, useState } from "react";

import AppShell from "@/components/app-shell";
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

  return (
    <AppShell>
      <section className="panel">
        <span className="badge">Tender Flow</span>
        <h1>招标上传页</h1>
        <p>当前页面已接入 MVP 主链路，可执行上传、解析、抽取、判断、生成的最小闭环。</p>

        <div className="upload-area">
          <strong>上传区域</strong>
          <p className="muted">当前优先支持 txt / docx。pdf 可上传，但解析接口会返回预留提示。</p>
          <input className="file-input" type="file" accept=".txt,.docx,.pdf" onChange={handleFileChange} />
          <div className="upload-actions">
            <button className="button" type="button" onClick={handleUploadOnly} disabled={!canRun}>
              仅上传
            </button>
            <button className="button button-secondary" type="button" onClick={handleRunPipeline} disabled={!canRun}>
              上传并运行主链路
            </button>
            <Link className="button button-secondary" href="/results">
              查看结果页
            </Link>
          </div>
          {pageMessage ? <p className="status-message">{pageMessage}</p> : null}
        </div>

        <div className="status-list">
          {(Object.keys(stepLabels) as StepKey[]).map((step) => (
            <div className="status-item" key={step}>
              <div>
                <strong>{stepLabels[step]}</strong>
                <p className="muted step-message">{steps[step].message}</p>
              </div>
              <span className={`status-pill state-${steps[step].status}`}>{steps[step].status}</span>
            </div>
          ))}
        </div>

        {latestResult ? (
          <div className="placeholder-box">
            <h2 className="section-title">最新结果摘要</h2>
            <p className="muted">项目名称：{latestResult.extract.project_name || "待识别"}</p>
            <p className="muted">是否建议投标：{latestResult.judge.should_bid ? "建议" : "谨慎评估"}</p>
            <p className="muted">风险数：{latestResult.judge.risks.length}</p>
          </div>
        ) : null}
      </section>
    </AppShell>
  );
}
