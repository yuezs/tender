import { ReactNode } from "react";

import { cn } from "@/lib/cn";

type PanelCardProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  muted?: boolean;
};

export default function PanelCard({
  title,
  description,
  actions,
  children,
  className,
  bodyClassName,
  muted = false
}: PanelCardProps) {
  return (
    <section className={cn(muted ? "ui-panel-muted" : "ui-panel", className)}>
      <div className="flex flex-col gap-4 px-5 py-5 sm:px-6 sm:py-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="ui-section-title">{title}</h2>
            {description ? <p className="ui-copy mt-2">{description}</p> : null}
          </div>
          {actions ? <div className="shrink-0">{actions}</div> : null}
        </div>
        <div className={cn("min-w-0", bodyClassName)}>{children}</div>
      </div>
    </section>
  );
}
