import Link from "next/link";
import { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

const navItems = [
  { href: "/", label: "首页" },
  { href: "/tender", label: "招标上传" },
  { href: "/results", label: "结果页" },
  { href: "/knowledge", label: "知识库" }
];

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand">AI 招投标助手</div>
        <nav className="nav">
          {navItems.map((item) => (
            <Link key={item.href} className="nav-link" href={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      {children}
    </div>
  );
}
