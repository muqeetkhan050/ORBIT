'use client';

import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";
import {useState} from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
export default function DashboardPage() {


  const [briefing, setBriefing] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  function handlePrepare(){
    setLoading(true);
    fetch(`${API_URL}/api/v1/agent/briefing`)
    .then ((res)=>res.json())
    .then((data)=>setBriefing(data.briefing))
    .finally(()=>setLoading(false));
  }
  return (
    <div className="min-h-screen">
      <header className="border-b bg-white px-8 py-5">
        <div className="mx-auto max-w-7xl">
          <p className="text-sm text-gray-500">
            Tuesday, September 8, 2026
          </p>

          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Good morning, Muqeet 👋
          </h1>

          <p className="mt-1 text-sm text-gray-500">
            Here's what matters today.
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-6 p-8">

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-3">
          <StatCard
            icon={<CalendarDays size={18} />}
            label="Meetings"
            value="4"
            description="Today"
          />

          <StatCard
            icon={<Clock3 size={18} />}
            label="Focus time"
            value="2h 40m"
            description="Available today"
          />

          <StatCard
            icon={<CheckCircle2 size={18} />}
            label="Priorities"
            value="3"
            description="Need your attention"
          />
        </div>

        {/* AI recommendation */}
        <section className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Sparkles size={17} />
            NEXT BEST ACTION
          </div>

          <div className="mt-5 flex flex-col justify-between gap-5 md:flex-row md:items-end">
            <div>
              <h2 className="text-xl font-semibold">
                Prepare for your 2 PM meeting
              </h2>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-500">
                ORBIT will search your calendar, emails, Slack
                conversations, and previous interactions to build
                a meeting briefing.
              </p>

              <div className="mt-4 flex gap-2">
                <span className="rounded-full bg-gray-100 px-3 py-1 text-xs">
                  Calendar
                </span>

                <span className="rounded-full bg-gray-100 px-3 py-1 text-xs">
                  Gmail
                </span>

                <span className="rounded-full bg-gray-100 px-3 py-1 text-xs">
                  Slack
                </span>
              </div>
            </div>

            <button
              onClick={handlePrepare}
              disabled={loading}
              className="flex shrink-0 items-center justify-center gap-2 rounded-lg bg-black px-4 py-2.5 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-50"
            >
              {loading ? "Preparing…" : "Prepare me"}
              <ArrowUpRight size={16} />
            </button>
          </div>

          {briefing && (
            <p className="mt-4 whitespace-pre-line rounded-lg bg-gray-50 p-4 text-sm text-gray-700">
              {briefing}
            </p>
          )}
        </section>

        {/* Today's schedule */}
        <section className="rounded-2xl border bg-white shadow-sm">
          <div className="border-b px-6 py-4">
            <h2 className="font-semibold">Today</h2>
          </div>

          <div className="divide-y">
            <ScheduleItem
              time="09:00"
              title="Product meeting"
              type="Meeting"
            />

            <ScheduleItem
              time="10:00"
              title="Deep work"
              type="Focus"
            />

            <ScheduleItem
              time="12:00"
              title="Lunch"
              type="Personal"
            />

            <ScheduleItem
              time="14:00"
              title="Client meeting"
              type="Meeting"
              highlight
            />

            <ScheduleItem
              time="16:00"
              title="Deep work"
              type="Focus"
            />
          </div>
        </section>

        {/* AI activity */}
        <section className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold">AI activity</h2>
              <p className="mt-1 text-sm text-gray-500">
                What ORBIT has done recently.
              </p>
            </div>

            <a
              href="/dashboard/assistant"
              className="text-sm font-medium hover:underline"
            >
              View all
            </a>
          </div>

          <div className="mt-5 space-y-4">
            <Activity text="Checked your calendar" />
            <Activity text="Analyzed today's priorities" />
            <Activity text="Found 3 unanswered emails" />
          </div>
        </section>
      </div>
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

      <div className="mt-4 text-2xl font-semibold">
        {value}
      </div>

      <p className="mt-1 text-xs text-gray-500">
        {description}
      </p>
    </div>
  );
}

function ScheduleItem({
  time,
  title,
  type,
  highlight = false,
}: {
  time: string;
  title: string;
  type: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-6 px-6 py-4 ${
        highlight ? "bg-gray-50" : ""
      }`}
    >
      <span className="w-14 text-sm font-medium text-gray-500">
        {time}
      </span>

      <div className="h-2 w-2 rounded-full bg-black" />

      <div className="flex-1">
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-0.5 text-xs text-gray-500">{type}</p>
      </div>
    </div>
  );
}

function Activity({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="h-2 w-2 rounded-full bg-green-500" />
      <span>{text}</span>
      <span className="ml-auto text-xs text-gray-400">
        Just now
      </span>
    </div>
  );
}
