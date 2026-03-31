import { ReactNode } from "react";

import SidebarNav from "@/components/ui/sidebar-nav";

type AppShellProps = {
  children: ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-canvas">
      <div className="mx-auto flex min-h-screen max-w-[1680px] flex-col lg:flex-row">
        <SidebarNav />
        <main className="min-w-0 flex-1">
          <div className="mx-auto flex min-h-screen max-w-[1160px] flex-col gap-6 px-4 py-4 sm:px-6 lg:px-8 lg:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
