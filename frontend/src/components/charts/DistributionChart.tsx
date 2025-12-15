import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type DistributionChartProps = {
  data: Array<{
    range: string;
    count: number;
  }>;
  title?: string;
};

export function DistributionChart({ data, title }: DistributionChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="text-center text-muted" style={{ padding: "2rem" }}>
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <div>
      {title && (
        <h3 style={{ fontSize: "1rem", fontWeight: "600", marginBottom: "1rem" }}>
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" label={{ value: "Nombre d'utilisateurs", position: "insideBottom", offset: -5 }} />
          <YAxis dataKey="range" type="category" width={100} />
          <Tooltip />
          <Bar dataKey="count" fill="#3b82f6" name="Nombre d'utilisateurs" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

