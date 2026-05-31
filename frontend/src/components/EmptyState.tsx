import { LucideIcon } from 'lucide-react';

export function EmptyState({ icon: Icon, title, body }: { icon: LucideIcon; title: string; body: string }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-white p-8 text-center">
      <div className="mx-auto grid h-11 w-11 place-items-center rounded-lg bg-app text-muted">
        <Icon size={22} />
      </div>
      <h3 className="mt-4 text-base font-semibold text-ink">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">{body}</p>
    </div>
  );
}
