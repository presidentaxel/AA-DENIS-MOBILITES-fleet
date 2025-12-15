import React, { useEffect, useState, useMemo } from "react";
import { getBoltDrivers, getBoltOrders } from "../api/fleetApi";
import { StatCard } from "../components/StatCard";
import { DistributionChart } from "../components/charts/DistributionChart";

type AnalyticsPageProps = {
  token: string;
};

export function AnalyticsPage({ token }: AnalyticsPageProps) {
  const [stats, setStats] = useState({
    connectedUsers: 0,
    workingUsers: 0,
    totalGrossEarnings: 0,
    totalNetEarnings: 0,
  });
  const [topDrivers, setTopDrivers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<"week" | "month">("week");

  useEffect(() => {
    async function loadAnalytics() {
      setLoading(true);
      try {
        const drivers = await getBoltDrivers(token, { limit: 200 }).catch(() => []);
        
        // Calculer la période
        const endDate = new Date();
        const startDate = new Date();
        if (period === "week") {
          startDate.setDate(endDate.getDate() - 7);
        } else {
          startDate.setDate(endDate.getDate() - 30);
        }

        const dateFrom = startDate.toISOString().slice(0, 10);
        const dateTo = endDate.toISOString().slice(0, 10);

        // Récupérer les orders
        const orders = await getBoltOrders(token, dateFrom, dateTo).catch(() => []);

        // Calculer les stats globales
        const workingDriverIds = new Set(orders.map((o: any) => o.driver_uuid).filter(Boolean));
        const totalGrossEarnings = orders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
        const totalNetEarnings = orders.reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);

        // Top drivers par revenus
        const driverEarningsMap = new Map<string, number>();
        orders.forEach((order: any) => {
          if (order.driver_uuid) {
            const current = driverEarningsMap.get(order.driver_uuid) || 0;
            driverEarningsMap.set(order.driver_uuid, current + (order.net_earnings || 0));
          }
        });

        const topDriversList = Array.from(driverEarningsMap.entries())
          .map(([driverId, earnings]) => {
            const driver = drivers.find((d: any) => d.id === driverId);
            return {
              id: driverId,
              name: driver ? `${driver.first_name} ${driver.last_name}` : "Unknown",
              earnings,
            };
          })
          .sort((a, b) => b.earnings - a.earnings)
          .slice(0, 10);

        setStats({
          connectedUsers: drivers.length,
          workingUsers: workingDriverIds.size,
          totalGrossEarnings: totalGrossEarnings,
          totalNetEarnings: totalNetEarnings,
        });
        setTopDrivers(topDriversList);
      } catch (err) {
        console.error("Erreur chargement analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [token, period]);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.5rem" }}>
            📈 Analytics
          </h1>
          <p style={{ color: "#64748b", fontSize: "0.875rem" }}>
            Insights et statistiques de votre flotte
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className={`btn ${period === "week" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setPeriod("week")}
          >
            Cette semaine
          </button>
          <button
            className={`btn ${period === "month" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setPeriod("month")}
          >
            Ce mois
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          label="Utilisateurs connectés"
          value={stats.connectedUsers}
          icon="👥"
          color="primary"
        />
        <StatCard
          label="Chauffeurs actifs"
          value={stats.workingUsers}
          icon="✅"
          color="success"
        />
        <StatCard
          label="Revenus bruts totaux"
          value={`${stats.totalGrossEarnings.toFixed(2)} EUR`}
          icon="💰"
          color="success"
        />
        <StatCard
          label="Revenus nets totaux"
          value={`${stats.totalNetEarnings.toFixed(2)} EUR`}
          icon="💵"
          color="success"
        />
      </div>

      {/* Top Drivers */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">🏆 Top chauffeurs ({period === "week" ? "Cette semaine" : "Ce mois"})</h2>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
            </div>
          ) : topDrivers.length > 0 ? (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Rang</th>
                    <th>Nom</th>
                    <th>Revenus nets</th>
                  </tr>
                </thead>
                <tbody>
                  {topDrivers.map((driver, index) => (
                    <tr key={driver.id}>
                      <td>
                        <span style={{
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          width: "32px",
                          height: "32px",
                          borderRadius: "50%",
                          backgroundColor: index === 0 ? "#fbbf24" : index === 1 ? "#9ca3af" : index === 2 ? "#cd7f32" : "#e2e8f0",
                          color: index < 3 ? "#fff" : "#64748b",
                          fontWeight: "600",
                        }}>
                          {index + 1}
                        </span>
                      </td>
                      <td>
                        <strong>{driver.name}</strong>
                      </td>
                      <td>
                        <strong style={{ color: "#10b981" }}>
                          {driver.earnings.toFixed(2)} EUR
                        </strong>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-muted">Aucune donnée disponible</div>
          )}
        </div>
      </div>

      {/* Distribution des revenus */}
      {(() => {
        // Calculer la distribution des revenus par tranche
        const distributionData = useMemo(() => {
          const ranges = [
            { min: 0, max: 100, label: "0-100€" },
            { min: 100, max: 300, label: "100-300€" },
            { min: 300, max: 500, label: "300-500€" },
            { min: 500, max: 700, label: "500-700€" },
            { min: 700, max: 900, label: "700-900€" },
            { min: 900, max: 1100, label: "900-1100€" },
            { min: 1100, max: 1300, label: "1100-1300€" },
            { min: 1300, max: 1500, label: "1300-1500€" },
            { min: 1500, max: Infinity, label: "1500€+" },
          ];

          return ranges.map((range) => ({
            range: range.label,
            count: topDrivers.filter((d) => {
              const earnings = d.earnings || 0;
              return earnings >= range.min && earnings < range.max;
            }).length,
          }));
        }, [topDrivers]);

        return (
          <div className="card mt-4">
            <div className="card-header">
              <h2 className="card-title">
                Distribution des revenus ({period === "week" ? "Cette semaine" : "Ce mois"})
              </h2>
            </div>
            <div className="card-body">
              <DistributionChart data={distributionData} />
            </div>
          </div>
        );
      })()}
    </div>
  );
}

