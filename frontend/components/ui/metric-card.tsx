import { cn } from "@/lib/cn";

type MetricCardProps = {
  label: string;
  value: string;
  helper?: string;
  tone?: "default" | "accent" | "success" | "warning";
};

const toneMap = {
  default: "border-line/70 bg-surface",
  accent: "border-accent/15 bg-accent-soft",
  success: "border-success/15 bg-success-soft",
  warning: "border-warning/20 bg-warning-soft"
} as const;

const dotToneMap = {
  default: "bg-line-strong",
  accent: "bg-accent",
  success: "bg-success",
  warning: "bg-warning"
};

export default function MetricCard({
  label,
  value,
  helper,
  tone = "default"
}: MetricCardProps) {
  return (
    <article className={cn("rounded-2xl border px-4 py-4 shadow-panel", toneMap[tone])}>
      <div className="flex h-full flex-col justify-between gap-4">
        <div className="flex items-center justify-between gap-3">
          <p className="ui-field-label">{label}</p>
          <span className={cn("h-2.5 w-2.5 rounded-full", dotToneMap[tone])} />
        </div>
        <div>
          <p className="break-words text-[24px] font-semibold leading-8 text-ink sm:text-[28px] sm:leading-9">{value}</p>
          {helper ? <p className="mt-2 text-sm leading-6 text-muted">{helper}</p> : null}
        </div>
      </div>
    </article>
  );
}
