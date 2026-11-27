"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/src/lib/supabase/client";
import { HEADER_HEIGHT } from "@/src/components/layout/page-header";
import {
  Home,
  Inbox,
  CalendarDays,
  CheckSquare,
  Bot,
  Plug,
  Settings,
  Orbit,
  LogOut,
} from "lucide-react";

const mainNavigation = [
  { name: "Today", href: "/dashboard", icon: Home },
  { name: "Inbox", href: "/dashboard/inbox", icon: Inbox },
  { name: "Calendar", href: "/dashboard/calendar", icon: CalendarDays },
  { name: "Tasks", href: "/dashboard/tasks", icon: CheckSquare },
  { name: "AI Assistant", href: "/dashboard/assistant", icon: Bot },
];

const bottomNavigation = [
  { name: "Integrations", href: "/dashboard/integrations", icon: Plug },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

type SidebarUser = { name: string; email: string };

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<SidebarUser | null>(null);

  // Load the logged-in user, and keep it updated: when the name is changed on the
  // Settings page, Supabase fires a "USER_UPDATED" event and the sidebar re-renders.
  useEffect(() => {
    const supabase = createClient();
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      const email = session?.user.email ?? "";
      // Use full_name if one is set (Settings page), otherwise the part of the email before "@".
      const name = session?.user.user_metadata?.full_name || email.split("@")[0];
      setUser({ name, email });
    });
    // Stop listening when the sidebar disappears, so listeners don't pile up.
    return () => listener.subscription.unsubscribe();
  }, []);

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    // sticky top-0: stays pinned to the top of the window while the page content scrolls.
    // shrink-0: never squeezed narrower by wide page content.
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r bg-white">
      {/* Same height as PageHeader, so the two bottom borders form one straight line. */}
      <div className={`flex ${HEADER_HEIGHT} shrink-0 items-center gap-3 border-b px-6`}>
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
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-200 text-sm font-medium uppercase">
            {user?.name.charAt(0) ?? ""}
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">
              {user ? user.name : "Loading…"}
            </p>
            <p className="truncate text-xs text-gray-500">
              {user?.email}
            </p>
          </div>

          <button
            onClick={handleLogout}
            title="Log out"
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-900"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </aside>
  );
}
