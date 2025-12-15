import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getBoltDrivers, getBoltDriverEarnings, getBoltOrders } from "../api/fleetApi";
import { DriverTableModern } from "../components/DriverTableModern";
import { DriverStats } from "../components/DriverStats";
import { OrdersList } from "../components/OrdersList";

type DriversPageProps = {
  token: string;
};

export function DriversPage({ token }: DriversPageProps) {
  const navigate = useNavigate();
  const [drivers, setDrivers] = useState<any[]>([]);
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null);
  const [driverEarnings, setDriverEarnings] = useState<any>(null);
  const [driverOrders, setDriverOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().slice(0, 10));

  useEffect(() => {
    async function fetchDrivers() {
      setLoading(true);
      try {
        const data = await getBoltDrivers(token, { limit: 200 });
        setDrivers(data);
        if (data.length && !selectedDriver) {
          setSelectedDriver(data[0].id);
        }
      } catch (err: any) {
        console.error("Erreur chargement drivers:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchDrivers();
  }, [token]);

  useEffect(() => {
    async function fetchDriverDetails() {
      if (!selectedDriver) return;
      setLoading(true);
      try {
        const [earningsData, ordersData] = await Promise.all([
          getBoltDriverEarnings(token, selectedDriver, dateFrom, dateTo).catch(() => null),
          getBoltOrders(token, dateFrom, dateTo, selectedDriver).catch(() => []),
        ]);
        setDriverEarnings(earningsData);
        setDriverOrders(ordersData);
      } catch (err: any) {
        console.error("Erreur chargement détails:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchDriverDetails();
  }, [token, selectedDriver, dateFrom, dateTo]);

  const selectedDriverObj = drivers.find((d) => d.id === selectedDriver);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.5rem" }}>
            👥 Chauffeurs
          </h1>
          <p style={{ color: "#64748b", fontSize: "0.875rem" }}>
            {drivers.length} chauffeur{drivers.length > 1 ? "s" : ""} au total
          </p>
        </div>
      </div>

      {/* Date Range */}
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

      {/* Content */}
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

        {/* Détails du chauffeur */}
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

              <DriverStats earnings={driverEarnings} loading={loading} />
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
    </div>
  );
}

