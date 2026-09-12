'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { MessageCircle, X } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  action?: string | null;
  params?: Record<string, any>;
  confirmed?: boolean;
  cancelled?: boolean;
};

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  function sendMessage() {
    if (!input.trim()) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    fetch(`${API_URL}/api/v1/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage.content }),
    })
      .then((res) => res.json())
      .then((data) => {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: data.message,
            action: data.action,
            params: data.params,
          },
        ]);
      })
      .finally(() => setLoading(false));
  }

  function confirmAction(index: number) {
    const message = messages[index];

    fetch(`${API_URL}/api/v1/agent/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: message.action, params: message.params }),
    })
      .then((res) => res.json())
      .then((data) => {
        setMessages((prev) => [
          ...prev.map((m, i) => (i === index ? { ...m, confirmed: true } : m)),
          { role: 'assistant', content: data.message },
        ]);
      });
  }

  function cancelAction(index: number) {
    setMessages((prev) =>
      prev.map((m, i) => (i === index ? { ...m, cancelled: true } : m))
    );
  }

  return (
    <>
      {open && (
        <div className="fixed bottom-24 right-6 z-50 flex h-[500px] w-96 flex-col overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-neutral-100 px-4 py-3">
            <span className="text-sm font-semibold text-neutral-900">Assistant</span>
            <button onClick={() => setOpen(false)} className="text-neutral-400 hover:text-neutral-600">
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.length === 0 && (
              <p className="text-xs text-neutral-400">
                Try: &quot;add a meeting tomorrow at 9am called Team Standup&quot;
              </p>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
              >
                <div
                  className={
                    message.role === 'user'
                      ? 'max-w-[80%] rounded-2xl bg-black px-3 py-2 text-sm text-white'
                      : 'max-w-[80%] rounded-2xl bg-neutral-50 px-3 py-2 text-sm text-neutral-800'
                  }
                >
                  {message.role === 'assistant' ? (
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  ) : (
                    message.content
                  )}

                  {message.action && !message.confirmed && !message.cancelled && (
                    <div className="mt-2 flex gap-2">
                      <button
                        onClick={() => confirmAction(index)}
                        className="rounded-lg bg-black px-2.5 py-1 text-xs font-medium text-white hover:bg-gray-800"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => cancelAction(index)}
                        className="rounded-lg border border-neutral-300 px-2.5 py-1 text-xs font-medium text-neutral-600 hover:bg-neutral-100"
                      >
                        Cancel
                      </button>
                    </div>
                  )}

                  {message.cancelled && (
                    <p className="mt-1 text-xs italic text-neutral-400">Cancelled</p>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2 border-t border-neutral-100 p-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask AURA..."
              className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-400"
            />
            <button
              onClick={sendMessage}
              disabled={loading}
              className="rounded-lg bg-black px-3 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen((prev) => !prev)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-black text-white shadow-lg hover:bg-gray-800"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </>
  );
}
