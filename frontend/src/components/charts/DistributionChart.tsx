import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

type DistributionChartProps = {
  data: { range: string; count: number }[];
};

export function DistributionChart({ data }: DistributionChartProps) {
  // Format des ranges: "0-200" -> "0 - 200" pour l'affichage
  const chartData = data.map((item) => ({
    range: item.range.includes("-") ? item.range.replace("-", " - ") : item.range,
    count: item.count,
  }));

  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="range"
          tick={{ fontSize: 12, fill: "#64748b" }}
          label={{ value: "Earnings in €", position: "insideBottom", offset: -5, style: { fill: "#64748b" } }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: "#64748b" }}
          label={{ value: "Number of users", angle: -90, position: "insideLeft", style: { fill: "#64748b" } }}
          domain={[0, Math.max(maxCount + 2, 4)]}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "white",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            padding: "8px 12px",
          }}
          labelFormatter={(label) => `${label} €`}
          formatter={(value: number) => [value, "Weekly income distribution"]}
        />
        <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
