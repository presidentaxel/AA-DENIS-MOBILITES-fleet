import React from "react";
import { StatCard } from "./StatCard";

type DriverEarnings = {
  driver_uuid: string;
  driver_name?: string;
  total_orders?: number | null;
  completed_orders?: number | null;
  cancelled_orders?: number | null;
  total_net_earnings?: number | null;
  total_ride_price?: number | null;
  total_commission?: number | null;
  total_tip?: number | null;
  total_distance?: number | null;
  average_order_value?: number | null;
  average_net_earnings_per_order?: number | null;
  currency?: string | null;
};

type DriverStatsProps = {
  earnings: DriverEarnings;
  loading?: boolean;
};

export function DriverStats({ earnings, loading }: DriverStatsProps) {
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span className="ml-2">Chargement des statistiques...</span>
      </div>
    );
  }

  // Fonction helper pour formater les nombres en toute sécurité
  const safeToFixed = (value: number | null | undefined, decimals: number = 2): string => {
    if (value === null || value === undefined || isNaN(value)) return "0";
    return value.toFixed(decimals);
  };

  const safeNumber = (value: number | null | undefined): number => {
    return value === null || value === undefined || isNaN(value) ? 0 : value;
  };

  const totalOrders = safeNumber(earnings.total_orders);
  const completedOrders = safeNumber(earnings.completed_orders);
  const cancelledOrders = safeNumber(earnings.cancelled_orders);
  const totalNetEarnings = safeNumber(earnings.total_net_earnings);
  const totalRidePrice = safeNumber(earnings.total_ride_price);
  const totalCommission = safeNumber(earnings.total_commission);
  const totalTip = safeNumber(earnings.total_tip);
  const totalDistance = safeNumber(earnings.total_distance);
  const avgOrderValue = safeNumber(earnings.average_order_value);
  const avgNetEarningsPerOrder = safeNumber(earnings.average_net_earnings_per_order);

  const completionRate = totalOrders > 0
    ? ((completedOrders / totalOrders) * 100).toFixed(1)
    : "0";

  const cancellationRate = totalOrders > 0
    ? ((cancelledOrders / totalOrders) * 100).toFixed(1)
    : "0";

  const earningsPerKm = totalDistance > 0
    ? (totalNetEarnings / totalDistance).toFixed(2)
    : "0";

  const currency = earnings.currency || "EUR";

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <StatCard
        label="Commandes totales"
        value={totalOrders}
        icon="📦"
        color="primary"
      />
      <StatCard
        label="Revenus nets"
        value={`${safeToFixed(totalNetEarnings, 2)} ${currency}`}
        icon="💰"
        color="success"
      />
      <StatCard
        label="Taux de complétion"
        value={`${completionRate}%`}
        icon="✅"
        color="success"
      />
      <StatCard
        label="Revenu moyen/commande"
        value={`${safeToFixed(avgNetEarningsPerOrder, 2)} ${currency}`}
        icon="📊"
        color="info"
      />
      <StatCard
        label="Commandes complétées"
        value={completedOrders}
        icon="✓"
        color="success"
      />
      <StatCard
        label="Commandes annulées"
        value={cancelledOrders}
        icon="✗"
        color="error"
      />
      <StatCard
        label="Commission totale"
        value={`${safeToFixed(totalCommission, 2)} ${currency}`}
        icon="💳"
        color="warning"
      />
      <StatCard
        label="Pourboires"
        value={`${safeToFixed(totalTip, 2)} ${currency}`}
        icon="🎁"
        color="success"
      />
      <StatCard
        label="Distance totale"
        value={`${safeToFixed(totalDistance, 2)} km`}
        icon="🚗"
        color="info"
      />
      <StatCard
        label="Revenu/km"
        value={`${earningsPerKm} ${currency}/km`}
        icon="📈"
        color="success"
      />
      <StatCard
        label="Taux d'annulation"
        value={`${cancellationRate}%`}
        icon="⚠️"
        color={parseFloat(cancellationRate) > 20 ? "error" : "warning"}
      />
      <StatCard
        label="Valeur moyenne commande"
        value={`${safeToFixed(avgOrderValue, 2)} ${currency}`}
        icon="💵"
        color="primary"
      />
    </div>
  );
}

