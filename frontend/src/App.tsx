import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { MainLayout } from "./components/layout/MainLayout";
import { OverviewPage } from "./pages/OverviewPage";
import { DriversPage } from "./pages/DriversPage";
import { VehiclesPage } from "./pages/VehiclesPage";
import { OrdersPage } from "./pages/OrdersPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { LoginPage } from "./pages/LoginPage";
import { getMe } from "./api/fleetApi";

function App() {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem("auth_token");
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function verifyToken() {
      const storedToken = localStorage.getItem("auth_token");
      if (!storedToken) {
        setToken(null);
        setLoading(false);
        return;
      }

      try {
        await getMe(storedToken);
        setToken(storedToken);
      } catch (err) {
        // Token invalide ou expiré
        console.error("Token invalide, déconnexion...", err);
        localStorage.removeItem("auth_token");
        setToken(null);
      } finally {
        setLoading(false);
      }
    }
    verifyToken();
  }, []);

  const handleLogin = (newToken: string) => {
    localStorage.setItem("auth_token", newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    setToken(null);
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            token ? (
              <Navigate to="/" replace />
            ) : (
              <LoginPage onLogin={handleLogin} />
            )
          }
        />
        <Route
          path="/"
          element={
            token ? (
              <MainLayout onLogout={handleLogout}>
                <OverviewPage token={token} />
              </MainLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/drivers"
          element={
            token ? (
              <MainLayout onLogout={handleLogout}>
                <DriversPage token={token} />
              </MainLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/vehicles"
          element={
            token ? (
              <MainLayout onLogout={handleLogout}>
                <VehiclesPage token={token} />
              </MainLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/orders"
          element={
            token ? (
              <MainLayout onLogout={handleLogout}>
                <OrdersPage token={token} />
              </MainLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/analytics"
          element={
            token ? (
              <MainLayout onLogout={handleLogout}>
                <AnalyticsPage token={token} />
              </MainLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/settings"
          element={
            token ? (
              <MainLayout onLogout={handleLogout}>
                <SettingsPage token={token} />
              </MainLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
