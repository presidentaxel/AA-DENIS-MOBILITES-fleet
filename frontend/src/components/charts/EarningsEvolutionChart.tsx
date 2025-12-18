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
  // Filtrer les données pour ne garder que celles avec des earnings > 0
  // L'échelle X doit être basée uniquement sur les données d'earnings
  const filteredData = data.filter((d) => d.earnings > 0);
  
  // Si aucune donnée filtrée, utiliser toutes les données
  const dataToUse = filteredData.length > 0 ? filteredData : data;
  
  const chartData = dataToUse.map((d) => ({
    date: d.date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" }),
    earnings: d.earnings,
    connected: d.connected,
  }));

  const maxEarnings = Math.max(...dataToUse.map((d) => d.earnings), 1);
  const maxConnected = Math.max(...dataToUse.map((d) => d.connected), 1);

  // Calculer les domaines adaptatifs
  // Pour les earnings : utiliser maxEarnings * 1.1 avec un minimum de 100 pour éviter les échelles trop petites
  const earningsDomain = maxEarnings > 0 ? [0, Math.max(maxEarnings * 1.1, 100)] : [0, 100];
  
  // Pour les connected users : utiliser maxConnected + 10% avec un minimum de 10
  const connectedDomain = maxConnected > 0 ? [0, Math.max(maxConnected * 1.1, 10)] : [0, 10];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData} margin={{ top: 50, right: 50, left: 80, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12, fill: "#64748b" }}
          label={{ value: "Time of earnings", position: "insideBottom", offset: -5, style: { fill: "#64748b" } }}
          domain={['dataMin', 'dataMax']}
        />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 12, fill: "#64748b" }}
          label={{ value: "Number of connected users", angle: -90, position: "insideLeft", style: { fill: "#3b82f6" } }}
          domain={connectedDomain}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 12, fill: "#64748b" }}
          label={{ value: "Total weekly earnings in €", angle: 90, position: "insideRight", style: { fill: "#f97316" } }}
          domain={earningsDomain}
          tickFormatter={(value) => {
            // Formatter adaptatif : utiliser k pour les milliers, sinon afficher la valeur normale
            if (value >= 1000) {
              return `${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`;
            }
            return value.toFixed(0);
          }}
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

