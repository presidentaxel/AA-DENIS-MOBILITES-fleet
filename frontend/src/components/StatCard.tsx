import React from "react";

type StatCardProps = {
  label: string;
  value: string | number;
  change?: {
    value: number;
    type: "positive" | "negative" | "neutral";
  };
  icon?: React.ReactNode;
  color?: "primary" | "success" | "warning" | "error" | "info";
};

export function StatCard({ label, value, change, icon, color = "primary" }: StatCardProps) {
  const borderColors = {
    primary: "#3b82f6",
    success: "#10b981",
    warning: "#f59e0b",
    error: "#ef4444",
    info: "#06b6d4",
  };

  return (
    <div className="stat-card" style={{ borderLeft: `4px solid ${borderColors[color]}` }}>
      <div className="flex items-center justify-between" style={{ marginBottom: "0.5rem" }}>
        <span className="stat-label">{label}</span>
        {icon && <span style={{ fontSize: "1.5rem" }}>{icon}</span>}
      </div>
      <div className="stat-value">{typeof value === "number" ? value.toLocaleString() : value}</div>
      {change && (
        <div className={`stat-change ${change.type}`}>
          <span>{change.type === "positive" ? "↑" : change.type === "negative" ? "↓" : "→"}</span>
          <span>{Math.abs(change.value).toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
}

