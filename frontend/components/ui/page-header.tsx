import { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  footer?: ReactNode;
  actions?: ReactNode;
  aside?: ReactNode;
};

export default function PageHeader({
  eyebrow,
  title,
  description,
  footer,
  actions,
  aside
}: PageHeaderProps) {
  return (
    <header className="ui-hero-panel px-5 py-5 sm:px-6 sm:py-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1 max-w-3xl">
          {eyebrow ? <p className="ui-kicker">{eyebrow}</p> : null}
          <h1 className="ui-page-title mt-3">{title}</h1>
          <p className="ui-copy mt-3 max-w-2xl text-[15px] leading-7">{description}</p>
          {footer ? <div className="mt-6 flex flex-wrap gap-2 border-t border-line/70 pt-5">{footer}</div> : null}
        </div>

        {(actions || aside) ? (
          <div className="flex w-full flex-col gap-3 lg:w-[336px] lg:flex-none lg:items-stretch">
            {actions ? <div className="flex w-full flex-wrap gap-2 lg:justify-end">{actions}</div> : null}
            {aside ? <div className="w-full rounded-2xl border border-line/70 bg-surface px-3 py-3">{aside}</div> : null}
          </div>
        ) : null}
      </div>
    </header>
  );
}
