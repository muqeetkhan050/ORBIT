import { createClient } from '@/src/lib/supabase/client';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// Wrapper around fetch() for calls to our FastAPI backend.
// It attaches the logged-in user's Supabase token as
// "Authorization: Bearer <token>" so the backend knows who is calling.
export async function apiFetch(path: string, options: RequestInit = {}) {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  return fetch(`${API_URL}${path}`, { ...options, headers });
}
