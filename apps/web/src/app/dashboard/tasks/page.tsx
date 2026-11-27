'use client';

import { Check, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { PageHeader } from '@/src/components/layout/page-header';
import { apiFetch } from '@/src/lib/api';

// Same fields as TaskOut in tasks.py.
type Task = {
  id: number;
  title: string;
  notes: string | null;
  due_date: string | null; // "2026-12-01"
  done: boolean;
  created_at: string;
};

// The fields PATCH accepts (TaskUpdate in tasks.py).
type TaskChanges = Partial<Pick<Task, 'title' | 'notes' | 'due_date' | 'done'>>;

const JSON_HEADERS = { 'Content-Type': 'application/json' };

// Today as "YYYY-MM-DD" in the user's own time zone (en-CA happens to use that format).
function todayString() {
  return new Date().toLocaleDateString('en-CA');
}

function formatDue(due: string) {
  if (due === todayString()) return 'Today';
  // "T00:00:00" makes JS read it as LOCAL midnight; without it, it's UTC and can show the wrong day.
  return new Date(`${due}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}

// Earliest due date first, tasks without a date last, then newest first. Same order as the API.
function compareTasks(a: Task, b: Task) {
  if (a.due_date !== b.due_date) {
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return a.due_date < b.due_date ? -1 : 1;
  }
  return b.created_at.localeCompare(a.created_at);
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState(''); // what's typed in the "Add" box
  const [dueDate, setDueDate] = useState(''); // the date picker ('' = no date)

  // Load the tasks once when the page opens (state is only set inside the callbacks).
  useEffect(() => {
    apiFetch('/api/v1/tasks')
      .then(async (res) => {
        if (!res.ok) throw new Error("Couldn't load your tasks.");
        setTasks(await res.json());
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function addTask(e: React.FormEvent) {
    e.preventDefault(); // stop the form from reloading the page
    const trimmed = title.trim();
    if (!trimmed) return;

    const res = await apiFetch('/api/v1/tasks', {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({ title: trimmed, due_date: dueDate || null }),
    });
    if (!res.ok) return setError("Couldn't add the task.");

    const created: Task = await res.json();
    setTasks((prev) => [created, ...prev]);
    setTitle('');
    setDueDate('');
  }

  async function updateTask(id: number, changes: TaskChanges) {
    const res = await apiFetch(`/api/v1/tasks/${id}`, {
      method: 'PATCH',
      headers: JSON_HEADERS,
      body: JSON.stringify(changes), // only what changed, e.g. {"done": true}
    });
    if (!res.ok) return setError("Couldn't save the change.");

    const updated: Task = await res.json();
    setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
  }

  async function deleteTask(id: number) {
    const res = await apiFetch(`/api/v1/tasks/${id}`, { method: 'DELETE' });
    if (!res.ok) return setError("Couldn't delete the task.");
    setTasks((prev) => prev.filter((t) => t.id !== id));
  }

  const open = tasks.filter((t) => !t.done).sort(compareTasks);
  const completed = tasks.filter((t) => t.done).sort(compareTasks);

  return (
    <div className="min-h-screen">
      <PageHeader title="Tasks" subtitle={`${open.length} open · ${completed.length} done`} />

      <div className="mx-auto max-w-3xl space-y-6 p-8">
        {error && (
          <div className="flex items-center justify-between rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
            <button onClick={() => setError(null)} className="font-medium underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Add a task */}
        <form onSubmit={addTask} className="flex gap-2 rounded-2xl border bg-white p-3 shadow-sm">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Add a task…"
            maxLength={200}
            className="min-w-0 flex-1 rounded-lg px-3 py-2 text-sm outline-none"
          />
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="rounded-lg border px-2 py-2 text-sm text-gray-600"
          />
          <button
            type="submit"
            disabled={!title.trim()}
            className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            Add
          </button>
        </form>

        {loading ? (
          <p className="text-center text-sm text-gray-400">Loading tasks…</p>
        ) : (
          <>
            <section className="rounded-2xl border bg-white shadow-sm">
              {open.length === 0 ? (
                <p className="px-6 py-8 text-center text-sm text-gray-400">Nothing to do. Add a task above.</p>
              ) : (
                <div className="divide-y">
                  {open.map((task) => (
                    <TaskRow key={task.id} task={task} onUpdate={updateTask} onDelete={deleteTask} />
                  ))}
                </div>
              )}
            </section>

            {completed.length > 0 && (
              <section>
                <h2 className="mb-2 px-1 text-sm font-medium text-gray-500">Completed</h2>
                <div className="divide-y rounded-2xl border bg-white shadow-sm">
                  {completed.map((task) => (
                    <TaskRow key={task.id} task={task} onUpdate={updateTask} onDelete={deleteTask} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function TaskRow({
  task,
  onUpdate,
  onDelete,
}: {
  task: Task;
  onUpdate: (id: number, changes: TaskChanges) => void;
  onDelete: (id: number) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(task.title);
  const overdue = !task.done && task.due_date !== null && task.due_date < todayString();

  function startEditing() {
    setDraft(task.title);
    setEditing(true);
  }

  function save() {
    setEditing(false);
    const trimmed = draft.trim();
    if (trimmed && trimmed !== task.title) onUpdate(task.id, { title: trimmed });
  }

  return (
    <div className="group flex items-center gap-3 px-6 py-3">
      <button
        onClick={() => onUpdate(task.id, { done: !task.done })}
        aria-label={task.done ? 'Mark as not done' : 'Mark as done'}
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border ${
          task.done ? 'border-black bg-black text-white' : 'border-gray-300 hover:border-gray-500'
        }`}
      >
        {task.done && <Check size={13} />}
      </button>

      <div className="min-w-0 flex-1">
        {editing ? (
          <input
            autoFocus
            value={draft}
            maxLength={200}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={save}
            onKeyDown={(e) => {
              if (e.key === 'Enter') save();
              if (e.key === 'Escape') setEditing(false);
            }}
            className="w-full rounded-md border px-2 py-1 text-sm outline-none"
          />
        ) : (
          <button
            onClick={startEditing}
            title="Click to edit"
            className={`w-full truncate text-left text-sm ${task.done ? 'text-gray-400 line-through' : 'text-gray-900'}`}
          >
            {task.title}
          </button>
        )}
      </div>

      {task.due_date && (
        <span className={`shrink-0 text-xs ${overdue ? 'font-medium text-red-600' : 'text-gray-500'}`}>
          {overdue && 'Overdue · '}
          {formatDue(task.due_date)}
        </span>
      )}

      <button
        onClick={() => onDelete(task.id)}
        aria-label="Delete task"
        className="shrink-0 rounded-md p-1.5 text-gray-400 opacity-0 hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 focus:opacity-100"
      >
        <Trash2 size={15} />
      </button>
    </div>
  );
}
