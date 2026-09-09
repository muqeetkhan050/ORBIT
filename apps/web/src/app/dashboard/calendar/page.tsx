
'use client'

import { useEffect, useState } from 'react'


const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function CalendarPage() {

  const [connected, setConnected] = useState<boolean | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/api/v1/integrations/google/status`)
      .then((res) => res.json())
      .then((data) => setConnected(data.connected))
      .catch(() => setConnected(false))
  }, [])

  function handleConnect() {

    window.location.href = `${API_URL}/api/v1/integrations/google/connect`
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10">
      <header className="mb-10">
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">
          Calendar
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Your schedule, understood by AURA.
        </p>
      </header>

      {connected === null ? (
        <div className="rounded-2xl border border-neutral-200 bg-white p-10 text-center text-sm text-neutral-400">
          Checking calendar connection…
        </div>
      ) : connected ? (
        <ConnectedCalendar onDisconnect={() => setConnected(false)} />
      ) : (
        <ConnectEmptyState onConnect={handleConnect} />
      )}
    </div>
  )
}

function ConnectEmptyState({ onConnect }: { onConnect: () => void }) {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-10">
      <div className="mx-auto flex max-w-md flex-col items-center text-center">
        <CalendarGlyph />

        <h2 className="mt-6 text-lg font-semibold text-neutral-900">
          Connect your calendar
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-neutral-500">
          Link your Google Calendar so AURA can see your meetings, find open
          time, and prepare you before each one.
        </p>

        <ul className="mt-8 w-full space-y-4 text-left">
          <Benefit
            title="See your week at a glance"
            body="Meetings and focus blocks in one place."
          />
          <Benefit
            title="Find free time instantly"
            body="AURA spots the gaps when you ask it to schedule."
          />
          <Benefit
            title="Walk in prepared"
            body="Context pulled together before each meeting starts."
          />
        </ul>

        <button
          onClick={onConnect}
          className="mt-8 inline-flex items-center gap-3 rounded-lg border border-neutral-300 bg-white px-5 py-2.5 text-sm font-medium text-neutral-800 shadow-sm transition hover:bg-neutral-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:ring-offset-2"
        >
          <GoogleLogo />
          Connect Google Calendar
        </button>

        <p className="mt-4 text-xs text-neutral-400">
          AURA requests read access to your events. You stay in control and can
          disconnect anytime.
        </p>
      </div>
    </div>
  )
}

type CalendarEvent = {
  id: string
  summary?: string
  start?: { date?: string; dateTime?: string }
  end?: { date?: string; dateTime?: string }
}

function ConnectedCalendar({ onDisconnect }: { onDisconnect: () => void }) {
  const [events, setEvents] = useState<CalendarEvent[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/api/v1/integrations/google/events`)
      .then((res) => {
        if (!res.ok) throw new Error('request failed')
        return res.json()
      })
      .then((data) => setEvents(data))
      .catch(() => setError('Could not load your calendar events.'))
  }, [])

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="text-sm font-medium text-neutral-700">
            Google Calendar connected
          </span>
        </div>
        <button
          onClick={onDisconnect}
          className="text-xs font-medium text-neutral-400 hover:text-neutral-600"
        >
          Disconnect
        </button>
      </div>

      <div className="mt-8">
        {error ? (
          <p className="rounded-xl border border-dashed border-neutral-200 p-10 text-center text-sm text-red-500">
            {error}
          </p>
        ) : events === null ? (
          <p className="rounded-xl border border-dashed border-neutral-200 p-10 text-center text-sm text-neutral-400">
            Loading events…
          </p>
        ) : events.length === 0 ? (
          <p className="rounded-xl border border-dashed border-neutral-200 p-10 text-center text-sm text-neutral-400">
            No upcoming events.
          </p>
        ) : (
          <ul className="space-y-3">
            {events.map((event) => (
              <li
                key={event.id}
                className="flex items-center justify-between rounded-lg border border-neutral-100 px-4 py-3"
              >
                <span className="text-sm font-medium text-neutral-800">
                  {event.summary ?? '(No title)'}
                </span>
                <span className="text-xs text-neutral-400">
                  {formatEventTime(event)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function formatEventTime(event: CalendarEvent) {
  const raw = event.start?.dateTime ?? event.start?.date
  if (!raw) return ''

  const date = new Date(raw)

  return event.start?.dateTime
    ? date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
}

function Benefit({ title, body }: { title: string; body: string }) {
  return (
    <li className="flex gap-3">
      <CheckIcon />
      <div>
        <p className="text-sm font-medium text-neutral-800">{title}</p>
        <p className="text-sm text-neutral-500">{body}</p>
      </div>
    </li>
  )
}

/* --- Inline icons (no external icon library needed) --- */

function CalendarGlyph() {
  return (
    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-neutral-900">
      <svg
        width="26"
        height="26"
        viewBox="0 0 24 24"
        fill="none"
        stroke="white"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <path d="M16 2v4M8 2v4M3 10h18" />
      </svg>
    </div>
  )
}

function CheckIcon() {
  return (
    <svg
      className="mt-0.5 h-5 w-5 shrink-0 text-neutral-900"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M20 6L9 17l-5-5" />
    </svg>
  )
}

function GoogleLogo() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z"
      />
    </svg>
  )
}