import React from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type EarningsChartProps = {
  data: Array<{
    date: string;
    earnings: number;
    users?: number;
  }>;
  type?: "line" | "bar";
  showUsers?: boolean;
};

export function EarningsChart({ data, type = "line", showUsers = false }: EarningsChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="text-center text-muted" style={{ padding: "2rem" }}>
        Aucune donnée disponible
      </div>
    );
  }

  if (type === "bar") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="earnings" fill="#3b82f6" name="Revenus (EUR)" />
          {showUsers && <Bar dataKey="users" fill="#10b981" name="Utilisateurs" />}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis yAxisId="left" />
        {showUsers && <YAxis yAxisId="right" orientation="right" />}
        <Tooltip />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="earnings"
          stroke="#3b82f6"
          strokeWidth={2}
          name="Revenus nets (EUR)"
        />
        {showUsers && (
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="users"
            stroke="#10b981"
            strokeWidth={2}
            name="Utilisateurs connectés"
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}

