"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import AppShell from "@/components/app-shell";
import EmptyState from "@/components/ui/empty-state";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import { cn } from "@/lib/cn";
import {
  getDiscoveryProfile,
  listDiscoveryProjects,
  listDiscoveryRuns,
  runDiscoveryCollection
} from "@/lib/api";
import {
  DiscoveryProfile,
  DiscoveryProfileDirection,
  DiscoveryProjectListResponse,
  DiscoveryRunListResponse,
  DiscoveryRunResponse
} from "@/types/discovery";

type Filters = {
  keyword: string;
  region: string;
  notice_type: string;
  recommendation_level: string;
  profile_key: string;
  recommended_only: boolean;
  page: number;
  page_size: number;
};

const initialFilters: Filters = {
  keyword: "",
  region: "",
  notice_type: "",
  recommendation_level: "",
  profile_key: "",
  recommended_only: false,
  page: 1,
  page_size: 10
};

function formatLevel(level: string) {
  if (level === "high") {
    return "高推荐";
  }
  if (level === "medium") {
    return "中推荐";
  }
  return "低推荐";
}

function formatConfidence(confidence: string) {
  if (confidence === "high") {
    return "高把握";
  }
  if (confidence === "medium") {
    return "中把握";
  }
  return "低把握";
}

function levelBadgeClass(level: string) {
  if (level === "high") {
    return "border-success/20 bg-success-soft text-success";
  }
  if (level === "medium") {
    return "border-accent/20 bg-accent-soft text-accent";
  }
  return "border-warning/20 bg-warning-soft text-warning";
}

function confidenceBadgeClass(confidence: string) {
  if (confidence === "high") {
    return "border-success/20 bg-success-soft text-success";
  }
  if (confidence === "medium") {
    return "border-accent/20 bg-accent-soft text-accent";
  }
  return "border-warning/20 bg-warning-soft text-warning";
}

function splitTerms(value: string, limit = 5) {
  return value
    .split(/[\n,，、；;]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item, index, list) => list.indexOf(item) === index)
    .slice(0, limit);
}

function formatRunMode(mode: DiscoveryRunResponse["targeting"]["mode"]) {
  if (mode === "targeted") {
    return "定向采集";
  }
  if (mode === "keyword") {
    return "关键词采集";
  }
  return "广泛采集";
}

