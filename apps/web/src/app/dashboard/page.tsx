'use client';

import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  ExternalLink,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { PageHeader } from '@/src/components/layout/page-header';
import { apiFetch } from '@/src/lib/api';
import { createClient } from '@/src/lib/supabase/client';

// ---------------------------------------------------------------------------
// The shape of GET /api/v1/today. It mirrors the Pydantic models in today.py,
// so TypeScript warns us if we use a field the backend doesn't send.
// ---------------------------------------------------------------------------
type Urgency = 'high' | 'medium' | 'low';

type Priority = {
  title: string;
  why: string;
  action: string;
  urgency: Urgency;
  email_id: string;
};

type MeetingPrep = {
  title: string;
  when: string | null;
  context: string;
  checklist: string[];
  email_id: string | null;
};

type TodayData = {
  generated_at: string;
  date: string;
  connected: { gmail: boolean; calendar: boolean };
  meeting_count: number;
  schedule: { time: string; title: string }[];
  ai_error: string | null; // set when Gemini failed; the rest of the data is still valid
  summary: string;
  priorities: Priority[];
  prep: MeetingPrep[];
};

const URGENCY_STYLE: Record<Urgency, string> = {
  high: 'bg-red-50 text-red-700 ring-red-200',
  medium: 'bg-amber-50 text-amber-700 ring-amber-200',
  low: 'bg-gray-100 text-gray-600 ring-gray-200',
};

// Opens the original email in Gmail.
function gmailLink(emailId: string) {
  return `https://mail.google.com/mail/u/0/#all/${emailId}`;
}

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

function minutesAgo(iso: string) {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  return minutes < 1 ? 'just now' : `${minutes} min ago`;
}

