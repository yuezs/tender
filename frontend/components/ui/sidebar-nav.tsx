"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";

const navItems = [
  { href: "/", label: "工作台总览", helper: "系统入口与能力概览" },
  { href: "/discovery", label: "项目发现", helper: "采集、筛选与推荐线索" },
  { href: "/tender", label: "招标处理", helper: "上传文件并发起主链路" },
  { href: "/results", label: "结果审阅", helper: "审阅结论、风险与正文" },
  { href: "/knowledge", label: "资料中心", helper: "管理企业知识资料" }
];

export default function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside className="lg:sticky lg:top-5 lg:h-[calc(100vh-2.5rem)] lg:w-[292px] lg:flex-none">
      <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-line/80 bg-sidebar shadow-panel">
        <div className="border-b border-line/70 px-4 py-5 sm:px-6 lg:px-5">
          <p className="ui-kicker">Tender Executive Demo</p>
          <h1 className="mt-2 text-xl font-semibold text-ink">AI 招投标助手</h1>
          <p className="mt-3 text-sm leading-6 text-muted">
            围绕项目发现、招标判断与标书生成，展示一套更完整、可信、可连续处理的企业工作台。
          </p>
        </div>

        <nav className="grid gap-2 px-3 py-4 sm:px-5 lg:flex-1 lg:px-4">
          {navItems.map((item) => {
            const active = item.href === "/"
              ? pathname === item.href
              : pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-2xl border px-4 py-3 transition-all duration-200",
                  active
                    ? "border-accent/15 bg-panel text-ink shadow-panel"
                    : "border-transparent bg-transparent text-muted hover:border-line/80 hover:bg-panel"
                )}
              >
                <div className="flex items-start gap-3">
                  <span className={cn("mt-1.5 h-2.5 w-2.5 rounded-full", active ? "bg-accent" : "bg-line-strong")} />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-ink">{item.label}</p>
                    <p className="mt-1 text-xs leading-5 text-subtle">{item.helper}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-line/70 px-3 py-4 sm:px-5 lg:px-4">
          <div className="ui-inset px-4 py-4">
            <p className="ui-field-label">当前阶段</p>
            <p className="mt-2 text-sm font-semibold text-ink">MVP 演示版</p>
            <p className="mt-2 text-xs leading-5 text-subtle">
              本轮聚焦公开项目发现、招标判断、标书初稿与知识引用，不扩展审批流和复杂协作能力。
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