export default function DiscoveryPage() {
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [projects, setProjects] = useState<DiscoveryProjectListResponse | null>(null);
  const [runs, setRuns] = useState<DiscoveryRunListResponse | null>(null);
  const [profile, setProfile] = useState<DiscoveryProfile | null>(null);
  const [selectedProfileKey, setSelectedProfileKey] = useState("");
  const [keywordDraft, setKeywordDraft] = useState({
    keywords: "",
    regions: "",
    noticeTypes: "",
    excludeKeywords: ""
  });
  const [pageMessage, setPageMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCollecting, setIsCollecting] = useState(false);

  const latestRun: DiscoveryRunResponse | null = runs?.items[0] ?? null;
  const selectedDirection = useMemo<DiscoveryProfileDirection | null>(() => {
    if (!profile?.directions.length) {
      return null;
    }
    return (
      profile.directions.find((item) => item.profile_key === selectedProfileKey) ??
      profile.directions[0]
    );
  }, [profile, selectedProfileKey]);

  const totalPages = useMemo(() => {
    if (!projects) {
      return 1;
    }
    return Math.max(1, Math.ceil(projects.total / projects.page_size));
  }, [projects]);

  const rangeSummary = useMemo(() => {
    if (!projects?.items.length) {
      return "当前没有可展示的项目。";
    }

    const start = (projects.page - 1) * projects.page_size + 1;
    const end = start + projects.items.length - 1;
    return `显示第 ${start}-${end} 条，共 ${projects.total} 条项目线索。`;
  }, [projects]);
  const latestRunMode = latestRun ? formatRunMode(latestRun.targeting.mode) : "";
  const latestKeywordSummary = latestRun?.targeting.keywords.length
    ? latestRun.targeting.keywords.join("、")
    : "未指定";

  async function loadProjects(nextFilters: Filters) {
    const response = await listDiscoveryProjects(nextFilters);
    setProjects(response);
  }

  async function loadRuns() {
    const response = await listDiscoveryRuns();
    setRuns(response);
  }

  async function loadProfile() {
    const response = await getDiscoveryProfile();
    setProfile(response);
    if (response.directions.length) {
      setSelectedProfileKey((current) => current || response.directions[0].profile_key);
    }
  }

  async function refreshAll(nextFilters: Filters) {
    setIsLoading(true);
    try {
      await Promise.all([loadProjects(nextFilters), loadRuns(), loadProfile()]);
      if (!pageMessage) {
        setPageMessage("已加载项目发现工作台，可以先看推荐方向，再决定是否发起定向采集。");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "加载项目发现数据失败";
      setPageMessage(message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refreshAll(initialFilters);
  }, []);

  async function handleCollectBroad() {
    setIsCollecting(true);
    try {
      const result = await runDiscoveryCollection({ source: "ggzy", mode: "broad" });
      await refreshAll(filters);
      setPageMessage(`广泛采集完成：发现 ${result.total_found} 条，新增 ${result.total_new} 条，更新 ${result.total_updated} 条。`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "广泛采集失败";
      setPageMessage(message);
    } finally {
      setIsCollecting(false);
    }
  }

  async function handleCollectTargeted() {
    if (!selectedDirection) {
      setPageMessage("当前没有可用的推荐方向，请先补充并处理知识库资料。");
      return;
    }

    setIsCollecting(true);
    try {
      const result = await runDiscoveryCollection({
        source: "ggzy",
        mode: "targeted",
        profile_key: selectedDirection.profile_key,
        profile_title: selectedDirection.title,
        keywords: selectedDirection.keywords,
        regions: selectedDirection.regions,
        qualification_terms: selectedDirection.qualification_terms,
        industry_terms: selectedDirection.industry_terms
      });
      const nextFilters = { ...filters, page: 1, profile_key: selectedDirection.profile_key };
      setFilters(nextFilters);
      await refreshAll(nextFilters);
      setPageMessage(`已按“${selectedDirection.title}”完成定向采集：发现 ${result.total_found} 条，新增 ${result.total_new} 条，更新 ${result.total_updated} 条。`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "定向采集失败";
      setPageMessage(message);
    } finally {
      setIsCollecting(false);
    }
  }

  async function handleCollectByKeyword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const keywords = splitTerms(keywordDraft.keywords, 5);
    const regions = splitTerms(keywordDraft.regions, 4);
    const noticeTypes = splitTerms(keywordDraft.noticeTypes, 4);
    const excludeKeywords = splitTerms(keywordDraft.excludeKeywords, 5);

    if (!keywords.length) {
      setPageMessage("请至少输入一个关键词后再发起采集。");
      return;
    }

    setIsCollecting(true);
    try {
      const result = await runDiscoveryCollection({
        source: "ggzy",
        mode: "keyword",
        keywords,
        regions,
        notice_types: noticeTypes,
        exclude_keywords: excludeKeywords
      });
      const nextFilters = {
        ...filters,
        keyword: keywords[0],
        region: regions[0] ?? "",
        notice_type: noticeTypes[0] ?? "",
        profile_key: "",
        page: 1
      };
      setFilters(nextFilters);
      await refreshAll(nextFilters);
      if (result.total_found > 0) {
        setPageMessage(
          `已按关键词完成采集：发现 ${result.total_found} 条，新增 ${result.total_new} 条，更新 ${result.total_updated} 条。`
        );
      } else {
        setPageMessage(
          "本次关键词采集未发现结果。建议放宽地区、减少关键词个数、删除排除词，或切换到广泛采集。"
        );
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "关键词采集失败";
      setPageMessage(message);
    } finally {
      setIsCollecting(false);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextFilters = { ...filters, page: 1 };
    setFilters(nextFilters);
    await refreshAll(nextFilters);
  }

  async function changePage(nextPage: number) {
    const safePage = Math.min(Math.max(nextPage, 1), totalPages);
    const nextFilters = { ...filters, page: safePage };
    setFilters(nextFilters);
    await refreshAll(nextFilters);
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Discovery Executive Demo"
        title="项目发现工作台"
        description="系统支持广泛采集、按推荐方向采集，以及按关键词采集。你可以先主动找项目，再结合筛选和详情继续收敛结果。"
        actions={
          <>
            <button
              className="ui-button-secondary"
              type="button"
              onClick={handleCollectBroad}
              disabled={isCollecting}
            >
              广泛采集 ggzy
            </button>
            <button
              className="ui-button-primary"
              type="button"
              onClick={handleCollectTargeted}
              disabled={isCollecting || !selectedDirection}
            >
              {isCollecting ? "采集中..." : "按推荐方向采集"}
            </button>
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard
              label="推荐方向"
              value={String(profile?.directions.length ?? 0)}
              helper={profile?.has_profile ? "来自企业能力画像" : "等待知识资料补充"}
              tone="accent"
            />
            <MetricCard
              label="线索总数"
              value={String(projects?.total ?? 0)}
              helper={latestRun ? `最近${latestRunMode} ${latestRun.total_found} 条` : "尚未采集"}
            />
          </div>
        }
      />

      <div aria-live="polite" className="ui-page-note">
        {pageMessage || "可先按关键词主动找项目，也可用推荐方向采集，再结合筛选条件收敛结果。"}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_360px]">
        <div className="space-y-6">
          <PanelCard
            title="关键词采集"
            description="当推荐方向不够准，或你已经明确知道要找什么项目时，可以直接输入关键词发起采集。"
          >
            <form className="space-y-5" onSubmit={handleCollectByKeyword}>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <label className="space-y-2">
                  <span className="ui-field-label">关键词</span>
                  <input
                    className="ui-input"
                    placeholder="例如：智慧园区、弱电集成"
                    value={keywordDraft.keywords}
                    onChange={(event) =>
                      setKeywordDraft((current) => ({ ...current, keywords: event.target.value }))
                    }
                  />
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">地区</span>
                  <input
                    className="ui-input"
                    placeholder="例如：甘肃、兰州"
                    value={keywordDraft.regions}
                    onChange={(event) =>
                      setKeywordDraft((current) => ({ ...current, regions: event.target.value }))
                    }
                  />
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">公告类型</span>
                  <input
                    className="ui-input"
                    placeholder="例如：招标公告、采购公告"
                    value={keywordDraft.noticeTypes}
                    onChange={(event) =>
                      setKeywordDraft((current) => ({ ...current, noticeTypes: event.target.value }))
                    }
                  />
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">排除词</span>
                  <input
                    className="ui-input"
                    placeholder="例如：监理、造价"
                    value={keywordDraft.excludeKeywords}
                    onChange={(event) =>
                      setKeywordDraft((current) => ({ ...current, excludeKeywords: event.target.value }))
                    }
                  />
                </label>
              </div>

              <div className="flex flex-col gap-3 border-t border-line/70 pt-5 sm:flex-row sm:flex-wrap sm:items-center">
                <button className="ui-button-primary" type="submit" disabled={isCollecting}>
                  {isCollecting ? "采集中..." : "按关键词采集"}
                </button>
                <p className="ui-help sm:ml-auto">支持逗号分隔多个词。第一版最多采集 5 个关键词。</p>
              </div>
            </form>
          </PanelCard>

          <PanelCard
            title="推荐采集方向"
            description="优先利用企业资料反推出更值得追踪的项目方向，减少无目标地浏览公开项目。"
            actions={
              <Link className="ui-button-ghost" href="/knowledge">
                补充知识资料
              </Link>
            }
          >
            {profile?.has_profile && profile.directions.length ? (
              <div className="space-y-5">
                <div className="ui-summary-card-accent">
                  <p className="ui-field-label">当前建议</p>
                  <p className="mt-3 text-xl font-semibold leading-8 text-ink">
                    {selectedDirection ? `优先采集“${selectedDirection.title}”方向` : "优先从推荐方向开始采集"}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-muted">{profile.message}</p>
                  {selectedDirection ? (
                    <div className="mt-5 grid gap-3 md:grid-cols-3">
                      <div className="rounded-2xl border border-line/60 bg-panel px-4 py-4 shadow-panel">
                        <p className="ui-field-label">方向置信度</p>
                        <p className="mt-2 text-sm font-semibold text-ink">{formatConfidence(selectedDirection.confidence)}</p>
                      </div>
                      <div className="rounded-2xl border border-line/60 bg-panel px-4 py-4 shadow-panel">
                        <p className="ui-field-label">关键词数量</p>
                        <p className="mt-2 text-sm font-semibold text-ink">{selectedDirection.keywords.length} 个</p>
                      </div>
                      <div className="rounded-2xl border border-line/60 bg-panel px-4 py-4 shadow-panel">
                        <p className="ui-field-label">覆盖地区</p>
                        <p className="mt-2 text-sm font-semibold text-ink">{selectedDirection.regions.length || 0} 个</p>
                      </div>
                    </div>
                  ) : null}
                </div>

                <div className="grid gap-3 lg:grid-cols-3">
                  {profile.directions.map((direction) => {
                    const active = selectedDirection?.profile_key === direction.profile_key;
                    return (
                      <button
                        key={direction.profile_key}
                        type="button"
                        onClick={() => setSelectedProfileKey(direction.profile_key)}
                        className={cn(
                          "rounded-2xl border px-4 py-4 text-left transition-all duration-200",
                          active
                            ? "border-accent/15 bg-accent-soft shadow-panel"
                            : "border-line/80 bg-panel hover:border-line-strong hover:bg-surface"
                        )}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm font-semibold leading-6 text-ink">{direction.title}</p>
                          <span className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${confidenceBadgeClass(direction.confidence)}`}>
                            {formatConfidence(direction.confidence)}
                          </span>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-muted">{direction.description}</p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {direction.keywords.slice(0, 3).map((item) => (
                            <span key={item} className="rounded-full border border-line/70 bg-panel px-2 py-1 text-xs text-muted">
                              {item}
                            </span>
                          ))}
                        </div>
                        {direction.gap_message ? (
                          <p className="mt-3 text-xs leading-5 text-warning">{direction.gap_message}</p>
                        ) : null}
                      </button>
                    );
                  })}
                </div>

                {selectedDirection ? (
                  <div className="ui-inset overflow-hidden">
                    <div className="grid lg:grid-cols-2">
                      <div className="px-4 py-4 lg:border-r lg:border-line/70">
                        <p className="ui-field-label">推荐原因</p>
                        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                          {selectedDirection.reasons.map((item) => (
                            <li key={item} className="flex gap-2">
                              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="border-t border-line/70 px-4 py-4 lg:border-t-0">
                        <p className="ui-field-label">采集参数</p>
                        <div className="mt-3 space-y-3 text-sm leading-6 text-muted">
                          <p><span className="font-medium text-ink">关键词：</span>{selectedDirection.keywords.join("、") || "未生成"}</p>
                          <p><span className="font-medium text-ink">地区：</span>{selectedDirection.regions.join("、") || "未限定"}</p>
                          <p><span className="font-medium text-ink">资质词：</span>{selectedDirection.qualification_terms.join("、") || "未生成"}</p>
                          <p><span className="font-medium text-ink">行业词：</span>{selectedDirection.industry_terms.join("、") || "未生成"}</p>
                        </div>
                      </div>
                    </div>

                    <div className="border-t border-line/70 px-4 py-4">
                      <p className="ui-field-label">依赖资料</p>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        {selectedDirection.supporting_documents.map((item) => (
                          <div key={`${item.category}-${item.document_title}-${item.section_title}`} className="rounded-2xl border border-line/70 bg-panel px-3 py-3 shadow-panel">
                            <p className="text-xs font-medium text-muted">{item.category}</p>
                            <p className="mt-1 text-sm font-semibold text-ink">{item.document_title}</p>
                            <p className="mt-1 text-xs leading-5 text-subtle">{item.section_title || "未定位到分节"}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <EmptyState
                title="还没有可用的企业能力画像"
                description={profile?.message || "请先上传并处理资质、案例或公司概况资料，再获得推荐采集方向。"}
              />
            )}
          </PanelCard>

          <PanelCard
            title="筛选条件"
            description="当推荐方向还不够精确时，可继续用筛选条件收敛结果。筛选会直接作用于当前项目线索池。"
          >
            <form className="space-y-5" onSubmit={handleSearch}>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <label className="space-y-2">
                  <span className="ui-field-label">关键词</span>
                  <input
                    className="ui-input"
                    placeholder="例如：智慧园区"
                    value={filters.keyword}
                    onChange={(event) => setFilters((current) => ({ ...current, keyword: event.target.value }))}
                  />
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">地区</span>
                  <input
                    className="ui-input"
                    placeholder="例如：甘肃"
                    value={filters.region}
                    onChange={(event) => setFilters((current) => ({ ...current, region: event.target.value }))}
                  />
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">公告类型</span>
                  <input
                    className="ui-input"
                    placeholder="例如：招标公告"
                    value={filters.notice_type}
                    onChange={(event) => setFilters((current) => ({ ...current, notice_type: event.target.value }))}
                  />
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">推荐等级</span>
                  <select
                    className="ui-input"
                    value={filters.recommendation_level}
                    onChange={(event) =>
                      setFilters((current) => ({ ...current, recommendation_level: event.target.value }))
                    }
                  >
                    <option value="">全部推荐等级</option>
                    <option value="high">高推荐</option>
                    <option value="medium">中推荐</option>
                    <option value="low">低推荐</option>
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="ui-field-label">方向过滤</span>
                  <select
                    className="ui-input"
                    value={filters.profile_key}
                    onChange={(event) => setFilters((current) => ({ ...current, profile_key: event.target.value }))}
                  >
                    <option value="">全部方向</option>
                    {profile?.directions.map((direction) => (
                      <option key={direction.profile_key} value={direction.profile_key}>
                        {direction.title}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="space-y-2">
                  <span className="ui-field-label">结果范围</span>
                  <label className="flex h-10 items-center gap-3 rounded-xl border border-line/80 bg-panel px-3 text-sm text-ink shadow-panel">
                    <input
                      type="checkbox"
                      checked={filters.recommended_only}
                      onChange={(event) =>
                        setFilters((current) => ({ ...current, recommended_only: event.target.checked }))
                      }
                    />
                    仅看推荐项目
                  </label>
                </div>
              </div>

              <div className="flex flex-col gap-3 border-t border-line/70 pt-5 sm:flex-row sm:flex-wrap sm:items-center">
                <button className="ui-button-primary" type="submit" disabled={isLoading}>
                  {isLoading ? "加载中..." : "应用筛选"}
                </button>
                <button
                  className="ui-button-secondary"
                  type="button"
                  onClick={() => {
                    setFilters(initialFilters);
                    void refreshAll(initialFilters);
                  }}
                >
                  重置条件
                </button>
                <p className="ui-help sm:ml-auto">{rangeSummary}</p>
              </div>
            </form>
          </PanelCard>

          <PanelCard
            title="项目线索列表"
            description="先看标题、关键字段、推荐等级和推荐原因，再决定是否进入单条详情做继续判断。"
            actions={
              projects && projects.total > projects.page_size ? (
                <div className="flex gap-2">
                  <button
                    className="ui-button-secondary h-10 px-3"
                    type="button"
                    onClick={() => void changePage(filters.page - 1)}
                    disabled={filters.page <= 1}
                  >
                    上一页
                  </button>
                  <button
                    className="ui-button-secondary h-10 px-3"
                    type="button"
                    onClick={() => void changePage(filters.page + 1)}
                    disabled={filters.page >= totalPages}
                  >
                    下一页
                  </button>
                </div>
              ) : null
            }
          >
            {projects?.items.length ? (
              <div className="space-y-4">
                <div className="ui-page-note flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <p>
                    {rangeSummary}
                    {latestRun?.targeting.mode === "keyword" && latestRun.targeting.keywords.length
                      ? ` 当前结果最近一次来自关键词采集：${latestKeywordSummary}。`
                      : ""}
                  </p>
                  <p>第 {filters.page} / {totalPages} 页</p>
                </div>

                {projects.items.map((item) => (
                  <article key={item.lead_id} className="rounded-2xl border border-line/70 bg-panel px-5 py-5 shadow-panel">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full border border-line/70 bg-surface px-2 py-0.5 text-[11px] font-medium text-muted">
                            {item.notice_type || "待识别公告类型"}
                          </span>
                          {item.profile_title ? (
                            <span className="rounded-full border border-line/70 bg-surface px-2 py-0.5 text-[11px] font-medium text-muted">
                              命中方向：{item.profile_title}
                            </span>
                          ) : null}
                          {item.targeting_match_score > 0 ? (
                            <span className="rounded-full border border-line/70 bg-surface px-2 py-0.5 text-[11px] font-medium text-muted">
                              方向匹配：{item.targeting_match_score}
                            </span>
                          ) : null}
                          {item.matched_keywords.length ? (
                            <span className="rounded-full border border-accent/20 bg-accent-soft px-2 py-0.5 text-[11px] font-medium text-accent">
                              命中词：{item.matched_keywords.slice(0, 2).join("、")}
                            </span>
                          ) : null}
                        </div>

                        <h3 className="mt-3 text-lg font-semibold leading-8 text-ink">{item.title}</h3>

                        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                          <div>
                            <p className="ui-field-label">地区</p>
                            <p className="mt-1 text-sm text-ink">{item.region || "待识别"}</p>
                          </div>
                          <div>
                            <p className="ui-field-label">项目编号</p>
                            <p className="mt-1 text-sm text-ink">{item.project_code || "待识别"}</p>
                          </div>
                          <div>
                            <p className="ui-field-label">发布时间</p>
                            <p className="mt-1 text-sm text-ink">{item.published_at || "待识别"}</p>
                          </div>
                          <div>
                            <p className="ui-field-label">招标单位</p>
                            <p className="mt-1 text-sm text-ink">{item.tender_unit || "待识别"}</p>
                          </div>
                          <div>
                            <p className="ui-field-label">预算</p>
                            <p className="mt-1 text-sm text-ink">{item.budget_text || "待识别"}</p>
                          </div>
                          <div>
                            <p className="ui-field-label">截止时间</p>
                            <p className="mt-1 text-sm text-ink">{item.deadline_text || "待识别"}</p>
                          </div>
                        </div>

                        <div className="mt-4 border-t border-line/70 pt-4">
                          <p className="ui-field-label">推荐原因</p>
                          <ul className="mt-2 space-y-2 text-sm leading-6 text-muted">
                            {item.recommendation_reasons.length ? (
                              item.recommendation_reasons.slice(0, 2).map((reason) => (
                                <li key={reason} className="flex gap-2">
                                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                                  <span>{reason}</span>
                                </li>
                              ))
                            ) : (
                              <li className="flex gap-2">
                                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-line-strong" />
                                <span>暂无推荐理由</span>
                              </li>
                            )}
                          </ul>
                        </div>
                      </div>

                      <div className="flex w-full flex-col gap-3 lg:w-[240px] lg:flex-none">
                        <div className="ui-summary-card">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="ui-field-label">推荐评分</p>
                              <p className="mt-2 text-[30px] font-semibold leading-9 text-ink">{item.recommendation_score}</p>
                            </div>
                            <span className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${levelBadgeClass(item.recommendation_level)}`}>
                              {formatLevel(item.recommendation_level)}
                            </span>
                          </div>
                        </div>

                        <Link className="ui-button-primary w-full" href={`/discovery/${item.lead_id}`}>
                          查看详情
                        </Link>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                title="暂无项目线索"
                description="可先按推荐方向采集，也可以使用广泛采集建立基础线索池后再继续筛选。"
              />
            )}
          </PanelCard>
        </div>

        <div className="space-y-6">
          <PanelCard title="最近采集摘要" description="用于快速确认最近一次采集的模式、方向和结果规模。">
            {latestRun ? (
              <div className="space-y-4">
                <MetricCard
                  label="执行状态"
                  value={latestRun.status}
                  helper={latestRun.started_at}
                  tone="accent"
                />
                <div className="ui-summary-card">
                  <div className="space-y-3 text-sm leading-6 text-muted">
                    <p><span className="font-medium text-ink">采集模式：</span>{latestRunMode}</p>
                    <p><span className="font-medium text-ink">采集方向：</span>{latestRun.targeting.profile_title || "未指定"}</p>
                    <p><span className="font-medium text-ink">关键词：</span>{latestKeywordSummary}</p>
                    <p><span className="font-medium text-ink">地区：</span>{latestRun.targeting.regions.join("、") || "未指定"}</p>
                    <p><span className="font-medium text-ink">公告类型：</span>{latestRun.targeting.notice_types.join("、") || "未指定"}</p>
                    <p><span className="font-medium text-ink">排除词：</span>{latestRun.targeting.exclude_keywords.join("、") || "未指定"}</p>
                    <p><span className="font-medium text-ink">发现数量：</span>{latestRun.total_found}</p>
                    <p><span className="font-medium text-ink">新增数量：</span>{latestRun.total_new}</p>
                    <p><span className="font-medium text-ink">更新数量：</span>{latestRun.total_updated}</p>
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState title="尚未执行采集" description="点击采集按钮后，这里会显示最近一次采集摘要。" />
            )}
          </PanelCard>

          <PanelCard title="使用建议" description="保持工作台浏览效率时，优先先定向、后筛选、再进入详情。">
            <div className="divide-y divide-line/70">
              <div className="pb-4">
                <p className="text-sm font-semibold text-ink">明确目标时先用关键词</p>
                <p className="mt-2 text-sm leading-6 text-muted">
                  当你已经知道想找的项目类型时，优先用关键词采集；如果结果偏少，再放宽地区、减少关键词或切回广泛采集。
                </p>
              </div>
              <div className="py-4">
                <p className="text-sm font-semibold text-ink">先定向再筛选</p>
                <p className="mt-2 text-sm leading-6 text-muted">
                  推荐方向来自企业能力画像，优先用它确定范围，再补充关键词、地区和公告类型筛选。
                </p>
              </div>
              <div className="py-4">
                <p className="text-sm font-semibold text-ink">先浏览再进入详情</p>
                <p className="mt-2 text-sm leading-6 text-muted">
                  列表页优先判断标题、关键字段、推荐等级和推荐原因，确认值得跟进后再进入详情页。
                </p>
              </div>
              <div className="pt-4">
                <p className="text-sm font-semibold text-ink">采集与列表联动</p>
                <p className="mt-2 text-sm leading-6 text-muted">
                  定向采集完成后，系统会自动把方向条件带入当前筛选，方便继续在同一工作台里收敛结果。
                </p>
              </div>
            </div>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
