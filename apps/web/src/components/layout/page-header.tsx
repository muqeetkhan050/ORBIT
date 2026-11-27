// The header at the top of every dashboard page.
//
// It has a FIXED height (HEADER_HEIGHT) that the sidebar's ORBIT logo box uses too,
// so the line under the logo and the line under the page header always meet in one
// straight line. One shared component = every page gets the same height automatically.

export const HEADER_HEIGHT = 'h-24'; // 96px

export function PageHeader({
  title,
  subtitle,
  actions,
  width = 'max-w-3xl',
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode; // optional buttons on the right, e.g. Refresh
  width?: string; // match the page content's max width so the text lines up
}) {
  return (
    <header className={`flex ${HEADER_HEIGHT} shrink-0 items-center border-b bg-white px-8`}>
      <div className={`mx-auto flex w-full ${width} items-center justify-between gap-4`}>
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold tracking-tight">{title}</h1>
          {subtitle && <p className="mt-1 truncate text-sm text-gray-500">{subtitle}</p>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-3">{actions}</div>}
      </div>
    </header>
  );
}
