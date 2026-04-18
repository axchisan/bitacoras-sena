import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { Sidebar } from "./components/layout/Sidebar";
import Dashboard from "./pages/Dashboard";
import BitacoraList from "./pages/BitacoraList";
import BitacoraDetail from "./pages/BitacoraDetail";
import WorkItems from "./pages/WorkItems";
import Settings from "./pages/Settings";

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <div className="flex min-h-screen bg-gray-950">
          <Sidebar />
          <main className="flex-1 sm:ml-60 p-4 sm:p-6 lg:p-8 pb-20 sm:pb-8 max-w-6xl">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/bitacoras" element={<BitacoraList />} />
              <Route path="/bitacoras/:id" element={<BitacoraDetail />} />
              <Route path="/work-items" element={<WorkItems />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1f2937",
            color: "#f3f4f6",
            border: "1px solid #374151",
            borderRadius: "0.5rem",
            fontSize: "13px",
          },
        }}
      />
    </QueryClientProvider>
  );
}
