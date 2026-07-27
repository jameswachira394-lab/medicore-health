export function Card({ title, action, children, className = "" }) {
  return (
    <div className={`bg-surface border border-line rounded-xl p-5 ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h3 className="font-display text-[1.05rem] tracking-tight text-ink">{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

export function Button({ variant = "primary", className = "", ...props }) {
  const base = "inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";
  const variants = {
    primary: "bg-brand text-white hover:bg-brand-dim",
    secondary: "bg-brand-tint text-brand-dim hover:bg-[#d5e7e1]",
    ghost: "bg-transparent text-ink hover:bg-canvas border border-line",
    danger: "bg-danger text-white hover:bg-[#8c2c23]",
  };
  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />;
}

export function Input({ label, error, className = "", ...props }) {
  return (
    <label className="block">
      {label && <span className="block text-sm font-medium text-ink/80 mb-1">{label}</span>}
      <input
        className={`w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink/40 focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand ${className}`}
        {...props}
      />
      {error && <span className="block text-xs text-danger mt-1">{error}</span>}
    </label>
  );
}

export function Select({ label, className = "", children, ...props }) {
  return (
    <label className="block">
      {label && <span className="block text-sm font-medium text-ink/80 mb-1">{label}</span>}
      <select
        className={`w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand ${className}`}
        {...props}
      >
        {children}
      </select>
    </label>
  );
}

const STATUS_STYLES = {
  requested: { dot: "text-amber", tint: "bg-amber-tint text-[#8a5a12]" },
  confirmed: { dot: "text-brand", tint: "bg-brand-tint text-brand-dim" },
  completed: { dot: "text-success", tint: "bg-success-tint text-success" },
  cancelled: { dot: "text-ink/40", tint: "bg-canvas text-ink/50" },
  no_show: { dot: "text-danger", tint: "bg-danger-tint text-danger" },
  pending: { dot: "text-amber", tint: "bg-amber-tint text-[#8a5a12]" },
  paid: { dot: "text-success", tint: "bg-success-tint text-success" },
  partially_paid: { dot: "text-amber", tint: "bg-amber-tint text-[#8a5a12]" },
  overdue: { dot: "text-danger", tint: "bg-danger-tint text-danger" },
};

/** Status chip with the signature "vitals pulse" dot — used for
 * appointment/invoice/lab statuses across every portal. */
export function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.requested;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${style.tint}`}>
      <span className={`relative inline-block h-1.5 w-1.5 rounded-full bg-current status-pulse ${style.dot}`} />
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function Table({ columns, rows, emptyLabel = "Nothing here yet." }) {
  if (!rows || rows.length === 0) {
    return <p className="text-sm text-ink/50 py-6 text-center">{emptyLabel}</p>;
  }
  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-ink/45 border-b border-line">
            {columns.map((c) => (
              <th key={c.key} className="py-2 px-3 font-medium">{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id || i} className="border-b border-line/60 last:border-0 hover:bg-canvas/60">
              {columns.map((c) => (
                <td key={c.key} className="py-2.5 px-3 align-middle">
                  {c.render ? c.render(row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PageHeader({ eyebrow, title, description, action }) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div>
        {eyebrow && <p className="text-xs font-medium uppercase tracking-wide text-brand mb-1">{eyebrow}</p>}
        <h1 className="font-display text-2xl text-ink tracking-tight">{title}</h1>
        {description && <p className="text-sm text-ink/60 mt-1 max-w-xl">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function Banner({ tone = "info", children }) {
  const tones = {
    info: "bg-brand-tint text-brand-dim",
    danger: "bg-danger-tint text-danger",
    success: "bg-success-tint text-success",
  };
  return <div className={`rounded-lg px-4 py-3 text-sm ${tones[tone]}`}>{children}</div>;
}
