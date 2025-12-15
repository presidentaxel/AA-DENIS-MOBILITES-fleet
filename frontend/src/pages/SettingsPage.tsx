import React from "react";

type SettingsPageProps = {
  token: string;
};

export function SettingsPage({ token }: SettingsPageProps) {
  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.875rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.5rem" }}>
          ⚙️ Paramètres
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.875rem" }}>
          Gestion des paramètres de l'application
        </p>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button className="tab active">Accès Dashboard</button>
        <button className="tab">Synchronisation</button>
        <button className="tab">API</button>
      </div>

      {/* Settings Content */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Accès Dashboard</h2>
        </div>
        <div className="card-body">
          <div className="text-center text-muted" style={{ padding: "2rem" }}>
            <p style={{ marginBottom: "1rem" }}>
              Gestion des accès dashboard non implémentée
            </p>
            <p style={{ fontSize: "0.875rem" }}>
              Cette fonctionnalité nécessiterait une gestion des utilisateurs et des permissions dans Supabase.
            </p>
          </div>
        </div>
      </div>

      {/* Synchronisation Settings */}
      <div className="card mt-4">
        <div className="card-header">
          <h2 className="card-title">Synchronisation automatique</h2>
        </div>
        <div className="card-body">
          <div style={{ marginBottom: "1rem" }}>
            <strong>Statut :</strong> Active
          </div>
          <div style={{ marginBottom: "1rem" }}>
            <strong>Fréquence :</strong> Quotidienne (2h du matin)
          </div>
          <div style={{ marginBottom: "1rem" }}>
            <strong>Synchronisé :</strong> Organizations, Drivers, Vehicles, Orders, State Logs
          </div>
          <p style={{ fontSize: "0.875rem", color: "#64748b" }}>
            La synchronisation est gérée automatiquement par le scheduler quotidien.
            Les données lourdes (orders, state_logs) sont synchronisées par lots pour ne pas bloquer le serveur.
          </p>
        </div>
      </div>
    </div>
  );
}

