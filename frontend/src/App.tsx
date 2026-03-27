import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { CompareRunsPage } from "./pages/CompareRunsPage";
import { HomePage } from "./pages/HomePage";
import { BrokerStatusPage } from "./pages/BrokerStatusPage";
import { LiveExecutionPage } from "./pages/LiveExecutionPage";
import { MetadataPage } from "./pages/MetadataPage";
import { MLResultPage } from "./pages/MLResultPage";
import { MLRunPage } from "./pages/MLRunPage";
import { PaperTradingPage } from "./pages/PaperTradingPage";
import { RunHistoryPage } from "./pages/RunHistoryPage";
import { RunsPage } from "./pages/RunsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { StrategyResultPage } from "./pages/StrategyResultPage";
import { StrategyRunPage } from "./pages/StrategyRunPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="/metadata" element={<MetadataPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/live-execution" element={<LiveExecutionPage />} />
          <Route path="/broker-status" element={<BrokerStatusPage />} />
          <Route path="/strategy" element={<StrategyRunPage />} />
          <Route path="/ml" element={<MLRunPage />} />
          <Route path="/paper" element={<PaperTradingPage />} />
          <Route path="/history" element={<RunHistoryPage />} />
          <Route path="/compare" element={<CompareRunsPage />} />
          <Route path="/runs" element={<RunsPage />} />
          <Route path="/runs/:runId/strategy" element={<StrategyResultPage />} />
          <Route path="/runs/:runId/ml" element={<MLResultPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
