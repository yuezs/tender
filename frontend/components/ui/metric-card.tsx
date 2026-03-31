import { cn } from "@/lib/cn";

type MetricCardProps = {
  label: string;
  value: string;
  helper?: string;
  tone?: "default" | "accent" | "success" | "warning";
};

const toneMap = {
  default: "bg-panel",
  accent: "bg-accent-soft/90",
  success: "bg-success-soft",
  warning: "bg-warning-soft"
};

export default function MetricCard({
  label,
  value,
  helper,
  tone = "default"
}: MetricCardProps) {
  return (
    <article className={cn("rounded-2xl border px-4 py-4 shadow-sm", toneMap[tone])}>
      <p className="ui-field-label">{label}</p>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-ink">{value}</p>
      {helper ? <p className="ui-help mt-2">{helper}</p> : null}
    </article>
  );
}
