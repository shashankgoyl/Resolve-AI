import { Routes, Route, useLocation } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { DashboardPage } from "@/pages/DashboardPage";
import { InboxPage } from "@/pages/InboxPage";
import { TicketWorkspacePage } from "@/pages/TicketWorkspacePage";
import { IntegrationsPage } from "@/pages/IntegrationsPage";
import { AuditLogsPage } from "@/pages/AuditLogsPage";

const TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/inbox": "Inbox",
  "/integrations": "Integrations",
  "/audit-logs": "Audit Logs",
};

function useTitle() {
  const { pathname } = useLocation();
  if (pathname.startsWith("/tickets/")) return "Ticket Workspace";
  return TITLES[pathname] || "Resolve AI";
}

export default function App() {
  const title = useTitle();

  return (
    <div className="flex h-screen w-full overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar title={title} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/inbox" element={<InboxPage />} />
            <Route path="/tickets/:ticketId" element={<TicketWorkspacePage />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="/audit-logs" element={<AuditLogsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
