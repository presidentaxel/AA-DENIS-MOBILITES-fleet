import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DriverTableModern } from "../components/DriverTableModern";
import { DriverStats } from "../components/DriverStats";
import { OrdersList } from "../components/OrdersList";
import {
  getBoltDrivers,
  getBoltDriverEarnings,
  getBoltOrders,
  getBoltVehicles,
} from "../api/fleetApi";

type DashboardPageProps = {
  token: string;
  onLogout: () => void;
};

export function DashboardPage({ token, onLogout }: DashboardPageProps) {
  const [drivers, setDrivers] = useState<any[]>([]);
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<"drivers" | "vehicles">("drivers");
  const [driverEarnings, setDriverEarnings] = useState<any>(null);
  const [driverOrders, setDriverOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Date range
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().slice(0, 10));

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [driversData, vehiclesData] = await Promise.all([
          getBoltDrivers(token, { limit: 100 }),
          getBoltVehicles(token, { limit: 100 }),
        ]);
        setDrivers(driversData);
        setVehicles(vehiclesData);
        if (driversData.length && !selectedDriver) {
          setSelectedDriver(driversData[0].id);
        }
      } catch (err: any) {
        setError(err?.response?.data?.detail || err?.message || "Erreur de chargement");
        if (err?.response?.status === 401) {
          onLogout();
        }
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [token]);

  useEffect(() => {
    async function fetchDriverDetails() {
      if (!selectedDriver) return;
      setLoading(true);
      setError(null);
      try {
        const [earningsData, ordersData] = await Promise.all([
          getBoltDriverEarnings(token, selectedDriver, dateFrom, dateTo).catch(() => null),
          getBoltOrders(token, dateFrom, dateTo, selectedDriver).catch(() => []),
        ]);
        setDriverEarnings(earningsData);
        setDriverOrders(ordersData);
      } catch (err: any) {
        setError(err?.response?.data?.detail || err?.message || "Erreur de chargement");
      } finally {
        setLoading(false);
      }
    }
    fetchDriverDetails();
  }, [token, selectedDriver, dateFrom, dateTo]);

  const selectedDriverObj = drivers.find((d) => d.id === selectedDriver);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="flex items-center justify-between">
          <h1>AA Denis Mobilités – Fleet Dashboard</h1>
          <button className="btn btn-secondary" onClick={onLogout}>
            Déconnexion
          </button>
        </div>
      </header>

      <main className="app-content">
        {error && (
          <div className="card" style={{ background: "#fee2e2", borderColor: "#ef4444", marginBottom: "1rem" }}>
            <div className="text-error">⚠️ {error}</div>
          </div>
        )}

        {/* Date Range Selector */}
        <div className="card mb-4">
          <div className="flex items-center gap-4">
            <div className="form-group" style={{ margin: 0, minWidth: "200px" }}>
              <label className="form-label">Période : Du</label>
              <input
                type="date"
                className="form-input"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="form-group" style={{ margin: 0, minWidth: "200px" }}>
              <label className="form-label">Au</label>
              <input
                type="date"
                className="form-input"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${selectedView === "drivers" ? "active" : ""}`}
            onClick={() => setSelectedView("drivers")}
          >
            👥 Chauffeurs
          </button>
          <button
            className={`tab ${selectedView === "vehicles" ? "active" : ""}`}
            onClick={() => setSelectedView("vehicles")}
          >
            🚗 Véhicules
          </button>
        </div>

        {selectedView === "drivers" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Liste des chauffeurs */}
            <div className="lg:col-span-1">
              <DriverTableModern
                drivers={drivers}
                selected={selectedDriver}
                onSelect={setSelectedDriver}
                loading={loading}
              />
            </div>

            {/* Détails du chauffeur sélectionné */}
            <div className="lg:col-span-2">
              {selectedDriverObj && driverEarnings ? (
                <>
                  <div className="card mb-4">
                    <div className="card-header">
                      <h2 className="card-title">
                        {selectedDriverObj.first_name} {selectedDriverObj.last_name}
                      </h2>
                    </div>
                    <div className="card-body">
                      <div className="flex gap-4">
                        <div>
                          <strong>Email:</strong> {selectedDriverObj.email || "—"}
                        </div>
                        <div>
                          <strong>Téléphone:</strong> {selectedDriverObj.phone || "—"}
                        </div>
                      </div>
                    </div>
                  </div>

                  {driverEarnings && <DriverStats earnings={driverEarnings} loading={loading} />}
                  <OrdersList orders={driverOrders} loading={loading} />
                </>
              ) : (
                <div className="card">
                  <div className="text-center text-muted">
                    Sélectionnez un chauffeur pour voir les détails
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {selectedView === "vehicles" && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Véhicules ({vehicles.length})</h2>
            </div>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Plaque</th>
                    <th>Modèle</th>
                    <th>Statut</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {vehicles.map((vehicle) => (
                    <tr key={vehicle.id}>
                      <td>{vehicle.plate}</td>
                      <td>{vehicle.model || "—"}</td>
                      <td>
                        <span className={`badge ${vehicle.state === "active" ? "badge-success" : "badge-gray"}`}>
                          {vehicle.state || "N/A"}
                        </span>
                      </td>
                      <td>
                        <button className="btn btn-primary btn-sm">Voir détails</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

