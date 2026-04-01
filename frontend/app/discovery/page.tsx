"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import AppShell from "@/components/app-shell";
import EmptyState from "@/components/ui/empty-state";
import MetricCard from "@/components/ui/metric-card";
import PageHeader from "@/components/ui/page-header";
import PanelCard from "@/components/ui/panel-card";
import {
  listDiscoveryProjects,
  listDiscoveryRuns,
  runDiscoveryCollection
} from "@/lib/api";
import {
  DiscoveryProjectListResponse,
  DiscoveryRunListResponse,
  DiscoveryRunResponse
} from "@/types/discovery";

type Filters = {
  keyword: string;
  region: string;
  notice_type: string;
  recommendation_level: string;
  recommended_only: boolean;
  page: number;
  page_size: number;
};

const initialFilters: Filters = {
  keyword: "",
  region: "",
  notice_type: "",
  recommendation_level: "",
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

export default function DiscoveryPage() {
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [projects, setProjects] = useState<DiscoveryProjectListResponse | null>(null);
  const [runs, setRuns] = useState<DiscoveryRunListResponse | null>(null);
  const [pageMessage, setPageMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCollecting, setIsCollecting] = useState(false);

  const latestRun: DiscoveryRunResponse | null = runs?.items[0] ?? null;

  async function loadProjects(nextFilters: Filters) {
    const response = await listDiscoveryProjects(nextFilters);
    setProjects(response);
  }

  async function loadRuns() {
    const response = await listDiscoveryRuns();
    setRuns(response);
  }

  async function refreshAll(nextFilters: Filters) {
    setIsLoading(true);
    try {
      await Promise.all([loadProjects(nextFilters), loadRuns()]);
      if (!pageMessage) {
        setPageMessage("已加载项目线索池，可手动筛选和查看推荐。");
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

  async function handleCollect() {
    setIsCollecting(true);
    try {
      const result = await runDiscoveryCollection("ggzy");
      await refreshAll(filters);
      setPageMessage(
        `采集完成：发现 ${result.total_found} 条，新增 ${result.total_new} 条，更新 ${result.total_updated} 条。`
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "手动采集失败";
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
        title="项目发现"
        description="手动采集单个公共资源交易网的公开项目，形成内部线索池，并基于现有知识库给出推荐分和推荐理由。"
        actions={
          <>
            <button className="ui-button-primary" type="button" onClick={handleCollect} disabled={isCollecting}>
              {isCollecting ? "采集中..." : "手动采集 ggzy"}
            </button>
            <Link className="ui-button-secondary" href="/tender">
              去招标处理
            </Link>
          </>
        }
        aside={
          <div className="grid grid-cols-2 gap-3">
            <MetricCard
              label="线索总数"
              value={String(projects?.total ?? 0)}
              helper="支持关键词、地区和推荐等级筛选"
              tone="accent"
            />
            <MetricCard
              label="最近采集"
              value={latestRun ? String(latestRun.total_found) : "0"}
              helper={latestRun ? latestRun.started_at : "尚未采集"}
            />
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_360px]">
        <div className="space-y-6">
          <PanelCard title="筛选项目" description="先做内部筛选和推荐判断，再决定是否进入写标书流程。">
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
            description="当前只展示项目发现结果，不自动导入写标书主链路。"
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
                    disabled={
                      !projects || filters.page >= Math.ceil(projects.total / projects.page_size)
                    }
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
                        <p className="ui-field-label">{item.notice_type || "待识别公告类型"}</p>
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

                      <div className="flex shrink-0 flex-col gap-3 lg:w-[180px]">
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
                description="先执行一次手动采集，或者调整筛选条件后再查看项目线索。"
              />
            )}
          </PanelCard>
        </div>

        <div className="space-y-6">
          <PanelCard title="最近采集摘要" description="每次手动采集都会写入一条执行记录。">
            {latestRun ? (
              <div className="space-y-4">
                <MetricCard label="执行状态" value={latestRun.status} helper={latestRun.started_at} tone="accent" />
                <div className="rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted">
                  <p>发现：{latestRun.total_found}</p>
                  <p>新增：{latestRun.total_new}</p>
                  <p>更新：{latestRun.total_updated}</p>
                  <p>来源：{latestRun.source}</p>
                  <p>触发方式：{latestRun.trigger_type}</p>
                </div>
              </div>
            ) : (
              <EmptyState
                title="尚未执行采集"
                description="点击“手动采集 ggzy”后，这里会显示最近一次采集的执行摘要。"
              />
            )}
          </PanelCard>

          <PanelCard title="页面提示" description="这一层只负责发现与推荐，不负责自动写标。">
            <div
              aria-live="polite"
              className="rounded-2xl border bg-surface px-4 py-4 text-sm leading-6 text-muted"
            >
              {pageMessage || "系统会先形成项目线索池，用户确认后再自行进入招标处理流程。"}
            </div>
          </PanelCard>
        </div>
      </div>
    </AppShell>
  );
}
