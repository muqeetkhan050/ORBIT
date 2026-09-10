'use client'

import { useEffect, useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function InboxPage() {
  const [connected, setConnected] = useState<boolean | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/api/v1/integrations/gmail/status`)
      .then((res) => res.json())
      .then((data) => setConnected(data.connected))
      .catch(() => setConnected(false))
  }, [])

  function handleConnect() {
    window.location.href = `${API_URL}/api/v1/integrations/gmail/connect`
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10">
      <header className="mb-10">
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">
          Inbox
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Your email, understood by AURA.
        </p>
      </header>

      {connected === null ? (
        <div className="rounded-2xl border border-neutral-200 bg-white p-10 text-center text-sm text-neutral-400">
          Checking inbox connection…
        </div>
      ) : connected ? (
        <ConnectedInbox onDisconnect={() => setConnected(false)} />
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
        <InboxGlyph />

        <h2 className="mt-6 text-lg font-semibold text-neutral-900">
          Connect your inbox
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-neutral-500">
          Link your Gmail so AURA can see what needs a reply, surface what
          matters, and keep you out of the inbox itself.
        </p>

        <ul className="mt-8 w-full space-y-4 text-left">
          <Benefit
            title="See what needs you"
            body="Important messages surfaced, noise left behind."
          />
          <Benefit
            title="Never miss a reply"
            body="AURA flags threads waiting on you."
          />
          <Benefit
            title="Context before you act"
            body="Related messages pulled together automatically."
          />
        </ul>

        <button
          onClick={onConnect}
          className="mt-8 inline-flex items-center gap-3 rounded-lg border border-neutral-300 bg-white px-5 py-2.5 text-sm font-medium text-neutral-800 shadow-sm transition hover:bg-neutral-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-400 focus-visible:ring-offset-2"
        >
          <GoogleLogo />
          Connect Gmail
        </button>

        <p className="mt-4 text-xs text-neutral-400">
          AURA requests read access to your email. You stay in control and can
          disconnect anytime.
        </p>
      </div>
    </div>
  )
}

type GmailMessage = {
  id: string
  subject: string
  from: string
  snippet: string
  date?: string
}

function ConnectedInbox({ onDisconnect }: { onDisconnect: () => void }) {
  const [messages, setMessages] = useState<GmailMessage[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/api/v1/integrations/gmail/messages`)
      .then((res) => {
        if (!res.ok) throw new Error('request failed')
        return res.json()
      })
      .then((data) => setMessages(data))
      .catch(() => setError('Could not load your inbox.'))
  }, [])

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="text-sm font-medium text-neutral-700">
            Gmail connected
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
        ) : messages === null ? (
          <p className="rounded-xl border border-dashed border-neutral-200 p-10 text-center text-sm text-neutral-400">
            Loading messages…
          </p>
        ) : messages.length === 0 ? (
          <p className="rounded-xl border border-dashed border-neutral-200 p-10 text-center text-sm text-neutral-400">
            No messages.
          </p>
        ) : (
          <ul className="space-y-3">
            {messages.map((message) => (
              <li
                key={message.id}
                className="rounded-lg border border-neutral-100 px-4 py-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-neutral-800">
                    {message.from}
                  </span>
                  <span className="text-xs text-neutral-400">
                    {formatMessageTime(message.date)}
                  </span>
                </div>
                <p className="mt-1 text-sm text-neutral-700">
                  {message.subject || '(No subject)'}
                </p>
                <p className="mt-1 truncate text-xs text-neutral-400">
                  {message.snippet}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function formatMessageTime(date?: string) {
  if (!date) return ''

  return new Date(date).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
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

function InboxGlyph() {
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
        <path d="M22 12h-6l-2 3h-4l-2-3H2" />
        <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
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
