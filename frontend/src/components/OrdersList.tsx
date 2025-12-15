import React from "react";

type Order = {
  order_reference: string;
  driver_name?: string;
  order_status?: string;
  order_created_timestamp?: number | null;
  order_finished_timestamp?: number | null;
  ride_price?: number | null;
  net_earnings?: number | null;
  commission?: number | null;
  tip?: number | null;
  ride_distance?: number | null;
  currency?: string | null;
  vehicle_license_plate?: string;
  payment_method?: string;
};

type OrdersListProps = {
  orders: Order[];
  loading?: boolean;
};

export function OrdersList({ orders, loading }: OrdersListProps) {
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span className="ml-2">Chargement des commandes...</span>
      </div>
    );
  }

  if (!orders.length) {
    return (
      <div className="card">
        <div className="text-center text-muted">Aucune commande disponible</div>
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

  const formatDate = (timestamp?: number | null) => {
    if (!timestamp) return "—";
    return new Date(timestamp * 1000).toLocaleString("fr-FR", {
      dateStyle: "short",
      timeStyle: "short",
    });
  };

  const getStatusBadge = (status?: string) => {
    if (!status) return <span className="badge badge-gray">Inconnu</span>;
    const statusLower = status.toLowerCase();
    if (statusLower.includes("finished") || statusLower.includes("completed")) {
      return <span className="badge badge-success">Terminée</span>;
    }
    if (statusLower.includes("cancel")) {
      return <span className="badge badge-error">Annulée</span>;
    }
    if (statusLower.includes("active") || statusLower.includes("ongoing")) {
      return <span className="badge badge-info">En cours</span>;
    }
    return <span className="badge badge-gray">{status}</span>;
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Commandes ({orders.length})</h2>
      </div>
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Référence</th>
              <th>Date</th>
              <th>Chauffeur</th>
              <th>Statut</th>
              <th>Véhicule</th>
              <th>Prix course</th>
              <th>Revenu net</th>
              <th>Commission</th>
              <th>Pourboire</th>
              <th>Distance</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.order_reference}>
                <td>
                  <code style={{ fontSize: "0.75rem" }}>
                    {order.order_reference.slice(0, 8)}...
                  </code>
                </td>
                <td>
                  <div>{formatDate(order.order_created_timestamp)}</div>
                  {order.order_finished_timestamp && (
                    <div className="text-muted" style={{ fontSize: "0.75rem" }}>
                      Fin: {formatDate(order.order_finished_timestamp)}
                    </div>
                  )}
                </td>
                <td>{order.driver_name || "—"}</td>
                <td>{getStatusBadge(order.order_status)}</td>
                <td>{order.vehicle_license_plate || "—"}</td>
                <td>
                  <strong>{safeToFixed(order.ride_price, 2)} {order.currency || "EUR"}</strong>
                </td>
                <td>
                  <span className="text-success">
                    <strong>+{safeToFixed(order.net_earnings, 2)} {order.currency || "EUR"}</strong>
                  </span>
                </td>
                <td>
                  <span className="text-error">
                    -{safeToFixed(order.commission, 2)} {order.currency || "EUR"}
                  </span>
                </td>
                <td>
                  {safeNumber(order.tip) > 0 ? (
                    <span className="text-success">+{safeToFixed(order.tip, 2)} {order.currency || "EUR"}</span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
                <td>{safeToFixed(order.ride_distance, 2)} km</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

