import React from "react";

type Driver = {
  id?: string;
  uuid?: string;
  first_name?: string;
  last_name?: string;
  name?: string;
  email?: string;
  phone?: string;
  active?: boolean;
};

type DriverTableModernProps = {
  drivers: Driver[];
  selected?: string | null;
  onSelect?: (driverId: string) => void;
  loading?: boolean;
};

export function DriverTableModern({ drivers, selected, onSelect, loading }: DriverTableModernProps) {
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span className="ml-2">Chargement des chauffeurs...</span>
      </div>
    );
  }

  if (!drivers.length) {
    return (
      <div className="card">
        <div className="text-center text-muted">Aucun chauffeur disponible</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Chauffeurs ({drivers.length})</h2>
      </div>
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Téléphone</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {drivers.map((driver, idx) => {
              const driverId = driver.id || driver.uuid || `driver-${idx}`;
              const fullName = driver.first_name && driver.last_name
                ? `${driver.first_name} ${driver.last_name}`
                : driver.name || "N/A";
              const isSelected = selected === driverId;

              return (
                <tr
                  key={driverId}
                  style={{
                    backgroundColor: isSelected ? "rgba(37, 99, 235, 0.1)" : undefined,
                    cursor: "pointer",
                  }}
                  onClick={() => onSelect?.(driverId)}
                >
                  <td>
                    <div className="font-weight: 600">{fullName}</div>
                    {driver.first_name && driver.last_name && (
                      <div className="text-muted" style={{ fontSize: "0.75rem" }}>
                        {driver.first_name} {driver.last_name}
                      </div>
                    )}
                  </td>
                  <td>{driver.email || <span className="text-muted">—</span>}</td>
                  <td>{driver.phone || <span className="text-muted">—</span>}</td>
                  <td>
                    <span className={`badge ${driver.active !== false ? "badge-success" : "badge-gray"}`}>
                      {driver.active !== false ? "Actif" : "Inactif"}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelect?.(driverId);
                      }}
                    >
                      Voir détails
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

