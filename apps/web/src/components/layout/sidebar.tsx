"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Inbox,
  CalendarDays,
  CheckSquare,
  Target,
  Users,
  Brain,
  Bot,
  Zap,
  BarChart3,
  Plug,
  Settings,
  Orbit,
} from "lucide-react";

const mainNavigation = [
  { name: "Today", href: "/dashboard", icon: Home },
  { name: "Inbox", href: "/dashboard/inbox", icon: Inbox },
  { name: "Calendar", href: "/dashboard/calendar", icon: CalendarDays },
  { name: "Tasks", href: "/dashboard/tasks", icon: CheckSquare },
  { name: "Goals", href: "/dashboard/goals", icon: Target },
  { name: "People", href: "/dashboard/people", icon: Users },
  { name: "Knowledge", href: "/dashboard/knowledge", icon: Brain },
  { name: "AI Assistant", href: "/dashboard/assistant", icon: Bot },
  { name: "Automations", href: "/dashboard/automations", icon: Zap },
  { name: "Insights", href: "/dashboard/insights", icon: BarChart3 },
];

const bottomNavigation = [
  { name: "Integrations", href: "/dashboard/integrations", icon: Plug },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-white">
      <div className="flex h-16 items-center gap-3 border-b px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-black text-white">
          <Orbit size={18} />
        </div>

        <span className="text-lg font-semibold tracking-tight">
          ORBIT
        </span>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {mainNavigation.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                active
                  ? "bg-black text-white"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
            >
              <Icon size={18} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-1 border-t p-4">
        {bottomNavigation.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                active
                  ? "bg-black text-white"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
            >
              <Icon size={18} />
              {item.name}
            </Link>
          );
        })}
      </div>

      <div className="border-t p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-200 text-sm font-medium">
            M
          </div>

          <div className="min-w-0">
            <p className="truncate text-sm font-medium">
              Muqeet
            </p>
            <p className="truncate text-xs text-gray-500">
              Personal workspace
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
