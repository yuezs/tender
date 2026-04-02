"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";

import AppShell from "@/components/app-shell";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import { listKnowledgeDocuments, processKnowledgeDocument, retrieveKnowledge, uploadKnowledgeDocument } from "@/lib/api";
import { KnowledgeCategory, KnowledgeDocumentItem, KnowledgeDocumentStatus, KnowledgeChunkItem } from "@/types/knowledge";

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
] as const;

const categoryOptions = categories.map((item) => item.code) as KnowledgeCategory[];
const statusOptions: Array<KnowledgeDocumentStatus | ""> = ["", "uploaded", "processed", "error"];

function normalizeCsvList(raw: string) {
  return raw
    .replace(/，/g, ",")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
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

  const [filterCategory, setFilterCategory] = useState<KnowledgeCategory | "">("");
  const [filterStatus, setFilterStatus] = useState<KnowledgeDocumentStatus | "">("");
  const [documents, setDocuments] = useState<KnowledgeDocumentItem[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [processingId, setProcessingId] = useState("");

  const [retrieveCategory, setRetrieveCategory] = useState<KnowledgeCategory | "">("");
  const [retrieveQuery, setRetrieveQuery] = useState("");
  const [retrieveTags, setRetrieveTags] = useState("");
  const [retrieveIndustry, setRetrieveIndustry] = useState("");
  const [retrieveLimit, setRetrieveLimit] = useState(5);
  const [retrieving, setRetrieving] = useState(false);
  const [retrievedChunks, setRetrievedChunks] = useState<KnowledgeChunkItem[]>([]);

  const processedCount = useMemo(
    () => documents.filter((item) => item.status === "processed").length,
    [documents]
  );
  const uploadedCount = useMemo(
    () => documents.filter((item) => item.status === "uploaded").length,
    [documents]
  );

  async function refreshDocuments(nextFilters?: { category?: KnowledgeCategory | ""; status?: KnowledgeDocumentStatus | "" }) {
    setLoadingList(true);
    try {
      const response = await listKnowledgeDocuments({
        category: nextFilters?.category ?? filterCategory,
        status: nextFilters?.status ?? filterStatus
      });
      setDocuments(response.items);
    } catch (error) {
      const message = error instanceof Error ? error.message : "知识文档列表获取失败";
      setPageMessage(message);
    } finally {
      setLoadingList(false);
    }
  }

  useEffect(() => {
    refreshDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    if (file && !uploadTitle.trim()) {
      const baseName = file.name.replace(/\.[^/.]+$/, "");
      setUploadTitle(baseName);
    }
  }

  async function handleUpload() {
    setPageMessage("");
    if (!selectedFile) {
      setPageMessage("请先选择一个 txt 或 docx 文件。");
      return;
    }
    if (!uploadTitle.trim()) {
      setPageMessage("title 不能为空。");
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

      setPageMessage(`上传成功：${result.title}（${result.category}）`);
      setSelectedFile(null);
      const fileInput = document.getElementById("knowledge-file") as HTMLInputElement | null;
      if (fileInput) {
        fileInput.value = "";
      }

      if (autoProcess) {
        setProcessingId(result.document_id);
        await processKnowledgeDocument(result.document_id);
        setProcessingId("");
        setPageMessage(`上传并处理完成：${result.title}`);
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
      await processKnowledgeDocument(documentId);
      setPageMessage("处理完成。");
      await refreshDocuments();
    } catch (error) {
      const message = error instanceof Error ? error.message : "处理失败";
      setPageMessage(message);
    } finally {
      setProcessingId("");
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
        limit: retrieveLimit
      });
      setRetrievedChunks(response.chunks);
      setPageMessage(`检索成功：命中 ${response.chunks.length} 条。`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "检索失败";
      setPageMessage(message);
    } finally {
      setRetrieving(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Knowledge Workspace"
        title="企业资料中心"
        description="上传公司资料并按固定流程解析、切块写入 MySQL，供 orchestrator 在 judge / generate 阶段按分类检索引用。"
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="资料类型" value="4 类" helper="固定分类，不扩散" tone="accent" />
            <MetricCard
              label="已处理"
              value={`${processedCount}/${documents.length}`}
              helper={uploadedCount ? `待处理 ${uploadedCount} 份` : "无待处理文档"}
            />
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_360px]">
        <div className="space-y-6">
          <PanelCard title="资料上传" description="当前仅支持 txt / docx。上传后可选择立即处理（解析 + 切块写入 MySQL）。">
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
                  {selectedFile ? `已选择：${selectedFile.name}` : "点击选择知识文档（txt / docx）"}
                </p>
                <p className="ui-copy mt-2">
                  {selectedFile
                    ? `文件大小约 ${(selectedFile.size / 1024).toFixed(1)} KB。`
                    : "建议上传公司介绍、资质、案例与模板等可复用内容，方便 judge / generate 检索引用。"}
                </p>
              </label>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-2">
                  <span className="ui-field-label">标题（title）</span>
                  <input
                    className="ui-input"
                    value={uploadTitle}
                    onChange={(event) => setUploadTitle(event.target.value)}
                    placeholder="例如：公司介绍2026版"
                    disabled={uploading}
                  />
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">分类（category）</span>
                  <select
                    className="ui-input"
                    value={uploadCategory}
                    onChange={(event) => setUploadCategory(event.target.value as KnowledgeCategory)}
                    disabled={uploading}
                  >
                    {categoryOptions.map((category) => (
                      <option key={category} value={category}>
                        {category}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">标签（tags，可选）</span>
                  <input
                    className="ui-input"
                    value={uploadTags}
                    onChange={(event) => setUploadTags(event.target.value)}
                    placeholder="逗号分隔，例如：政务,智慧城市"
                    disabled={uploading}
                  />
                  <span className="ui-help">用于简单过滤与检索增强（LIKE）。</span>
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">行业（industry，可选）</span>
                  <input
                    className="ui-input"
                    value={uploadIndustry}
                    onChange={(event) => setUploadIndustry(event.target.value)}
                    placeholder="逗号分隔，例如：政务,环保"
                    disabled={uploading}
                  />
                  <span className="ui-help">用于简单过滤与检索增强（LIKE）。</span>
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
                  {uploading ? "上传中..." : "上传文档"}
                </button>
              </div>

              <div aria-live="polite" className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm leading-6 text-muted">
                {pageMessage || "上传后会保存原文件到 storage/knowledge/raw/，处理后写入 knowledge_documents / knowledge_chunks。"}{" "}
                {processingId ? <span className="text-accent">正在处理：{processingId}</span> : null}
              </div>
            </div>
          </PanelCard>

          <PanelCard title="资料分类" description="分类名称面向业务使用，英文 code 仅作为系统辅助标识。">
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

          <PanelCard title="知识文档列表" description="支持按 category / status 过滤，上传后需处理后才会产生切块用于检索。">
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-[220px_200px_auto]">
                <label className="space-y-2">
                  <span className="ui-field-label">分类过滤</span>
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
                    <option value="">全部</option>
                    {categoryOptions.map((category) => (
                      <option key={category} value={category}>
                        {category}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">状态过滤</span>
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
                        {status || "全部"}
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
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-line bg-canvas text-xs uppercase tracking-wide text-subtle">
                    <tr>
                      <th className="px-4 py-3">标题</th>
                      <th className="px-4 py-3">分类</th>
                      <th className="px-4 py-3">状态</th>
                      <th className="px-4 py-3">切块</th>
                      <th className="px-4 py-3">更新时间</th>
                      <th className="px-4 py-3 text-right">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {documents.length ? (
                      documents.map((item) => {
                        const canProcess = item.status === "uploaded" || item.status === "error";
                        const busy = processingId === item.document_id;
                        return (
                          <tr key={item.document_id} className="text-muted">
                            <td className="px-4 py-3">
                              <p className="font-semibold text-ink">{item.title}</p>
                              <p className="mt-1 text-xs text-subtle">ID: {item.document_id}</p>
                            </td>
                            <td className="px-4 py-3">{item.category}</td>
                            <td className="px-4 py-3">{item.status}</td>
                            <td className="px-4 py-3">{item.chunk_count}</td>
                            <td className="px-4 py-3 text-xs text-subtle">{item.updated_at}</td>
                            <td className="px-4 py-3 text-right">
                              <button
                                className="ui-button-ghost"
                                type="button"
                                onClick={() => handleProcess(item.document_id)}
                                disabled={!canProcess || busy || uploading}
                              >
                                {busy ? "处理中..." : canProcess ? "处理" : "已处理"}
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={6} className="px-4 py-10 text-center text-sm text-muted">
                          {loadingList ? "正在加载..." : "暂无知识文档，请先上传一份公司资料。"}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </PanelCard>
        </div>

        <PanelCard title="检索调试" description="按 category + tags + industry + LIKE 关键词做简单检索，用于验证知识片段能否命中。">
          <div className="space-y-4">
            <label className="space-y-2">
              <span className="ui-field-label">分类（可选）</span>
              <select
                className="ui-input"
                value={retrieveCategory}
                onChange={(event) => setRetrieveCategory(event.target.value as KnowledgeCategory | "")}
                disabled={retrieving}
              >
                <option value="">全部</option>
                {categoryOptions.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-2">
              <span className="ui-field-label">关键词（query，可选）</span>
              <input
                className="ui-input"
                value={retrieveQuery}
                onChange={(event) => setRetrieveQuery(event.target.value)}
                placeholder="例如：软件企业证书"
                disabled={retrieving}
              />
            </label>

            <label className="space-y-2">
              <span className="ui-field-label">tags（可选）</span>
              <input
                className="ui-input"
                value={retrieveTags}
                onChange={(event) => setRetrieveTags(event.target.value)}
                placeholder="逗号分隔"
                disabled={retrieving}
              />
            </label>

            <label className="space-y-2">
              <span className="ui-field-label">industry（可选）</span>
              <input
                className="ui-input"
                value={retrieveIndustry}
                onChange={(event) => setRetrieveIndustry(event.target.value)}
                placeholder="逗号分隔"
                disabled={retrieving}
              />
            </label>

            <label className="space-y-2">
              <span className="ui-field-label">limit</span>
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
              {retrieving ? "检索中..." : "执行检索"}
            </button>

            <div className="space-y-3">
              {retrievedChunks.length ? (
                retrievedChunks.map((chunk) => (
                  <article key={chunk.id} className="ui-panel-muted px-4 py-4">
                    <p className="ui-field-label">{chunk.document_title}</p>
                    <p className="mt-2 text-sm font-semibold text-ink">{chunk.section_title}</p>
                    <p className="ui-copy mt-2 whitespace-pre-wrap break-words">{chunk.content}</p>
                  </article>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed bg-surface px-4 py-4 text-sm text-muted">
                  暂无检索结果。你可以先上传并处理一份资料，再用关键词验证是否能命中。
                </div>
              )}
            </div>
          </div>
        </PanelCard>
      </div>
    </AppShell>
  );
}

