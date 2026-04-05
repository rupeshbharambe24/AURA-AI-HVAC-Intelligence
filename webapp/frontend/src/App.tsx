import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import Overview from "./pages/Overview";
import DataExplorer from "./pages/DataExplorer";
import Models from "./pages/Models";
import ModelDetail from "./pages/ModelDetail";
import Experiments from "./pages/Experiments";
import Forecasting from "./pages/Forecasting";
import Anomalies from "./pages/Anomalies";
import Optimization from "./pages/Optimization";
import MarketShare from "./pages/MarketShare";
import SettingsPage from "./pages/SettingsPage";
import Help from "./pages/Help";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Overview />} />
            <Route path="/data" element={<DataExplorer />} />
            <Route path="/models" element={<Models />} />
            <Route path="/models/:modelId" element={<ModelDetail />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/forecasting" element={<Forecasting />} />
            <Route path="/anomalies" element={<Anomalies />} />
            <Route path="/optimization" element={<Optimization />} />
            <Route path="/market-share" element={<MarketShare />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/help" element={<Help />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