export default function DashboardPage() {
  const [data, setData] = useState<TodayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');

  // Fetches the data. State is only set inside the callbacks (after the response),
  // so it's safe to call from useEffect. refresh=true skips the 30-minute cache.
  function fetchToday(refresh = false) {
    apiFetch(`/api/v1/today${refresh ? '?refresh=true' : ''}`)
      .then(async (res) => {
        const body = await res.json();
        // fetch() only rejects on network failure; a 503 still "succeeds",
        // so check res.ok and show the backend's message.
        if (!res.ok) throw new Error(body.detail ?? 'Something went wrong');
        setData(body);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }

  // For buttons: show the spinner, clear old errors, then fetch.
  function reload(refresh: boolean) {
    setLoading(true);
    setError(null);
    fetchToday(refresh);
  }

  // Runs once when the page opens. `loading` already starts as true.
  useEffect(() => {
    fetchToday();
    createClient()
      .auth.getUser()
      .then(({ data }) => {
        const email = data.user?.email ?? '';
        setName(data.user?.user_metadata?.full_name ?? email.split('@')[0]);
      });
  }, []);

  const highCount = data?.priorities.filter((p) => p.urgency === 'high').length ?? 0;

  return (
    <div className="min-h-screen">
      {/* Date moved into the subtitle: 2 lines, so this header has the same height as every other page. */}
      <PageHeader
        width="max-w-7xl"
        title={`${greeting()}${name ? `, ${name}` : ''}`}
        subtitle={data ? `${data.date} · Here's what matters today.` : "Here's what matters today."}
        actions={
          <>
            {data && !loading && (
              <span className="text-xs text-gray-400">Updated {minutesAgo(data.generated_at)}</span>
            )}
            <button
              onClick={() => reload(true)}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
              {loading ? 'Updating…' : 'Refresh'}
            </button>
          </>
        }
      />

      <div className="mx-auto max-w-7xl space-y-6 p-8">
        {error && (
          <div className="flex items-center justify-between rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
            <button onClick={() => reload(false)} className="font-medium underline">
              Try again
            </button>
          </div>
        )}

        {loading && !data && <LoadingState />}

        {data && (
          <>
            {/* Numbers: all counted by code, not guessed by the AI */}
            <div className="grid gap-4 md:grid-cols-3">
              <StatCard
                icon={<CalendarDays size={18} />}
                label="Meetings"
                value={String(data.meeting_count)}
                description="Today"
              />
              <StatCard
                icon={<CheckCircle2 size={18} />}
                label="Priorities"
                value={data.ai_error ? '–' : String(data.priorities.length)}
                description="Need your attention"
              />
              <StatCard
                icon={<AlertTriangle size={18} />}
                label="Urgent"
                value={data.ai_error ? '–' : String(highCount)}
                description="High urgency"
              />
            </div>

            {data.ai_error && (
              <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                {data.ai_error}
              </p>
            )}

            {(!data.connected.gmail || !data.connected.calendar) && (
              <p className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-600">
                {!data.connected.gmail && 'Gmail is not connected. '}
                {!data.connected.calendar && 'Google Calendar is not connected. '}
                Connect them from the Inbox and Calendar pages for a complete picture.
              </p>
            )}

            {/* AI summary of the day */}
            <section className="rounded-2xl border bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Sparkles size={17} />
                YOUR DAY
              </div>
              <p className="mt-3 text-base leading-7 text-gray-800">{data.summary}</p>
            </section>

            {/* Priorities: one card per email that needs action */}
            <section className="rounded-2xl border bg-white shadow-sm">
              <div className="border-b px-6 py-4">
                <h2 className="font-semibold">Priorities</h2>
                <p className="mt-0.5 text-xs text-gray-500">From your emails in the last 48 hours</p>
              </div>
              {data.priorities.length === 0 ? (
                <p className="px-6 py-8 text-center text-sm text-gray-400">
                  {/* Never claim "nothing important" when the AI simply didn't run. */}
                  {data.ai_error
                    ? 'Priorities will appear here once the AI is available again.'
                    : 'Nothing needs your attention right now.'}
                </p>
              ) : (
                <div className="divide-y">
                  {data.priorities.map((p) => (
                    <PriorityRow key={p.email_id + p.title} priority={p} />
                  ))}
                </div>
              )}
            </section>

            {/* Meeting / interview prep: only shown when there is something to prepare */}
            {data.prep.length > 0 && (
              <section className="space-y-4">
                {data.prep.map((item) => (
                  <PrepCard key={item.title} prep={item} />
                ))}
              </section>
            )}

            {/* Today's real calendar */}
            <section className="rounded-2xl border bg-white shadow-sm">
              <div className="border-b px-6 py-4">
                <h2 className="font-semibold">Today</h2>
              </div>
              {data.schedule.length === 0 ? (
                <p className="px-6 py-8 text-center text-sm text-gray-400">No meetings today.</p>
              ) : (
                <div className="divide-y">
                  {data.schedule.map((item, i) => (
                    <ScheduleItem key={i} time={item.time} title={item.title} />
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="rounded-2xl border bg-white p-10 text-center shadow-sm">
      <RefreshCw size={22} className="mx-auto animate-spin text-gray-400" />
      <p className="mt-4 text-sm font-medium text-gray-700">Reading your emails and calendar…</p>
      <p className="mt-1 text-xs text-gray-400">
        The first load can take up to a minute. After that it&apos;s instant for 30 minutes.
      </p>
    </div>
  );
}

function PriorityRow({ priority }: { priority: Priority }) {
  return (
    <div className="flex gap-4 px-6 py-4">
      <span
        className={`h-fit shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize ring-1 ${URGENCY_STYLE[priority.urgency]}`}
      >
        {priority.urgency}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-900">{priority.title}</p>
        <p className="mt-0.5 text-sm text-gray-500">{priority.why}</p>
        <p className="mt-2 text-sm text-gray-800">
          <span className="font-medium">Next step: </span>
          {priority.action}
        </p>
      </div>
      <a
        href={gmailLink(priority.email_id)}
        target="_blank"
        rel="noopener noreferrer"
        title="Open in Gmail"
        className="h-fit rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
      >
        <ExternalLink size={16} />
      </a>
    </div>
  );
}

function PrepCard({ prep }: { prep: MeetingPrep }) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 text-sm font-medium">
        <ClipboardList size={17} />
        PREPARE
      </div>
      <h3 className="mt-3 text-lg font-semibold">{prep.title}</h3>
      {prep.when && <p className="mt-0.5 text-sm text-gray-500">{prep.when}</p>}
      <p className="mt-3 text-sm leading-6 text-gray-700">{prep.context}</p>
      <ul className="mt-4 space-y-2">
        {prep.checklist.map((step) => (
          <li key={step} className="flex gap-2 text-sm text-gray-800">
            <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-gray-400" />
            {step}
          </li>
        ))}
      </ul>
      {prep.email_id && (
        <a
          href={gmailLink(prep.email_id)}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-1 text-sm font-medium hover:underline"
        >
          Open email <ExternalLink size={14} />
        </a>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  description,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        {icon}
        {label}
      </div>
      <div className="mt-4 text-2xl font-semibold">{value}</div>
      <p className="mt-1 text-xs text-gray-500">{description}</p>
    </div>
  );
}

function ScheduleItem({ time, title }: { time: string; title: string }) {
  return (
    <div className="flex items-center gap-6 px-6 py-4">
      <span className="w-14 text-sm font-medium text-gray-500">{time}</span>
      <div className="h-2 w-2 rounded-full bg-black" />
      <p className="flex-1 text-sm font-medium">{title}</p>
    </div>
  );
}
