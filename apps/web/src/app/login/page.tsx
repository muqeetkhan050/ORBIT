'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createClient } from '../../lib/supabase/client';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    router.push('/dashboard');
    router.refresh();
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <form
        onSubmit={handleLogin}
        className="w-full max-w-sm space-y-4 rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm"
      >
        <h1 className="text-xl font-semibold text-neutral-900">Log in to Orbit</h1>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-black py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? 'Logging in…' : 'Log in'}
        </button>

        <p className="text-center text-sm text-neutral-500">
          No account yet?{' '}
          <Link href="/register" className="font-medium text-neutral-900 underline">
            Register
          </Link>
        </p>
      </form>
    </main>
  );
}
