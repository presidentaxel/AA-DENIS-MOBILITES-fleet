import React, { useEffect, useState } from "react";
import { getBoltOrders } from "../api/fleetApi";
import { OrdersList } from "../components/OrdersList";
import { StatCard } from "../components/StatCard";

type OrdersPageProps = {
  token: string;
};

export function OrdersPage({ token }: OrdersPageProps) {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().slice(0, 10));
  const [driverFilter, setDriverFilter] = useState<string>("");

  useEffect(() => {
    async function fetchOrders() {
      setLoading(true);
      try {
        const data = await getBoltOrders(
          token,
          dateFrom,
          dateTo,
          driverFilter || undefined
        );
        setOrders(data);
      } catch (err: any) {
        console.error("Erreur chargement orders:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchOrders();
  }, [token, dateFrom, dateTo, driverFilter]);

  // Calculer les stats
  const stats = React.useMemo(() => {
    const total = orders.length;
    const completed = orders.filter((o: any) =>
      o.order_status && o.order_status.toLowerCase().includes("finished")
    ).length;
    const cancelled = orders.filter((o: any) =>
      o.order_status && o.order_status.toLowerCase().includes("cancel")
    ).length;
    const totalRevenue = orders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
    const totalNetEarnings = orders.reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
    const totalCommission = orders.reduce((sum: number, o: any) => sum + (o.commission || 0), 0);
    const totalDistance = orders.reduce((sum: number, o: any) => sum + (o.ride_distance || 0), 0);

    return {
      total,
      completed,
      cancelled,
      totalRevenue,
      totalNetEarnings,
      totalCommission,
      totalDistance,
      completionRate: total > 0 ? (completed / total * 100) : 0,
    };
  }, [orders]);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.5rem" }}>
            📦 Commandes
          </h1>
          <p style={{ color: "#64748b", fontSize: "0.875rem" }}>
            {stats.total} commande{stats.total > 1 ? "s" : ""} au total
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="form-group">
            <label className="form-label">Période : Du</label>
            <input
              type="date"
              className="form-input"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Au</label>
            <input
              type="date"
              className="form-input"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Filtrer par chauffeur (UUID)</label>
            <input
              type="text"
              className="form-input"
              placeholder="UUID du chauffeur (optionnel)"
              value={driverFilter}
              onChange={(e) => setDriverFilter(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Total commandes"
          value={stats.total}
          icon="📦"
          color="primary"
        />
        <StatCard
          label="Complétées"
          value={stats.completed}
          icon="✅"
          color="success"
        />
        <StatCard
          label="Annulées"
          value={stats.cancelled}
          icon="❌"
          color="error"
        />
        <StatCard
          label="Taux complétion"
          value={`${stats.completionRate.toFixed(1)}%`}
          icon="📊"
          color="info"
        />
        <StatCard
          label="Revenus bruts"
          value={`${stats.totalRevenue.toFixed(2)} EUR`}
          icon="💰"
          color="success"
        />
        <StatCard
          label="Revenus nets"
          value={`${stats.totalNetEarnings.toFixed(2)} EUR`}
          icon="💵"
          color="success"
        />
        <StatCard
          label="Commissions"
          value={`${stats.totalCommission.toFixed(2)} EUR`}
          icon="💳"
          color="warning"
        />
        <StatCard
          label="Distance totale"
          value={`${stats.totalDistance.toFixed(2)} km`}
          icon="🚗"
          color="info"
        />
      </div>

      {/* Orders List */}
      <OrdersList orders={orders} loading={loading} />
    </div>
  );
}

