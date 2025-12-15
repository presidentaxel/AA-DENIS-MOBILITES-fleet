import React, { useEffect, useState } from "react";
import { getBoltVehicles, getBoltOrders } from "../api/fleetApi";

type VehiclesPageProps = {
  token: string;
};

export function VehiclesPage({ token }: VehiclesPageProps) {
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState<string | null>(null);
  const [vehicleStats, setVehicleStats] = useState<any>(null);

  useEffect(() => {
    async function fetchVehicles() {
      setLoading(true);
      try {
        const data = await getBoltVehicles(token, { limit: 200 });
        setVehicles(data);
        if (data.length) {
          setSelectedVehicle(data[0].id);
        }
      } catch (err: any) {
        console.error("Erreur chargement véhicules:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchVehicles();
  }, [token]);

  useEffect(() => {
    async function fetchVehicleStats() {
      if (!selectedVehicle) return;
      setLoading(true);
      try {
        // Récupérer les orders pour ce véhicule
        const vehicle = vehicles.find(v => v.id === selectedVehicle);
        if (!vehicle?.plate) return;

        const endDate = new Date();
        const startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000);
        const orders = await getBoltOrders(
          token,
          startDate.toISOString().slice(0, 10),
          endDate.toISOString().slice(0, 10)
        ).catch(() => []);

        const vehicleOrders = orders.filter((o: any) => o.vehicle_license_plate === vehicle.plate);
        
        const totalOrders = vehicleOrders.length;
        const totalDistance = vehicleOrders.reduce((sum: number, o: any) => sum + (o.ride_distance || 0), 0);
        const totalEarnings = vehicleOrders.reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
        const completedOrders = vehicleOrders.filter((o: any) => 
          o.order_status && o.order_status.toLowerCase().includes("finished")
        ).length;

        setVehicleStats({
          totalOrders,
          totalDistance,
          totalEarnings,
          completedOrders,
          cancellationRate: totalOrders > 0 ? ((totalOrders - completedOrders) / totalOrders * 100) : 0,
        });
      } catch (err: any) {
        console.error("Erreur chargement stats véhicule:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchVehicleStats();
  }, [token, selectedVehicle, vehicles]);

  const selectedVehicleObj = vehicles.find((v) => v.id === selectedVehicle);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.875rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.5rem" }}>
          🚗 Véhicules
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.875rem" }}>
          {vehicles.length} véhicule{vehicles.length > 1 ? "s" : ""} au total
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Liste des véhicules */}
        <div className="lg:col-span-1">
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
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {vehicles.map((vehicle) => (
                    <tr
                      key={vehicle.id}
                      style={{
                        backgroundColor: selectedVehicle === vehicle.id ? "rgba(59, 130, 246, 0.1)" : undefined,
                        cursor: "pointer",
                      }}
                      onClick={() => setSelectedVehicle(vehicle.id)}
                    >
                      <td>
                        <strong>{vehicle.plate}</strong>
                      </td>
                      <td>{vehicle.model || "—"}</td>
                      <td>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedVehicle(vehicle.id);
                          }}
                        >
                          Voir
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Détails du véhicule */}
        <div className="lg:col-span-2">
          {selectedVehicleObj ? (
            <>
              <div className="card mb-4">
                <div className="card-header">
                  <h2 className="card-title">Véhicule {selectedVehicleObj.plate}</h2>
                </div>
                <div className="card-body">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <strong>Plaque:</strong> {selectedVehicleObj.plate}
                    </div>
                    <div>
                      <strong>Modèle:</strong> {selectedVehicleObj.model || "—"}
                    </div>
                    <div>
                      <strong>ID:</strong> {selectedVehicleObj.id}
                    </div>
                    <div>
                      <strong>Provider Vehicle ID:</strong> {selectedVehicleObj.provider_vehicle_id || "—"}
                    </div>
                  </div>
                </div>
              </div>

              {vehicleStats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="stat-card">
                    <div className="stat-label">Commandes (30j)</div>
                    <div className="stat-value">{vehicleStats.totalOrders}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Distance totale</div>
                    <div className="stat-value">{vehicleStats.totalDistance.toFixed(2)} km</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Revenus totaux</div>
                    <div className="stat-value">{vehicleStats.totalEarnings.toFixed(2)} EUR</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Taux d'annulation</div>
                    <div className="stat-value">{vehicleStats.cancellationRate.toFixed(1)}%</div>
                  </div>
                </div>
              )}

              {loading && (
                <div className="loading">
                  <div className="spinner"></div>
                </div>
              )}
            </>
          ) : (
            <div className="card">
              <div className="text-center text-muted">
                Sélectionnez un véhicule pour voir les détails
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

