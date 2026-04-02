"use client";

import { ChangeEvent, MouseEvent, useEffect, useMemo, useState } from "react";

import AppShell from "@/components/app-shell";
import MetricCard from "@/components/ui/metric-card";
import PanelCard from "@/components/ui/panel-card";
import {
  deleteKnowledgeDocument,
  getKnowledgeDocumentContent,
  getKnowledgeDocumentDownloadUrl,
  listKnowledgeDocuments,
  processKnowledgeDocument,
  retrieveKnowledge,
  uploadKnowledgeDocument
} from "@/lib/api";
import {
  KnowledgeDocumentContentResponse,
  KnowledgeCategory,
  KnowledgeChunkItem,
  KnowledgeDocumentItem,
  KnowledgeDocumentStatus,
  ProcessKnowledgeDocumentResponse
} from "@/types/knowledge";

const categories = [
  { title: "公司介绍", code: "company_profile" },
  { title: "资质证书", code: "qualifications" },
  { title: "项目案例", code: "project_cases" },
  { title: "模板素材", code: "templates" }
] as const;

const categoryOptions = categories.map((item) => item.code) as KnowledgeCategory[];
const categoryLabelMap = Object.fromEntries(categories.map((item) => [item.code, item.title])) as Record<
  KnowledgeCategory,
  string
>;

const statusOptions: Array<KnowledgeDocumentStatus | ""> = ["", "uploaded", "processed", "error"];
const statusLabelMap: Record<KnowledgeDocumentStatus, string> = {
  uploaded: "待处理",
  processed: "已处理",
  error: "处理失败"
};

const EMPTY_PARSE_SUMMARY = {
  block_count: 0,
  heading_count: 0,
  paragraph_count: 0,
  list_item_count: 0,
  table_row_count: 0,
  character_count: 0,
  line_count: 0
} as const;

