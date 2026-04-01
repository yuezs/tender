"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";

const navItems = [
  { href: "/", label: "工作台总览", helper: "系统入口与当前能力概览" },
  { href: "/discovery", label: "项目发现", helper: "手动采集、筛选和推荐项目" },
  { href: "/tender", label: "招标处理", helper: "上传文件并运行主链路" },
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
          <p className="mt-2 text-sm leading-6 text-muted">
            当前版本把“项目发现”放在写标书主链路前，先做项目筛选和推荐，再决定是否进入正式写标流程。
          </p>
        </div>

        <nav className="grid gap-2 lg:flex-1">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
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
          <p className="mt-2 text-sm font-semibold text-ink">MVP + 项目发现前置层</p>
          <p className="mt-2 text-xs leading-5 text-subtle">
            本期只做单站手动采集、线索池和推荐，不做多站聚合、附件下载和自动进入写标书链路。
          </p>
        </div>
      </div>
    </aside>
  );
}
