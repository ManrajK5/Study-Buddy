import { LucideIcon } from 'lucide-react';

export function StatCard({ label, value, icon: Icon, accent }: { label: string; value: string; icon: LucideIcon; accent: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel p-4 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
        </div>
        <div className="grid h-10 w-10 place-items-center rounded-lg" style={{ backgroundColor: `${accent}18`, color: accent }}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}
