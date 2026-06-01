import { BarChart3, BookOpen, Bot, FileUp, LayoutDashboard, LogOut } from 'lucide-react';
import { ReactNode, useState } from 'react';
import { Page } from '../App';
import { useAppContext } from '../context/AppContext';

const navItems: { id: Page; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'courses', label: 'Courses', icon: BookOpen },
  { id: 'upload', label: 'Upload', icon: FileUp },
  { id: 'chat', label: 'AI Chat', icon: Bot },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
];

export function AppLayout({ page, onPageChange, children }: { page: Page; onPageChange: (page: Page) => void; children: ReactNode }) {
  const { userEmail, signInWithGoogle, signOut, isAuthConfigured, authReady } = useAppContext();
  const [authError, setAuthError] = useState('');

  async function handleGoogleSignIn() {
    setAuthError('');
    try {
      await signInWithGoogle();
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Google sign-in failed.');
    }
  }

  return (
    <div className="min-h-screen bg-app text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white px-4 py-5 lg:block">
        <div className="flex items-center gap-3 px-2">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-brand text-white">
            <BookOpen size={21} />
          </div>
          <div>
            <p className="text-lg font-semibold">Study Buddy</p>
            <p className="text-xs text-muted">Academic AI workspace</p>
          </div>
        </div>
        <nav className="mt-8 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = page === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                  active ? 'bg-brand text-white' : 'text-muted hover:bg-app hover:text-ink'
                }`}
              >
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-line bg-white/95 px-4 py-3 backdrop-blur lg:px-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm text-muted">Workspace</p>
              <h1 className="text-xl font-semibold text-ink md:text-2xl">{navItems.find((item) => item.id === page)?.label}</h1>
            </div>
            <div className="flex flex-col items-start gap-2 md:flex-row md:items-center">
              {userEmail ? (
                <div className="flex items-center gap-2 rounded-lg border border-line bg-app px-3 py-2 text-sm">
                  <span className="max-w-56 truncate text-muted">{userEmail}</span>
                  <button onClick={signOut} className="grid h-7 w-7 place-items-center rounded-md text-muted hover:bg-white hover:text-ink" title="Sign out">
                    <LogOut size={15} />
                  </button>
                </div>
              ) : isAuthConfigured ? (
                <button
                  onClick={handleGoogleSignIn}
                  disabled={!authReady}
                  className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                >
                  Sign in with Google
                </button>
              ) : (
                <span className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">Auth environment is missing</span>
              )}
              {authError && <span className="max-w-md text-sm text-red-600">{authError}</span>}
            </div>
          </div>
          <div className="mt-3 flex gap-2 overflow-x-auto lg:hidden">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => onPageChange(item.id)}
                  className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm ${page === item.id ? 'bg-brand text-white' : 'bg-app text-muted'}`}
                >
                  <Icon size={16} />
                  {item.label}
                </button>
              );
            })}
          </div>
        </header>
        <div className="px-4 py-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}
