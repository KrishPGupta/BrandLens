import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Outlet, useLocation } from "react-router-dom";
import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";
import DashboardLayout from "./components/dashboard/DashboardLayout";
import Home from "./pages/Home";
import OverviewPage from "./pages/dashboard/OverviewPage";
import TrendsPage from "./pages/dashboard/TrendsPage";
import BotsPage from "./pages/dashboard/BotsPage";
import ExplanationsPage from "./pages/dashboard/ExplanationsPage";
import ModelsPage from "./pages/dashboard/ModelsPage";

function ScrollToHash() {
  const { hash, pathname } = useLocation();
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [hash, pathname]);
  return null;
}

function SiteLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToHash />
      <Routes>
        <Route element={<SiteLayout />}>
          <Route path="/" element={<Home />} />
        </Route>
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<OverviewPage />} />
          <Route path="trends" element={<TrendsPage />} />
          <Route path="bots" element={<BotsPage />} />
          <Route path="explanations" element={<ExplanationsPage />} />
          <Route path="models" element={<ModelsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
