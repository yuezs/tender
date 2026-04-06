import { MouseEvent, ReactNode } from "react";

import { cn } from "@/lib/cn";

type AppModalProps = {
  open: boolean;
  title: string;
  eyebrow?: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
  maxWidthClassName?: string;
  contentClassName?: string;
  bodyClassName?: string;
  closeLabel?: string;
};

export default function AppModal({
  open,
  title,
  eyebrow,
  description,
  onClose,
  children,
  maxWidthClassName = "max-w-4xl",
  contentClassName,
  bodyClassName,
  closeLabel = "关闭"
}: AppModalProps) {
  if (!open) {
    return null;
  }

  function handleContentClick(event: MouseEvent<HTMLDivElement>) {
    event.stopPropagation();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6" onClick={onClose}>
      <div
        className={cn(
          "flex max-h-[85vh] w-full flex-col overflow-hidden rounded-3xl border border-line bg-white shadow-panel",
          maxWidthClassName,
          contentClassName
        )}
        onClick={handleContentClick}
      >
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div className="space-y-2">
            {eyebrow ? <p className="ui-field-label">{eyebrow}</p> : null}
            <h2 className="text-lg font-semibold text-ink">{title}</h2>
            {description ? <p className="text-sm text-subtle">{description}</p> : null}
          </div>
          <button className="ui-button-secondary" type="button" onClick={onClose}>
            {closeLabel}
          </button>
        </div>

        <div className={cn("overflow-y-auto px-5 py-4", bodyClassName)}>{children}</div>
      </div>
    </div>
  );
}
