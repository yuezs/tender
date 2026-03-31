import { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
  aside?: ReactNode;
};

export default function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  aside
}: PageHeaderProps) {
  return (
    <header className="ui-panel relative overflow-hidden px-5 py-6 sm:px-7 sm:py-7">
      <div className="absolute inset-x-0 top-0 h-1 bg-accent/70" />
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-3xl">
          {eyebrow ? <p className="ui-kicker">{eyebrow}</p> : null}
          <h1 className="ui-page-title mt-3">{title}</h1>
          <p className="ui-copy mt-3 max-w-2xl">{description}</p>
        </div>

        {(actions || aside) ? (
          <div className="flex w-full flex-col gap-3 lg:w-auto lg:min-w-[280px] lg:items-end">
            {actions ? <div className="flex w-full flex-wrap gap-3 lg:w-auto lg:justify-end">{actions}</div> : null}
            {aside ? <div className="w-full lg:max-w-sm">{aside}</div> : null}
          </div>
        ) : null}
      </div>
    </header>
  );
}
