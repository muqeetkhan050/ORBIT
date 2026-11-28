'use client';

import { CalendarDays, CheckCircle2, FileText, Mail, MessageSquare } from 'lucide-react';
import { useEffect, useState } from 'react';
import { PageHeader } from '@/src/components/layout/page-header';
import { apiFetch } from '@/src/lib/api';

// One entry per integration. `apiPath` is set for the ones the backend supports;
// Slack and Notion don't have a backend yet, so their Connect button only shows a notice.
type Integration = {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  apiPath?: string; // e.g. /api/v1/integrations/gmail -> has /status and /connect
};

const INTEGRATIONS: Integration[] = [
  {
    id: 'calendar',
    name: 'Google Calendar',
    description: 'Your meetings on the Today page, and booking events from chat.',
    icon: <CalendarDays size={20} />,
    apiPath: '/api/v1/integrations/google',
  },
  {
    id: 'gmail',
    name: 'Gmail',
    description: 'Email priorities, meeting prep, and sending emails from chat.',
    icon: <Mail size={20} />,
    apiPath: '/api/v1/integrations/gmail',
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Messages and mentions that need your reply.',
    icon: <MessageSquare size={20} />,
  },
  {
    id: 'notion',
    name: 'Notion',
    description: 'Your notes and docs, used as context for prep and answers.',
    icon: <FileText size={20} />,
  },
];

// true = connected, false = not connected, null = still checking
type Statuses = Record<string, boolean | null>;

export default function IntegrationsPage() {
  const [statuses, setStatuses] = useState<Statuses>({});
  const [notice, setNotice] = useState<string | null>(null);

  // Ask the backend whether each supported integration is connected (all in parallel).
  useEffect(() => {
    for (const item of INTEGRATIONS) {
      if (!item.apiPath) continue;
      apiFetch(`${item.apiPath}/status`)
        .then((res) => res.json())
        .then((data) => setStatuses((prev) => ({ ...prev, [item.id]: Boolean(data.connected) })))
        .catch(() => setStatuses((prev) => ({ ...prev, [item.id]: false })));
    }
  }, []);

  function connect(item: Integration) {
    if (!item.apiPath) {
      setNotice(`${item.name} isn't available yet. It's coming soon.`);
      return;
    }
    // Same flow as the Inbox/Calendar pages: get the Google URL (with signed state), then go there.
    apiFetch(`${item.apiPath}/connect`)
      .then((res) => res.json())
      .then((data) => {
        window.location.href = data.url;
      })
      .catch(() => setNotice(`Couldn't start connecting ${item.name}. Try again.`));
  }

  return (
    <div className="min-h-screen">
      <PageHeader title="Integrations" subtitle="Connect the apps Orbit can read and act in." />

      <div className="mx-auto max-w-3xl space-y-4 p-8">
        {notice && (
          <div className="flex items-center justify-between rounded-xl border bg-white px-4 py-3 text-sm text-gray-700">
            {notice}
            <button onClick={() => setNotice(null)} className="font-medium underline">
              OK
            </button>
          </div>
        )}

        <div className="divide-y rounded-2xl border bg-white shadow-sm">
          {INTEGRATIONS.map((item) => (
            <IntegrationRow
              key={item.id}
              item={item}
              // Unsupported ones are simply "not connected"; supported ones start as "checking".
              status={item.apiPath ? (statuses[item.id] ?? null) : false}
              onConnect={() => connect(item)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function IntegrationRow({
  item,
  status,
  onConnect,
}: {
  item: Integration;
  status: boolean | null;
  onConnect: () => void;
}) {
  return (
    <div className="flex items-center gap-4 px-6 py-5">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border bg-gray-50 text-gray-700">
        {item.icon}
      </div>

      <div className="min-w-0 flex-1">
        <p className="font-medium text-gray-900">{item.name}</p>
        <p className="mt-0.5 text-sm text-gray-500">{item.description}</p>
      </div>

      {status === null ? (
        <span className="shrink-0 text-sm text-gray-400">Checking…</span>
      ) : status ? (
        <span className="flex shrink-0 items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-sm font-medium text-green-700 ring-1 ring-green-200">
          <CheckCircle2 size={15} />
          Connected
        </span>
      ) : (
        <button
          onClick={onConnect}
          className="shrink-0 rounded-lg bg-black px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
        >
          Connect
        </button>
      )}
    </div>
  );
}
