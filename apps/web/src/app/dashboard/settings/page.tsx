'use client';

import type { User } from '@supabase/supabase-js';
import { KeyRound, Mail, ShieldCheck, UserRound } from 'lucide-react';
import { useEffect, useState } from 'react';
import { PageHeader } from '@/src/components/layout/page-header';
import { createClient } from '@/src/lib/supabase/client';

// Everything on this page talks to Supabase Auth directly from the browser.
// That's safe: updateUser() only works with the logged-in user's own session,
// so you can only ever change YOUR account. No backend endpoint needed.

type Message = { kind: 'ok' | 'error'; text: string } | null;

function formatDate(iso: string | undefined) {
  if (!iso) return '–';
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    createClient()
      .auth.getUser()
      .then(({ data }) => setUser(data.user));
  }, []);

  return (
    <div className="min-h-screen">
      <PageHeader title="Settings" subtitle="Your profile and account security." />

      <div className="mx-auto max-w-3xl space-y-6 p-8">
        {!user ? (
          <p className="text-center text-sm text-gray-400">Loading your profile…</p>
        ) : (
          <>
            {/* key={user.id}: the forms start from the loaded user's values */}
            <ProfileSection key={`name-${user.id}`} user={user} onSaved={setUser} />
            <EmailSection key={`email-${user.id}`} user={user} />
            <PasswordSection user={user} />
            <AccountSection user={user} />
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Name: stored in Supabase as user_metadata.full_name (the sidebar reads it).
// ---------------------------------------------------------------------------
function ProfileSection({ user, onSaved }: { user: User; onSaved: (user: User) => void }) {
  const savedName: string = user.user_metadata?.full_name ?? '';
  const [name, setName] = useState(savedName);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<Message>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    const { data, error } = await createClient().auth.updateUser({ data: { full_name: name.trim() } });
    setSaving(false);
    if (error) return setMessage({ kind: 'error', text: error.message });
    onSaved(data.user);
    setMessage({ kind: 'ok', text: 'Name saved.' });
  }

  const unchanged = name.trim() === savedName;

  return (
    <Section icon={<UserRound size={17} />} title="Profile" description="How Orbit greets you.">
      <form onSubmit={save} className="space-y-4">
        <Field label="Full name">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Alex Smith"
            maxLength={100}
            className={INPUT}
          />
        </Field>
        <FormFooter message={message}>
          <SaveButton disabled={saving || unchanged || !name.trim()} saving={saving} />
        </FormFooter>
      </form>
    </Section>
  );
}

// ---------------------------------------------------------------------------
// Email: Supabase doesn't switch it immediately. It emails a confirmation link
// first, so nobody can move your account to an address they don't own.
// ---------------------------------------------------------------------------
function EmailSection({ user }: { user: User }) {
  const [email, setEmail] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<Message>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    const { error } = await createClient().auth.updateUser({ email: email.trim() });
    setSaving(false);
    if (error) return setMessage({ kind: 'error', text: error.message });
    setEmail('');
    setMessage({
      kind: 'ok',
      text: 'Check your inbox: confirm the change from the link we emailed you. Until then your current email stays active.',
    });
  }

  const sameAsCurrent = email.trim().toLowerCase() === (user.email ?? '').toLowerCase();

  return (
    <Section icon={<Mail size={17} />} title="Email" description="Used to log in to Orbit.">
      <form onSubmit={save} className="space-y-4">
        <Field label="Current email">
          <p className="py-2 text-sm text-gray-800">{user.email}</p>
        </Field>
        <Field label="New email">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="new@example.com"
            className={INPUT}
          />
        </Field>
        <FormFooter message={message}>
          <SaveButton
            disabled={saving || !email.trim() || sameAsCurrent}
            saving={saving}
            label="Change email"
          />
        </FormFooter>
      </form>
    </Section>
  );
}

// ---------------------------------------------------------------------------
// Password: we can't SHOW the current password (Supabase only stores a hash of
// it). To change it we first re-check the current one, so someone using your
// unlocked laptop can't silently lock you out.
// ---------------------------------------------------------------------------
const MIN_PASSWORD = 8;

function PasswordSection({ user }: { user: User }) {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<Message>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    if (next.length < MIN_PASSWORD)
      return setMessage({ kind: 'error', text: `Use at least ${MIN_PASSWORD} characters.` });
    if (next !== confirm) return setMessage({ kind: 'error', text: "The new passwords don't match." });
    if (next === current) return setMessage({ kind: 'error', text: 'Choose a password different from the current one.' });

    setSaving(true);
    const supabase = createClient();

    // 1. Prove you know the current password (re-login with it).
    const check = await supabase.auth.signInWithPassword({ email: user.email ?? '', password: current });
    if (check.error) {
      setSaving(false);
      return setMessage({ kind: 'error', text: 'Your current password is incorrect.' });
    }

    // 2. Now set the new one.
    const { error } = await supabase.auth.updateUser({ password: next });
    setSaving(false);
    if (error) return setMessage({ kind: 'error', text: error.message });

    setCurrent('');
    setNext('');
    setConfirm('');
    setMessage({ kind: 'ok', text: 'Password changed.' });
  }

  return (
    <Section icon={<KeyRound size={17} />} title="Password" description="Your password is never shown, only changed.">
      <form onSubmit={save} className="space-y-4">
        <Field label="Current password">
          <input
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            className={INPUT}
          />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="New password">
            <input
              type="password"
              autoComplete="new-password"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              className={INPUT}
            />
          </Field>
          <Field label="Confirm new password">
            <input
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className={INPUT}
            />
          </Field>
        </div>
        <FormFooter message={message}>
          <SaveButton
            disabled={saving || !current || !next || !confirm}
            saving={saving}
            label="Change password"
          />
        </FormFooter>
      </form>
    </Section>
  );
}

