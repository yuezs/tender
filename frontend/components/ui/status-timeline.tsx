import { StepState } from "@/types/tender";
import { cn } from "@/lib/cn";

type StatusTimelineProps = {
  steps: Array<{
    key: string;
    label: string;
    state: StepState;
  }>;
};

const stateStyles = {
  pending: {
    dot: "border-line-strong bg-panel",
    label: "text-ink",
    badge: "border-line/80 bg-surface text-subtle"
  },
  loading: {
    dot: "border-warning bg-warning-soft",
    label: "text-ink",
    badge: "border-warning/20 bg-warning-soft text-warning"
  },
  success: {
    dot: "border-success bg-success",
    label: "text-ink",
    badge: "border-success/20 bg-success-soft text-success"
  },
  error: {
    dot: "border-danger bg-danger",
    label: "text-ink",
    badge: "border-danger/20 bg-danger-soft text-danger"
  }
} as const;

const stateLabelMap = {
  pending: "待处理",
  loading: "进行中",
  success: "已完成",
  error: "失败"
} as const;

export default function StatusTimeline({
  steps
}: StatusTimelineProps) {
  return (
    <ol className="space-y-5">
      {steps.map((step, index) => {
        const styles = stateStyles[step.state.status];
        const isLast = index === steps.length - 1;

        return (
          <li key={step.key} className="relative flex gap-4">
            <div className="relative flex w-5 justify-center">
              <span className={cn("mt-1 h-3.5 w-3.5 rounded-full border-2", styles.dot)} />
              {!isLast ? <span className="absolute left-1/2 top-5 h-[calc(100%-0.25rem)] w-px -translate-x-1/2 bg-line" /> : null}
            </div>
            <div className="min-w-0 flex-1 rounded-2xl border border-line/70 bg-surface px-4 py-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className={cn("text-sm font-semibold", styles.label)}>{step.label}</p>
                <span className={cn("inline-flex w-fit rounded-full border px-2.5 py-1 text-[11px] font-semibold", styles.badge)}>
                  {stateLabelMap[step.state.status]}
                </span>
              </div>
              <p className="ui-help mt-2">{step.state.message}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
