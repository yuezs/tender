"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";

const navItems = [
  { href: "/", label: "工作台总览", helper: "系统入口与主能力概览" },
  { href: "/tender", label: "招标处理", helper: "上传、解析、判断与生成" },
  { href: "/results", label: "结果评审", helper: "查看结构化结果和初稿" },
  { href: "/knowledge", label: "资料中心", helper: "管理企业知识资料" }
];

export default function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside className="border-b border-line bg-sidebar lg:sticky lg:top-0 lg:h-screen lg:w-[280px] lg:flex-none lg:border-b-0 lg:border-r">
      <div className="flex h-full flex-col gap-5 px-4 py-4 sm:px-6 lg:px-5 lg:py-6">
        <div className="ui-panel-muted px-4 py-4">
          <p className="ui-kicker">Tender Workspace</p>
          <h1 className="mt-2 text-lg font-semibold tracking-tight text-ink">AI 招投标助手</h1>
          <p className="mt-2 text-sm leading-6 text-muted">企业内部使用的辅助投标工作台，聚焦文档处理、评审判断与初稿生成。</p>
        </div>

        <nav className="grid gap-2 lg:flex-1">
          {navItems.map((item) => {
            const active = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-2xl border px-4 py-3 transition",
                  active
                    ? "border-accent/30 bg-panel text-ink shadow-panel"
                    : "border-transparent bg-transparent text-muted hover:border-line hover:bg-panel"
                )}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={cn(
                      "h-2.5 w-2.5 rounded-full",
                      active ? "bg-accent" : "bg-line-strong"
                    )}
                  />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold">{item.label}</p>
                    <p className="mt-1 text-xs leading-5 text-subtle">{item.helper}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        <div className="ui-panel border-dashed px-4 py-4">
          <p className="ui-field-label">当前阶段</p>
          <p className="mt-2 text-sm font-semibold text-ink">MVP 骨架 + 主链路验证</p>
          <p className="mt-2 text-xs leading-5 text-subtle">当前重点是让招标处理、知识检索与生成链路稳定可演示，而不是做复杂视觉装饰。</p>
        </div>
      </div>
    </aside>
  );
}
