export function StatusPill({ value }: { value: string }) {
  const styles: Record<string, string> = {
    processed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    processing: 'bg-blue-50 text-blue-700 border-blue-200',
    uploaded: 'bg-amber-50 text-amber-700 border-amber-200',
    failed: 'bg-red-50 text-red-700 border-red-200',
    verified: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    pending: 'bg-amber-50 text-amber-700 border-amber-200',
    flagged: 'bg-orange-50 text-orange-700 border-orange-200',
    rejected: 'bg-red-50 text-red-700 border-red-200',
  };
  return <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${styles[value] ?? 'border-line bg-app text-muted'}`}>{value}</span>;
}
