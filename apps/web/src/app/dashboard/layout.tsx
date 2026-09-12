import { Sidebar } from "@/src/components/layout/sidebar";
import { ChatWidget } from "@/src/components/assistant/ChatWidget";


export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      <main className="min-w-0 flex-1">
        {children}
      </main>

      <ChatWidget />
    </div>
  );
}
