"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import AppShell from "@/components/app-shell";
import EmptyState from "@/components/ui/empty-state";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
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

export default function DiscoveryPage() {
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [projects, setProjects] = useState<DiscoveryProjectListResponse | null>(null);
  const [runs, setRuns] = useState<DiscoveryRunListResponse | null>(null);
  const [profile, setProfile] = useState<DiscoveryProfile | null>(null);
  const [selectedProfileKey, setSelectedProfileKey] = useState("");
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
        setPageMessage("已加载项目发现工作台，可先查看推荐方向，再决定是否发起定向采集。");
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
      setPageMessage(
        `广泛采集完成：发现 ${result.total_found} 条，新增 ${result.total_new} 条，更新 ${result.total_updated} 条。`
      );
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
      setPageMessage(
        `已按“${selectedDirection.title}”完成定向采集：发现 ${result.total_found} 条，新增 ${result.total_new} 条，更新 ${result.total_updated} 条。`
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "定向采集失败";
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
    const totalPages = projects ? Math.max(1, Math.ceil(projects.total / projects.page_size)) : 1;
    const safePage = Math.min(Math.max(nextPage, 1), totalPages);
    const nextFilters = { ...filters, page: safePage };
    setFilters(nextFilters);
    await refreshAll(nextFilters);
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Discovery Workspace"
        title="按企业能力找项目"
        description="系统会先根据知识库资料生成推荐采集方向，再按方向发起定向采集。原有筛选区继续保留，作为补充筛选入口。"
        actions={
          <>
            <button
              className="ui-button-primary"
              type="button"
              onClick={handleCollectTargeted}
              disabled={isCollecting || !selectedDirection}
            >
              {isCollecting ? "采集中..." : "按推荐方向采集"}
            </button>
            <button className="ui-button-secondary" type="button" onClick={handleCollectBroad} disabled={isCollecting}>
              广泛采集 ggzy
            </button>
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard
              label="推荐方向"
              value={String(profile?.directions.length ?? 0)}
              helper={profile?.has_profile ? "来自企业能力画像" : "等待知识库补料"}
              tone="accent"
            />
            <MetricCard
              label="线索总数"
              value={String(projects?.total ?? 0)}
              helper={latestRun ? `最近采集 ${latestRun.total_found} 条` : "尚未采集"}
            />
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_360px]">
        <div className="space-y-6">
          <PanelCard
            title="推荐采集方向"
            description="优先使用知识库资料反推出更值得追踪的项目方向，减少无头绪找项目。"
            actions={
              <Link className="ui-button-ghost" href="/knowledge">
                去补充知识库
              </Link>
            }
          >
            {profile?.has_profile && profile.directions.length ? (
              <div className="space-y-4">
                <div className="rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted">
                  {profile.message}
                </div>
                <div className="grid gap-4 lg:grid-cols-3">
                  {profile.directions.map((direction) => {
                    const active = selectedDirection?.profile_key === direction.profile_key;
                    return (
                      <button
                        key={direction.profile_key}
                        type="button"
                        onClick={() => setSelectedProfileKey(direction.profile_key)}
                        className={`rounded-2xl border px-4 py-4 text-left transition ${
                          active
                            ? "border-accent bg-accent-soft/60"
                            : "border-line bg-surface hover:border-accent/40 hover:bg-accent-soft/30"
                        }`}
                      >
                        <p className="ui-field-label">{formatConfidence(direction.confidence)}</p>
                        <p className="mt-3 text-base font-semibold text-ink">{direction.title}</p>
                        <p className="ui-copy mt-2">{direction.description}</p>
                        <div className="mt-3 flex flex-wrap gap-2 text-xs text-subtle">
                          {direction.keywords.slice(0, 3).map((item) => (
                            <span key={item} className="rounded-full border border-line px-2 py-1">
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
                  <div className="rounded-2xl border bg-surface px-4 py-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <p className="ui-field-label">推荐原因</p>
                        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                          {selectedDirection.reasons.map((item) => (
                            <li key={item}>- {item}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="ui-field-label">采集参数</p>
                        <div className="mt-3 space-y-3 text-sm leading-6 text-muted">
                          <p>关键词：{selectedDirection.keywords.join("、") || "未生成"}</p>
                          <p>地区：{selectedDirection.regions.join("、") || "未限定"}</p>
                          <p>资质词：{selectedDirection.qualification_terms.join("、") || "未生成"}</p>
                          <p>行业词：{selectedDirection.industry_terms.join("、") || "未生成"}</p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 rounded-2xl border bg-panel px-4 py-4">
                      <p className="ui-field-label">依赖资料</p>
                      <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                        {selectedDirection.supporting_documents.map((item) => (
                          <li key={`${item.category}-${item.document_title}-${item.section_title}`}>
                            - [{item.category}] {item.document_title}
                            {item.section_title ? ` / ${item.section_title}` : ""}
                          </li>
                        ))}
                      </ul>
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

          <PanelCard title="补充筛选" description="当推荐方向还不够精确时，可继续用原有筛选条件做补充筛选。">
            <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSearch}>
              <input
                className="ui-input"
                placeholder="关键词，如智慧园区"
                value={filters.keyword}
                onChange={(event) => setFilters((current) => ({ ...current, keyword: event.target.value }))}
              />
              <input
                className="ui-input"
                placeholder="地区，如甘肃"
                value={filters.region}
                onChange={(event) => setFilters((current) => ({ ...current, region: event.target.value }))}
              />
              <input
                className="ui-input"
                placeholder="公告类型，如招标公告"
                value={filters.notice_type}
                onChange={(event) => setFilters((current) => ({ ...current, notice_type: event.target.value }))}
              />
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

              <label className="flex items-center gap-3 text-sm text-ink">
                <input
                  type="checkbox"
                  checked={filters.recommended_only}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, recommended_only: event.target.checked }))
                  }
                />
                仅看推荐项目
              </label>

              <div className="flex gap-3">
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
                  重置
                </button>
              </div>
            </form>
          </PanelCard>

          <PanelCard
            title="项目线索池"
            description="优先展示命中当前方向的项目，再看知识支撑和发布时间。"
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
                    disabled={!projects || filters.page >= Math.ceil(projects.total / projects.page_size)}
                  >
                    下一页
                  </button>
                </div>
              ) : null
            }
          >
            {projects?.items.length ? (
              <div className="space-y-4">
                {projects.items.map((item) => (
                  <article key={item.lead_id} className="rounded-2xl border bg-surface px-4 py-4">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap gap-2 text-xs text-subtle">
                          <span>{item.notice_type || "待识别公告类型"}</span>
                          {item.profile_title ? <span>命中方向：{item.profile_title}</span> : null}
                          {item.targeting_match_score > 0 ? (
                            <span>方向命中分：{item.targeting_match_score}</span>
                          ) : null}
                        </div>
                        <h3 className="mt-2 text-base font-semibold text-ink">{item.title}</h3>
                        <div className="mt-3 flex flex-wrap gap-2 text-xs text-subtle">
                          <span>地区：{item.region || "待识别"}</span>
                          <span>项目编号：{item.project_code || "待识别"}</span>
                          <span>发布时间：{item.published_at || "待识别"}</span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-subtle">
                          <span>招标单位：{item.tender_unit || "待识别"}</span>
                          <span>预算：{item.budget_text || "待识别"}</span>
                          <span>截止：{item.deadline_text || "待识别"}</span>
                        </div>
                        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                          {item.recommendation_reasons.length ? (
                            item.recommendation_reasons.slice(0, 2).map((reason) => <li key={reason}>- {reason}</li>)
                          ) : (
                            <li>- 暂无推荐理由</li>
                          )}
                        </ul>
                      </div>

                      <div className="flex shrink-0 flex-col gap-3 lg:w-[200px]">
                        <MetricCard
                          label="推荐分"
                          value={String(item.recommendation_score)}
                          helper={formatLevel(item.recommendation_level)}
                          tone={
                            item.recommendation_level === "high"
                              ? "success"
                              : item.recommendation_level === "medium"
                                ? "accent"
                                : "warning"
                          }
                        />
                        <Link className="ui-button-secondary" href={`/discovery/${item.lead_id}`}>
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
                description="可先按推荐方向采集，也可以用广泛采集建立线索池。"
              />
            )}
          </PanelCard>
        </div>

        <div className="space-y-6">
          <PanelCard title="最近采集摘要" description="每次采集都会保留本次模式和方向参数，便于复盘。">
            {latestRun ? (
              <div className="space-y-4">
                <MetricCard
                  label="执行状态"
                  value={latestRun.status}
                  helper={latestRun.started_at}
                  tone="accent"
                />
                <div className="rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted">
                  <p>模式：{latestRun.targeting.mode === "targeted" ? "定向采集" : "广泛采集"}</p>
                  <p>方向：{latestRun.targeting.profile_title || "未指定"}</p>
                  <p>发现：{latestRun.total_found}</p>
                  <p>新增：{latestRun.total_new}</p>
                  <p>更新：{latestRun.total_updated}</p>
                </div>
              </div>
            ) : (
              <EmptyState title="尚未执行采集" description="点击采集按钮后，这里会显示最近一次采集摘要。" />
            )}
          </PanelCard>

          <PanelCard title="页面提示" description="先用企业能力确定方向，再采集，再看推荐结果。">
            <div aria-live="polite" className="rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted">
              {pageMessage || "当前推荐方向为空时，仍可继续使用广泛采集和补充筛选。"}
            </div>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
