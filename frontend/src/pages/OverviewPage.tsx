import React, { useEffect, useState } from "react";
import {
  getBoltDrivers,
  getBoltVehicles,
  getBoltOrders,
  getBoltDriverEarnings,
} from "../api/fleetApi";
import { StatCard } from "../components/StatCard";

type OverviewPageProps = {
  token: string;
};

export function OverviewPage({ token }: OverviewPageProps) {
  const [stats, setStats] = useState({
    totalDrivers: 0,
    totalVehicles: 0,
    totalOrders: 0,
    totalEarnings: 0,
    activeDrivers: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const [drivers, vehicles, orders] = await Promise.all([
          getBoltDrivers(token, { limit: 200 }).catch(() => []),
          getBoltVehicles(token, { limit: 200 }).catch(() => []),
          getBoltOrders(token, new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10), new Date().toISOString().slice(0, 10)).catch(() => []),
        ]);

        // Calculer les revenus totaux depuis les orders
        const totalEarnings = orders.reduce((sum: number, order: any) => {
          return sum + (order.net_earnings || 0);
        }, 0);

        // Drivers actifs (avec au moins une commande cette semaine)
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        const activeDriverIds = new Set(
          orders
            .filter((o: any) => o.order_created_timestamp && new Date(o.order_created_timestamp * 1000) >= weekAgo)
            .map((o: any) => o.driver_uuid)
            .filter(Boolean)
        );

        setStats({
          totalDrivers: drivers.length || 0,
          totalVehicles: vehicles.length || 0,
          totalOrders: orders.length || 0,
          totalEarnings,
          activeDrivers: activeDriverIds.size,
        });
      } catch (err) {
        console.error("Erreur chargement stats:", err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, [token]);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.875rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.5rem" }}>
          Overview
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.875rem" }}>
          Vue d'ensemble de votre flotte et statistiques principales
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Chauffeurs totaux"
          value={stats.totalDrivers}
          icon="👥"
          color="primary"
        />
        <StatCard
          label="Véhicules"
          value={stats.totalVehicles}
          icon="🚗"
          color="info"
        />
        <StatCard
          label="Commandes (30j)"
          value={stats.totalOrders}
          icon="📦"
          color="success"
        />
        <StatCard
          label="Revenus totaux (30j)"
          value={`${stats.totalEarnings.toFixed(2)} EUR`}
          icon="💰"
          color="success"
        />
        <StatCard
          label="Chauffeurs actifs (7j)"
          value={stats.activeDrivers}
          icon="✅"
          color="success"
        />
      </div>

      {/* Quick Actions / Getting Started */}
      <div className="card" style={{ marginBottom: "2rem" }}>
        <div className="card-header">
          <h2 className="card-title">Démarrage rapide</h2>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-2 gap-4">
            <div style={{
              padding: "1.5rem",
              border: "2px solid #e2e8f0",
              borderRadius: "12px",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#3b82f6";
              e.currentTarget.style.boxShadow = "0 4px 6px rgba(59, 130, 246, 0.1)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "#e2e8f0";
              e.currentTarget.style.boxShadow = "none";
            }}>
              <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>👥</div>
              <h3 style={{ fontSize: "1.125rem", fontWeight: "600", marginBottom: "0.5rem" }}>
                Gérer les chauffeurs
              </h3>
              <p style={{ fontSize: "0.875rem", color: "#64748b" }}>
                Consultez la liste des chauffeurs et leurs statistiques détaillées
              </p>
            </div>
            <div style={{
              padding: "1.5rem",
              border: "2px solid #e2e8f0",
              borderRadius: "12px",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#3b82f6";
              e.currentTarget.style.boxShadow = "0 4px 6px rgba(59, 130, 246, 0.1)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "#e2e8f0";
              e.currentTarget.style.boxShadow = "none";
            }}>
              <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📊</div>
              <h3 style={{ fontSize: "1.125rem", fontWeight: "600", marginBottom: "0.5rem" }}>
                Voir les analytics
              </h3>
              <p style={{ fontSize: "0.875rem", color: "#64748b" }}>
                Analysez les performances et revenus de votre flotte
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

