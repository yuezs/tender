import { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export default function EmptyState({
  title,
  description,
  action
}: EmptyStateProps) {
  return (
    <div className="rounded-2xl border border-dashed border-line/80 bg-surface px-5 py-9 text-center">
      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full border border-line/80 bg-panel text-sm font-semibold text-muted shadow-panel">
        ·
      </div>
      <h3 className="mt-4 text-lg font-semibold text-ink">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted">{description}</p>
      {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
    </div>
  );
}
