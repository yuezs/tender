import { ReactNode } from "react";

import SidebarNav from "@/components/ui/sidebar-nav";

type AppShellProps = {
  children: ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-canvas">
      <div className="mx-auto flex min-h-screen max-w-[1680px] flex-col gap-4 px-3 py-3 sm:px-4 sm:py-4 lg:flex-row lg:gap-6 lg:px-5 lg:py-5">
        <SidebarNav />
        <main className="min-w-0 flex-1">
          <div className="mx-auto flex min-h-screen max-w-[1180px] flex-col gap-6 pb-6 lg:pt-1">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