// ---------------------------------------------------------------------------
// Read-only facts about the account.
// ---------------------------------------------------------------------------
function AccountSection({ user }: { user: User }) {
  return (
    <Section icon={<ShieldCheck size={17} />} title="Account" description="Details from your login account.">
      <dl className="grid gap-4 text-sm sm:grid-cols-2">
        <Info label="Member since" value={formatDate(user.created_at)} />
        <Info label="Last sign-in" value={formatDate(user.last_sign_in_at)} />
        <Info label="Email confirmed" value={user.email_confirmed_at ? 'Yes' : 'Not yet'} />
      </dl>
    </Section>
  );
}

// ---------------------------------------------------------------------------
// Small building blocks shared by the sections above.
// ---------------------------------------------------------------------------
const INPUT =
  'w-full rounded-lg border px-3 py-2 text-sm outline-none focus:border-gray-400 focus:ring-2 focus:ring-gray-100';

function Section({
  icon,
  title,
  description,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border bg-white shadow-sm">
      <div className="border-b px-6 py-4">
        <h2 className="flex items-center gap-2 font-semibold">
          {icon}
          {title}
        </h2>
        <p className="mt-0.5 text-xs text-gray-500">{description}</p>
      </div>
      <div className="px-6 py-5">{children}</div>
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-gray-600">{label}</span>
      {children}
    </label>
  );
}

function FormFooter({ message, children }: { message: Message; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <p className={`text-sm ${message?.kind === 'error' ? 'text-red-600' : 'text-green-700'}`}>
        {message?.text}
      </p>
      {children}
    </div>
  );
}

function SaveButton({ disabled, saving, label = 'Save' }: { disabled: boolean; saving: boolean; label?: string }) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className="shrink-0 rounded-lg bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
    >
      {saving ? 'Saving…' : label}
    </button>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium text-gray-500">{label}</dt>
      <dd className="mt-0.5 text-gray-800">{value}</dd>
    </div>
  );
}
