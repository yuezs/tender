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
    <div className="rounded-2xl border border-dashed bg-surface px-5 py-8 text-center">
      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full border bg-panel text-sm font-semibold text-muted">
        --
      </div>
      <h3 className="mt-4 text-base font-semibold text-ink">{title}</h3>
      <p className="ui-copy mx-auto mt-2 max-w-xl">{description}</p>
      {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
    </div>
  );
}
