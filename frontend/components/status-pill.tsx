type StatusPillProps = {
  status: string | null;
};

const statusMap: Record<string, string> = {
  surging: "bg-emerald-400/20 text-emerald-200 border-emerald-300/20",
  hot: "bg-cyan-400/20 text-cyan-100 border-cyan-300/20",
  warm: "bg-amber-300/20 text-amber-100 border-amber-300/20",
  cold: "bg-slate-500/20 text-slate-200 border-slate-300/20"
};

export function StatusPill({ status }: StatusPillProps) {
  const normalized = (status || "cold").toLowerCase();
  const className = statusMap[normalized] || statusMap.cold;

  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] ${className}`}>
      {normalized}
    </span>
  );
}