function normalizeCsvList(raw: string) {
  return raw
    .split(/[，,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function truncateText(value: string, maxLength = 180) {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength)}...`;
}

function formatDateTime(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("zh-CN", { hour12: false });
}

function getStatusLabel(status: KnowledgeDocumentStatus) {
  return statusLabelMap[status] ?? status;
}

function getContentSourceLabel(source: string) {
  if (source === "parsed_text") {
    return "解析文本";
  }
  if (source === "raw_file") {
    return "原始文件解析";
  }
  return source;
}

function normalizeProcessResult(
  result: Partial<ProcessKnowledgeDocumentResponse> | null | undefined
): ProcessKnowledgeDocumentResponse | null {
  if (!result) {
    return null;
  }

  return {
    document_id: result.document_id ?? "",
    chunk_count: result.chunk_count ?? 0,
    status: result.status ?? "processed",
    content_length: result.content_length ?? 0,
    parse_summary: {
      block_count: result.parse_summary?.block_count ?? 0,
      heading_count: result.parse_summary?.heading_count ?? 0,
      paragraph_count: result.parse_summary?.paragraph_count ?? 0,
      list_item_count: result.parse_summary?.list_item_count ?? 0,
      table_row_count: result.parse_summary?.table_row_count ?? 0,
      character_count: result.parse_summary?.character_count ?? 0,
      line_count: result.parse_summary?.line_count ?? 0
    },
    warnings: Array.isArray(result.warnings) ? result.warnings : [],
    key_points: Array.isArray(result.key_points) ? result.key_points : [],
    chunk_preview: Array.isArray(result.chunk_preview) ? result.chunk_preview : []
  };
}

export default function KnowledgePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadCategory, setUploadCategory] = useState<KnowledgeCategory>("company_profile");
  const [uploadTags, setUploadTags] = useState("");
  const [uploadIndustry, setUploadIndustry] = useState("");
  const [autoProcess, setAutoProcess] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [pageMessage, setPageMessage] = useState("");
  const [lastProcessResult, setLastProcessResult] = useState<ProcessKnowledgeDocumentResponse | null>(null);

  const [filterCategory, setFilterCategory] = useState<KnowledgeCategory | "">("");
  const [filterStatus, setFilterStatus] = useState<KnowledgeDocumentStatus | "">("");
  const [documents, setDocuments] = useState<KnowledgeDocumentItem[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [processingId, setProcessingId] = useState("");
  const [viewingContentId, setViewingContentId] = useState("");
  const [viewingDocument, setViewingDocument] = useState<KnowledgeDocumentContentResponse | null>(null);
  const [deletingId, setDeletingId] = useState("");

  const [retrieveCategory, setRetrieveCategory] = useState<KnowledgeCategory | "">("");
  const [retrieveQuery, setRetrieveQuery] = useState("");
  const [retrieveTags, setRetrieveTags] = useState("");
  const [retrieveIndustry, setRetrieveIndustry] = useState("");
  const [retrieveLimit, setRetrieveLimit] = useState(5);
  const [retrieving, setRetrieving] = useState(false);
  const [retrievedChunks, setRetrievedChunks] = useState<KnowledgeChunkItem[]>([]);
  const [selectedRetrievedChunk, setSelectedRetrievedChunk] = useState<KnowledgeChunkItem | null>(null);

  const processedCount = useMemo(
    () => documents.filter((item) => item.status === "processed").length,
    [documents]
  );
  const uploadedCount = useMemo(
    () => documents.filter((item) => item.status === "uploaded").length,
    [documents]
  );

  const latestParseSummary = lastProcessResult?.parse_summary ?? EMPTY_PARSE_SUMMARY;
  const latestWarnings = lastProcessResult?.warnings ?? [];
  const latestKeyPoints = lastProcessResult?.key_points ?? [];
  const latestChunkPreview = lastProcessResult?.chunk_preview ?? [];
  const latestWarningCount = latestWarnings.length;

  async function refreshDocuments(nextFilters?: {
    category?: KnowledgeCategory | "";
    status?: KnowledgeDocumentStatus | "";
  }) {
    setLoadingList(true);
    try {
      const response = await listKnowledgeDocuments({
        category: nextFilters?.category ?? filterCategory,
        status: nextFilters?.status ?? filterStatus
      });
      setDocuments(response.items);
    } catch (error) {
      const message = error instanceof Error ? error.message : "获取资料列表失败";
      setPageMessage(message);
    } finally {
      setLoadingList(false);
    }
  }

  useEffect(() => {
    refreshDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function scrollToSection(sectionId: string) {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setLastProcessResult(null);
    if (file && !uploadTitle.trim()) {
      setUploadTitle(file.name.replace(/\.[^/.]+$/, ""));
    }
  }

  async function handleUpload() {
    setPageMessage("");
    setLastProcessResult(null);

    if (!selectedFile) {
      setPageMessage("请先选择一个 txt 或 docx 文件。");
      return;
    }

    if (!uploadTitle.trim()) {
      setPageMessage("资料标题不能为空。");
      return;
    }

    setUploading(true);
    try {
      const result = await uploadKnowledgeDocument({
        file: selectedFile,
        title: uploadTitle.trim(),
        category: uploadCategory,
        tags: uploadTags.trim() || undefined,
        industry: uploadIndustry.trim() || undefined
      });

      setPageMessage(`上传成功：${result.title}`);
      setSelectedFile(null);

      const fileInput = document.getElementById("knowledge-file") as HTMLInputElement | null;
      if (fileInput) {
        fileInput.value = "";
      }

      if (autoProcess) {
        setProcessingId(result.document_id);
        const processResult = await processKnowledgeDocument(result.document_id);
        const normalized = normalizeProcessResult(processResult);
        setLastProcessResult(normalized);
        setPageMessage(`上传并处理完成：${result.title}，共生成 ${normalized?.chunk_count ?? 0} 个知识块。`);
      }

      await refreshDocuments();
    } catch (error) {
      const message = error instanceof Error ? error.message : "上传失败";
      setPageMessage(message);
    } finally {
      setUploading(false);
      setProcessingId("");
    }
  }

  async function handleProcess(documentId: string) {
    setPageMessage("");
    setProcessingId(documentId);
    try {
      const result = await processKnowledgeDocument(documentId);
      const normalized = normalizeProcessResult(result);
      setLastProcessResult(normalized);
      setPageMessage(`处理完成，共生成 ${normalized?.chunk_count ?? 0} 个知识块。`);
      await refreshDocuments();
    } catch (error) {
      const message = error instanceof Error ? error.message : "处理失败";
      setPageMessage(message);
    } finally {
      setProcessingId("");
    }
  }

  function closeActionMenu(event: MouseEvent<HTMLElement>) {
    const details = event.currentTarget.closest("details");
    if (details instanceof HTMLDetailsElement) {
      details.open = false;
    }
  }

  async function handleViewDocument(item: KnowledgeDocumentItem) {
    setPageMessage("");
    setViewingContentId(item.document_id);
    try {
      const result = await getKnowledgeDocumentContent(item.document_id);
      setViewingDocument(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : "全文查看失败";
      setPageMessage(message);
    } finally {
      setViewingContentId("");
    }
  }

  function handleDownloadDocument(documentId: string) {
    setPageMessage("开始下载资料文件。");
    const downloadUrl = getKnowledgeDocumentDownloadUrl(documentId);
    window.open(downloadUrl, "_blank", "noopener,noreferrer");
  }

  async function handleDeleteDocument(item: KnowledgeDocumentItem) {
    const shouldDelete = window.confirm(`确认删除资料“${item.title}”吗？删除后将同时移除原文件、解析文本和知识块。`);
    if (!shouldDelete) {
      return;
    }

    setPageMessage("");
    setDeletingId(item.document_id);
    try {
      const result = await deleteKnowledgeDocument(item.document_id);
      if (viewingDocument?.document_id === item.document_id) {
        setViewingDocument(null);
      }
      if (lastProcessResult?.document_id === item.document_id) {
        setLastProcessResult(null);
      }
      setPageMessage(`删除成功：${result.title}`);
      await refreshDocuments();
    } catch (error) {
      const message = error instanceof Error ? error.message : "删除资料失败";
      setPageMessage(message);
    } finally {
      setDeletingId("");
    }
  }

  async function handleRetrieve() {
    setPageMessage("");
    setRetrieving(true);
    try {
      const response = await retrieveKnowledge({
        category: retrieveCategory,
        query: retrieveQuery.trim(),
        tags: normalizeCsvList(retrieveTags),
        industry: normalizeCsvList(retrieveIndustry),
        limit: Math.min(Math.max(retrieveLimit, 1), 20)
      });
      setRetrievedChunks(response.chunks);
      setPageMessage(`检索完成：命中 ${response.chunks.length} 条知识片段。`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "检索失败";
      setPageMessage(message);
    } finally {
      setRetrieving(false);
    }
  }

  return (
    <AppShell>
      <section className="ui-panel relative overflow-hidden px-5 py-6 sm:px-7 sm:py-7">
        <div className="absolute inset-x-0 top-0 h-1 bg-accent/70" />
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_360px]">
          <div className="space-y-5">
            <div>
              <p className="ui-kicker">企业知识库</p>
              <h1 className="ui-page-title mt-3">资料中心</h1>
              <p className="ui-copy mt-3 max-w-2xl">
                统一管理公司资料的上传、解析、处理和检索，当前聚焦资料入库、规则切块和简单检索闭环。
              </p>
            </div>

            <div className="rounded-3xl border border-accent/15 bg-gradient-to-br from-accent-soft via-panel to-panel p-5 shadow-panel">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="ui-field-label text-accent">资料流程</p>
                  <p className="mt-2 text-lg font-semibold text-ink">上传 → 处理 → 检索</p>
                  <p className="ui-copy mt-2">
                    原文件、解析文本和知识块统一沉淀，方便后续在招投标流程中引用。
                  </p>
                </div>
                <div className="rounded-2xl border border-accent/20 bg-white/70 px-3 py-2 text-right shadow-sm">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-subtle">支持格式</p>
                  <p className="mt-1 text-sm font-semibold text-ink">TXT / DOCX</p>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {["资料入库", "规则切块", "处理预览", "简单检索"].map((item) => (
                  <span
                    key={item}
                    className="rounded-full border border-accent/15 bg-white/70 px-3 py-1 text-xs font-medium text-muted"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3 lg:items-end">
            <div className="flex w-full flex-wrap gap-3 lg:w-auto lg:justify-end">
              <button className="ui-button-secondary" type="button" onClick={() => scrollToSection("knowledge-upload")}>
                上传资料
              </button>
              <button className="ui-button-secondary" type="button" onClick={() => scrollToSection("knowledge-retrieve")}>
                检索调试
              </button>
            </div>

            <div className="grid w-full grid-cols-2 gap-3">
              <MetricCard label="资料分类" value="4 类" helper="固定分类，按当前 MVP 范围执行" tone="accent" />
              <MetricCard
                label="已处理文档"
                value={`${processedCount}/${documents.length}`}
                helper={uploadedCount ? `待处理 ${uploadedCount} 份` : "当前没有待处理文档"}
                tone={uploadedCount ? "warning" : "default"}
              />
              <MetricCard
                label="最近块数"
                value={lastProcessResult ? String(lastProcessResult.chunk_count) : "-"}
                helper="最近一次处理结果"
                tone={lastProcessResult ? "success" : "default"}
              />
              <MetricCard
                label="最近告警"
                value={String(latestWarningCount)}
                helper={lastProcessResult ? "解析与切块质量提示" : "等待资料处理"}
                tone={latestWarningCount ? "warning" : "default"}
              />
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_360px]">
        <div className="space-y-6">
          <div id="knowledge-upload">
            <PanelCard title="资料上传" description="支持上传 txt / docx 文件，并可在上传后立即执行解析和切块。">
            <div className="space-y-5">
              <label
                htmlFor="knowledge-file"
                className="block cursor-pointer rounded-3xl border border-dashed border-line-strong bg-surface p-5 transition hover:border-accent/40 hover:bg-accent-soft/40"
              >
                <input
                  id="knowledge-file"
                  className="sr-only"
                  type="file"
                  accept=".txt,.docx"
                  onChange={handleFileChange}
                  disabled={uploading}
                />
                <p className="ui-field-label">文件选择</p>
                <p className="mt-3 text-base font-semibold text-ink">
                  {selectedFile ? `已选择：${selectedFile.name}` : "点击选择资料文件（txt / docx）"}
                </p>
                <p className="ui-copy mt-2">
                  {selectedFile
                    ? `文件大小约 ${(selectedFile.size / 1024).toFixed(1)} KB`
                    : "建议上传公司介绍、资质证书、项目案例和模板素材等可复用资料。"}
                </p>
              </label>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-2">
                  <span className="ui-field-label">资料标题</span>
                  <input
                    className="ui-input"
                    value={uploadTitle}
                    onChange={(event) => setUploadTitle(event.target.value)}
                    placeholder="例如：公司介绍 2026 版"
                    disabled={uploading}
                  />
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">资料分类</span>
                  <select
                    className="ui-input"
                    value={uploadCategory}
                    onChange={(event) => setUploadCategory(event.target.value as KnowledgeCategory)}
                    disabled={uploading}
                  >
                    {categoryOptions.map((category) => (
                      <option key={category} value={category}>
                        {categoryLabelMap[category]}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">标签（可选）</span>
                  <input
                    className="ui-input"
                    value={uploadTags}
                    onChange={(event) => setUploadTags(event.target.value)}
                    placeholder="逗号分隔，例如：政务，智慧城市"
                    disabled={uploading}
                  />
                  <span className="ui-help">用于列表筛选和简单检索。</span>
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">行业（可选）</span>
                  <input
                    className="ui-input"
                    value={uploadIndustry}
                    onChange={(event) => setUploadIndustry(event.target.value)}
                    placeholder="逗号分隔，例如：政务，环保"
                    disabled={uploading}
                  />
                  <span className="ui-help">用于规则过滤和下游检索命中。</span>
                </label>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <label className="flex items-center gap-2 text-sm text-muted">
                  <input
                    type="checkbox"
                    checked={autoProcess}
                    onChange={(event) => setAutoProcess(event.target.checked)}
                    disabled={uploading}
                  />
                  上传后立即处理（解析 + 切块）
                </label>

                <button className="ui-button-primary" type="button" onClick={handleUpload} disabled={uploading}>
                  {uploading ? "上传中..." : "上传资料"}
                </button>
              </div>

              <div aria-live="polite" className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm leading-6 text-muted">
                {pageMessage || "上传后的原文件会保存到 storage/knowledge/raw/，处理完成后会写入知识文档和知识块表。"}{" "}
                {processingId ? <span className="text-accent">正在处理：{processingId}</span> : null}
              </div>
            </div>
            </PanelCard>
          </div>

          <PanelCard title="资料列表" description="支持按分类和状态筛选，并查看每份资料的处理状态、块数和错误信息。">
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-[220px_200px_auto]">
                <label className="space-y-2">
                  <span className="ui-field-label">分类筛选</span>
                  <select
                    className="ui-input"
                    value={filterCategory}
                    onChange={(event) => {
                      const value = event.target.value as KnowledgeCategory | "";
                      setFilterCategory(value);
                      refreshDocuments({ category: value });
                    }}
                    disabled={loadingList}
                  >
                    <option value="">全部分类</option>
                    {categoryOptions.map((category) => (
                      <option key={category} value={category}>
                        {categoryLabelMap[category]}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">状态筛选</span>
                  <select
                    className="ui-input"
                    value={filterStatus}
                    onChange={(event) => {
                      const value = event.target.value as KnowledgeDocumentStatus | "";
                      setFilterStatus(value);
                      refreshDocuments({ status: value });
                    }}
                    disabled={loadingList}
                  >
                    {statusOptions.map((status) => (
                      <option key={status || "all"} value={status}>
                        {status ? getStatusLabel(status) : "全部状态"}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="flex items-end justify-end">
                  <button className="ui-button-secondary" type="button" onClick={() => refreshDocuments()} disabled={loadingList}>
                    {loadingList ? "刷新中..." : "刷新列表"}
                  </button>
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-line bg-surface">
                <table className="w-full table-fixed text-sm">
                  <colgroup>
                    <col className="w-[18%]" />
                    <col className="w-[16%]" />
                    <col className="w-[12%]" />
                    <col className="w-[16%]" />
                    <col className="w-[22%]" />
                    <col className="w-[16%]" />
                  </colgroup>
                  <thead className="border-b border-line bg-canvas text-xs uppercase tracking-wide text-subtle">
                    <tr>
                      <th className="px-4 py-3">标题</th>
                      <th className="px-4 py-3 text-center whitespace-nowrap">分类</th>
                      <th className="px-4 py-3 text-center whitespace-nowrap">状态</th>
                      <th className="px-4 py-3 text-center whitespace-nowrap">切块数</th>
                      <th className="px-4 py-3 text-center whitespace-nowrap">更新时间</th>
                      <th className="px-4 py-3 text-center whitespace-nowrap">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {documents.length ? (
                      documents.map((item: KnowledgeDocumentItem) => {
                        const canProcess = item.status === "uploaded" || item.status === "error";
                        const busy = processingId === item.document_id;

                        return (
                          <tr key={item.document_id} className="align-top text-muted">
                            <td className="px-4 py-3 text-center align-middle">
                              <p className="mx-auto max-w-[8ch] truncate font-semibold text-ink" title={item.title}>
                                {truncateText(item.title, 8)}
                              </p>
                              {item.error_message ? (
                                <p className="mt-2 rounded-xl bg-danger-soft px-2 py-1 text-xs text-danger">{item.error_message}</p>
                              ) : null}
                            </td>
                            <td className="px-4 py-3 text-center align-middle whitespace-nowrap">
                              <p>{categoryLabelMap[item.category]}</p>
                            </td>
                            <td className="px-4 py-3 text-center align-middle whitespace-nowrap">
                              {getStatusLabel(item.status)}
                            </td>
                            <td className="px-4 py-3 text-center align-middle whitespace-nowrap">
                              <p className="text-sm font-medium text-ink">
                                {item.chunk_count} 块 / <span className="text-xs text-subtle">{item.content_length} 字符</span>
                              </p>
                            </td>
                            <td className="px-4 py-3 text-center align-middle text-xs text-subtle whitespace-nowrap">
                              {formatDateTime(item.updated_at)}
                            </td>
                            <td className="px-4 py-3 text-center align-middle whitespace-nowrap">
                              <details className="relative inline-block text-left">
                                <summary className="ui-button-ghost list-none cursor-pointer px-3 py-2">
                                  操作
                                </summary>
                                <div className="absolute right-0 z-20 mt-2 min-w-[148px] rounded-2xl border border-line bg-white p-2 shadow-panel">
                                  <div className="space-y-1">
                                    <button
                                      className="flex w-full items-center justify-center rounded-xl px-3 py-2 text-sm text-muted transition hover:bg-accent-soft hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
                                      type="button"
                                      onClick={(event) => {
                                        closeActionMenu(event);
                                        handleViewDocument(item);
                                      }}
                                      disabled={viewingContentId === item.document_id}
                                    >
                                      {viewingContentId === item.document_id ? "加载中..." : "全文查看"}
                                    </button>
                                    <button
                                      className="flex w-full items-center justify-center rounded-xl px-3 py-2 text-sm text-muted transition hover:bg-accent-soft hover:text-ink"
                                      type="button"
                                      onClick={(event) => {
                                        closeActionMenu(event);
                                        handleDownloadDocument(item.document_id);
                                      }}
                                    >
                                      文件下载
                                    </button>
                                    {canProcess ? (
                                      <button
                                        className="flex w-full items-center justify-center rounded-xl px-3 py-2 text-sm text-muted transition hover:bg-accent-soft hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
                                        type="button"
                                        onClick={(event) => {
                                          closeActionMenu(event);
                                          handleProcess(item.document_id);
                                        }}
                                        disabled={busy || uploading}
                                      >
                                        {busy ? "处理中..." : "处理"}
                                      </button>
                                    ) : null}
                                    <button
                                      className="flex w-full items-center justify-center rounded-xl px-3 py-2 text-sm text-danger transition hover:bg-danger-soft disabled:cursor-not-allowed disabled:opacity-50"
                                      type="button"
                                      onClick={(event) => {
                                        closeActionMenu(event);
                                        handleDeleteDocument(item);
                                      }}
                                      disabled={deletingId === item.document_id}
                                    >
                                      {deletingId === item.document_id ? "删除中..." : "删除"}
                                    </button>
                                  </div>
                                </div>
                              </details>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={6} className="px-4 py-10 text-center text-sm text-muted">
                          {loadingList ? "正在加载..." : "暂无资料，请先上传一份文档。"}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </PanelCard>
        </div>

        <div className="space-y-6">
          <PanelCard title="最近处理结果" description="用于快速确认解析质量、处理告警和切块效果。">
            {lastProcessResult ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <MetricCard label="知识块" value={String(lastProcessResult.chunk_count ?? 0)} helper="最近一次处理结果" tone="success" />
                  <MetricCard label="字数" value={String(lastProcessResult.content_length ?? 0)} helper="解析后的文本长度" />
                </div>

                <div className="rounded-2xl border border-line bg-surface px-4 py-4">
                  <p className="ui-field-label">解析摘要</p>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-muted">
                    <p>结构块：{latestParseSummary.block_count}</p>
                    <p>标题数：{latestParseSummary.heading_count}</p>
                    <p>段落数：{latestParseSummary.paragraph_count}</p>
                    <p>列表项：{latestParseSummary.list_item_count}</p>
                    <p>表格行：{latestParseSummary.table_row_count}</p>
                    <p>有效行：{latestParseSummary.line_count}</p>
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-surface px-4 py-4">
                  <p className="ui-field-label">重点内容</p>
                  {latestKeyPoints.length ? (
                    <ul className="mt-3 space-y-2 text-sm text-muted">
                      {latestKeyPoints.map((point) => (
                        <li key={point} className="rounded-xl bg-accent-soft px-3 py-2 text-ink">
                          {point}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="ui-copy mt-3">当前还没有提取到重点内容。</p>
                  )}
                </div>

                <div className="rounded-2xl border border-line bg-surface px-4 py-4">
                  <p className="ui-field-label">处理告警</p>
                  {latestWarnings.length ? (
                    <ul className="mt-3 space-y-2 text-sm text-warning">
                      {latestWarnings.map((warning) => (
                        <li key={warning} className="rounded-xl bg-warning-soft px-3 py-2">
                          {warning}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="ui-copy mt-3">当前没有处理告警。</p>
                  )}
                </div>

                <div className="rounded-2xl border border-line bg-surface px-4 py-4">
                  <p className="ui-field-label">切块预览</p>
                  <div className="mt-3 space-y-3">
                    {latestChunkPreview.length ? (
                      latestChunkPreview.map((chunk, index) => (
                        <article key={`${chunk.section_title}-${index}`} className="ui-panel-muted px-3 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-sm font-semibold text-ink">{chunk.section_title}</p>
                            <span className="text-xs text-subtle">{chunk.char_count} 字符</span>
                          </div>
                          <p className="ui-copy mt-2 whitespace-pre-wrap break-words">{chunk.content_preview}</p>
                        </article>
                      ))
                    ) : (
                      <p className="ui-copy">暂无可预览的知识块。</p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-line bg-surface px-4 py-6 text-sm text-muted">
                还没有最近一次处理结果。上传并处理资料后，这里会展示解析摘要、告警信息和前几个知识块预览。
              </div>
            )}
          </PanelCard>

          <div id="knowledge-retrieve">
            <PanelCard title="检索调试" description="用于验证资料处理后的知识块是否能被关键词、标签和行业条件命中。">
            <div className="space-y-4">
              <label className="space-y-2">
                <span className="ui-field-label">资料分类（可选）</span>
                <select
                  className="ui-input"
                  value={retrieveCategory}
                  onChange={(event) => setRetrieveCategory(event.target.value as KnowledgeCategory | "")}
                  disabled={retrieving}
                >
                  <option value="">全部分类</option>
                  {categoryOptions.map((category) => (
                    <option key={category} value={category}>
                      {categoryLabelMap[category]}
                    </option>
                  ))}
                </select>
              </label>

              <label className="space-y-2">
                <span className="ui-field-label">关键词（可选）</span>
                <input
                  className="ui-input"
                  value={retrieveQuery}
                  onChange={(event) => setRetrieveQuery(event.target.value)}
                  placeholder="例如：软件企业证书"
                  disabled={retrieving}
                />
              </label>

              <label className="space-y-2">
                <span className="ui-field-label">标签（可选）</span>
                <input
                  className="ui-input"
                  value={retrieveTags}
                  onChange={(event) => setRetrieveTags(event.target.value)}
                  placeholder="逗号分隔"
                  disabled={retrieving}
                />
              </label>

              <label className="space-y-2">
                <span className="ui-field-label">行业（可选）</span>
                <input
                  className="ui-input"
                  value={retrieveIndustry}
                  onChange={(event) => setRetrieveIndustry(event.target.value)}
                  placeholder="逗号分隔"
                  disabled={retrieving}
                />
              </label>

              <label className="space-y-2">
                <span className="ui-field-label">返回条数</span>
                <input
                  className="ui-input"
                  type="number"
                  value={retrieveLimit}
                  onChange={(event) => setRetrieveLimit(Number(event.target.value))}
                  min={1}
                  max={20}
                  disabled={retrieving}
                />
              </label>

              <button className="ui-button-primary w-full" type="button" onClick={handleRetrieve} disabled={retrieving}>
                {retrieving ? "检索中..." : "开始检索"}
              </button>

              <div className="space-y-3">
                {retrievedChunks.length ? (
                  retrievedChunks.map((chunk) => (
                    <button
                      key={chunk.id}
                      type="button"
                      className="ui-panel-muted block w-full px-4 py-4 text-left transition hover:border-accent/30 hover:bg-accent-soft/40"
                      onClick={() => setSelectedRetrievedChunk(chunk)}
                    >
                      <p className="ui-field-label truncate" title={chunk.document_title}>
                        {chunk.document_title}
                      </p>
                      <p className="mt-2 truncate text-sm font-semibold text-ink" title={chunk.section_title}>
                        {chunk.section_title}
                      </p>
                      <p className="ui-copy mt-2 truncate" title={chunk.content}>
                        {chunk.content}
                      </p>
                    </button>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-line bg-surface px-4 py-4 text-sm text-muted">
                    暂无检索结果。你可以先上传并处理资料，再通过关键词验证切块结果是否命中。
                  </div>
                )}
              </div>
            </div>
            </PanelCard>
          </div>
        </div>
      </div>

      {viewingDocument ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6"
          onClick={() => setViewingDocument(null)}
        >
          <div
            className="flex max-h-[85vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-line bg-white shadow-panel"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
              <div className="space-y-2">
                <p className="ui-field-label">全文查看</p>
                <h2 className="text-lg font-semibold text-ink">{viewingDocument.title}</h2>
                <p className="text-sm text-subtle">
                  {categoryLabelMap[viewingDocument.category]} · {getStatusLabel(viewingDocument.status)} ·{" "}
                  {getContentSourceLabel(viewingDocument.source)}
                </p>
              </div>
              <button className="ui-button-secondary" type="button" onClick={() => setViewingDocument(null)}>
                关闭
              </button>
            </div>

            <div className="overflow-y-auto px-5 py-4">
              <pre className="whitespace-pre-wrap break-words text-sm leading-7 text-muted">
                {viewingDocument.content}
              </pre>
            </div>
          </div>
        </div>
      ) : null}

      {selectedRetrievedChunk ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6"
          onClick={() => setSelectedRetrievedChunk(null)}
        >
          <div
            className="flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-3xl border border-line bg-white shadow-panel"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
              <div className="space-y-2">
                <p className="ui-field-label">检索结果全文</p>
                <h2 className="text-lg font-semibold text-ink">{selectedRetrievedChunk.document_title}</h2>
                <p className="text-sm text-subtle">{selectedRetrievedChunk.section_title}</p>
              </div>
              <button className="ui-button-secondary" type="button" onClick={() => setSelectedRetrievedChunk(null)}>
                关闭
              </button>
            </div>

            <div className="overflow-y-auto px-5 py-4">
              <pre className="whitespace-pre-wrap break-words text-sm leading-7 text-muted">
                {selectedRetrievedChunk.content}
              </pre>
            </div>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
