import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  YAxisProps,
} from "recharts";

type EvolutionData = {
  date: Date;
  earnings: number;
  connected: number;
};

type EarningsEvolutionChartProps = {
  data: EvolutionData[];
};

export function EarningsEvolutionChart({ data }: EarningsEvolutionChartProps) {
  const chartData = data.map((d) => ({
    date: d.date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" }),
    earnings: d.earnings,
    connected: d.connected,
  }));

  const maxEarnings = Math.max(...data.map((d) => d.earnings), 1);
  const maxConnected = Math.max(...data.map((d) => d.connected), 1);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12, fill: "#64748b" }}
          label={{ value: "Time of earnings", position: "insideBottom", offset: -5, style: { fill: "#64748b" } }}
        />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 12, fill: "#64748b" }}
          label={{ value: "Number of connected users", angle: -90, position: "insideLeft", style: { fill: "#3b82f6" } }}
          domain={[0, Math.max(maxConnected + 10, 120)]}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 12, fill: "#64748b" }}
          label={{ value: "Total weekly earnings in €", angle: 90, position: "insideRight", style: { fill: "#f97316" } }}
          domain={[0, Math.max(maxEarnings * 1.1, 60000)]}
          tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "white",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            padding: "8px 12px",
          }}
          formatter={(value: number, name: string) => {
            if (name === "earnings") {
              return [`${value.toFixed(2)} €`, "Total net income"];
            }
            return [value, "Number of connected driver"];
          }}
        />
        <Legend
          wrapperStyle={{ paddingTop: "20px" }}
          iconType="circle"
          formatter={(value) => {
            if (value === "connected") return "Number of connected driver";
            if (value === "earnings") return "Total net income";
            return value;
          }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="connected"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          name="connected"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="earnings"
          stroke="#f97316"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="earnings"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

