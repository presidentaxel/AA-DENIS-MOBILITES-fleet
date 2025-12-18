import React, { useEffect, useState, useMemo } from "react";
import { FiBarChart2, FiUsers, FiCheckCircle, FiDollarSign, FiTrendingUp, FiCalendar } from "react-icons/fi";
import { StatCard } from "../components/StatCard";
import { DistributionChart } from "../components/charts/DistributionChart";
import { EarningsEvolutionChart } from "../components/charts/EarningsEvolutionChart";
import { TopUsersTable } from "../components/analytics/TopUsersTable";
import { NoEarningUsersTable } from "../components/analytics/NoEarningUsersTable";
import { getBoltDrivers, getBoltOrders } from "../api/fleetApi";

type AnalyticsPageProps = {
  token: string;
};

export function AnalyticsPage({ token }: AnalyticsPageProps) {
  const [drivers, setDrivers] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<"week" | "month">("week");
  const [showSampleData, setShowSampleData] = useState(false);

  // Dates pour cette semaine et la semaine dernière
  const thisWeekStart = useMemo(() => {
    const d = new Date();
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Lundi
    return new Date(d.setDate(diff));
  }, []);

  const thisWeekEnd = useMemo(() => {
    const d = new Date(thisWeekStart);
    d.setDate(d.getDate() + 6); // Dimanche
    return d;
  }, [thisWeekStart]);

  const lastWeekStart = useMemo(() => {
    const d = new Date(thisWeekStart);
    d.setDate(d.getDate() - 7);
    return d;
  }, [thisWeekStart]);

  const lastWeekEnd = useMemo(() => {
    const d = new Date(thisWeekStart);
    d.setDate(d.getDate() - 1); // Dimanche de la semaine dernière
    return d;
  }, [thisWeekStart]);

  useEffect(() => {
    async function loadAnalytics() {
      setLoading(true);
      try {
        // Charger les données pour les 90 derniers jours pour le graphique d'évolution
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - 90);
        
        const [driversData, ordersData] = await Promise.all([
          getBoltDrivers(token, { limit: 200 }).catch(() => []),
          getBoltOrders(
            token,
            startDate.toISOString().slice(0, 10),
            endDate.toISOString().slice(0, 10)
          ).catch(() => []),
        ]);
        setDrivers(driversData);
        setOrders(ordersData);
      } catch (err) {
        console.error("Erreur chargement analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [token]);

  // Calculer les métriques de cette semaine
  const thisWeekMetrics = useMemo(() => {
    const thisWeekOrders = orders.filter((o: any) => {
      // Use order_finished_timestamp for earnings calculations
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (!orderTs) return false;
      const orderDate = new Date(orderTs * 1000);
      return orderDate >= thisWeekStart && orderDate <= thisWeekEnd;
    });

    const workingDriverIds = new Set(
      thisWeekOrders.map((o: any) => o.driver_uuid).filter(Boolean)
    );

    const totalGrossEarnings = thisWeekOrders.reduce(
      (sum: number, o: any) => sum + (o.ride_price || 0),
      0
    );

    return {
      connectedUsers: drivers.length,
      workingUsers: workingDriverIds.size,
      totalGrossEarnings,
    };
  }, [orders, drivers, thisWeekStart, thisWeekEnd]);

  // Distribution des revenus cette semaine
  const thisWeekDistribution = useMemo(() => {
    const thisWeekOrders = orders.filter((o: any) => {
      // Use order_finished_timestamp for earnings calculations
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (!orderTs) return false;
      const orderDate = new Date(orderTs * 1000);
      return orderDate >= thisWeekStart && orderDate <= thisWeekEnd;
    });

    // Grouper par driver et calculer les revenus
    const driverEarnings = new Map<string, number>();
    thisWeekOrders.forEach((o: any) => {
      if (o.driver_uuid) {
        const current = driverEarnings.get(o.driver_uuid) || 0;
        driverEarnings.set(o.driver_uuid, current + (o.net_earnings || 0));
      }
    });

    // Créer des buckets de revenus (0-200, 200-400, etc.)
    const buckets: Record<string, number> = {
      "0-200": 0,
      "200-400": 0,
      "400-600": 0,
      "600-800": 0,
      "800-1000": 0,
      "1000-1200": 0,
      "1200-1400": 0,
      "1400-1600": 0,
    };

    driverEarnings.forEach((earnings) => {
      if (earnings <= 200) buckets["0-200"]++;
      else if (earnings <= 400) buckets["200-400"]++;
      else if (earnings <= 600) buckets["400-600"]++;
      else if (earnings <= 800) buckets["600-800"]++;
      else if (earnings <= 1000) buckets["800-1000"]++;
      else if (earnings <= 1200) buckets["1000-1200"]++;
      else if (earnings <= 1400) buckets["1200-1400"]++;
      else buckets["1400-1600"]++;
    });

    return Object.entries(buckets).map(([range, count]) => ({
      range,
      count,
    }));
  }, [orders, thisWeekStart, thisWeekEnd]);

  // Distribution des revenus la semaine dernière
  const lastWeekDistribution = useMemo(() => {
    const lastWeekOrders = orders.filter((o: any) => {
      // Use order_finished_timestamp for earnings calculations
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (!orderTs) return false;
      const orderDate = new Date(orderTs * 1000);
      return orderDate >= lastWeekStart && orderDate <= lastWeekEnd;
    });

    const driverEarnings = new Map<string, number>();
    lastWeekOrders.forEach((o: any) => {
      if (o.driver_uuid) {
        const current = driverEarnings.get(o.driver_uuid) || 0;
        driverEarnings.set(o.driver_uuid, current + (o.net_earnings || 0));
      }
    });

    const buckets: Record<string, number> = {
      "0-200": 0,
      "200-400": 0,
      "400-600": 0,
      "600-800": 0,
      "800-1000": 0,
      "1000-1200": 0,
      "1200-1400": 0,
      "1400-1600": 0,
    };

    driverEarnings.forEach((earnings) => {
      if (earnings <= 200) buckets["0-200"]++;
      else if (earnings <= 400) buckets["200-400"]++;
      else if (earnings <= 600) buckets["400-600"]++;
      else if (earnings <= 800) buckets["600-800"]++;
      else if (earnings <= 1000) buckets["800-1000"]++;
      else if (earnings <= 1200) buckets["1000-1200"]++;
      else if (earnings <= 1400) buckets["1200-1400"]++;
      else buckets["1400-1600"]++;
    });

    return Object.entries(buckets).map(([range, count]) => ({
      range,
      count,
    }));
  }, [orders, lastWeekStart, lastWeekEnd]);

  // Pourcentage d'utilisateurs sans revenus cette semaine
  const noEarningsThisWeekPercent = useMemo(() => {
    const thisWeekOrders = orders.filter((o: any) => {
      // Use order_finished_timestamp for earnings calculations
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (!orderTs) return false;
      const orderDate = new Date(orderTs * 1000);
      return orderDate >= thisWeekStart && orderDate <= thisWeekEnd;
    });

    const workingDriverIds = new Set(
      thisWeekOrders.map((o: any) => o.driver_uuid).filter(Boolean)
    );

    const totalDrivers = drivers.length;
    const driversWithEarnings = workingDriverIds.size;
    const driversWithoutEarnings = totalDrivers - driversWithEarnings;

    return totalDrivers > 0 ? (driversWithoutEarnings / totalDrivers) * 100 : 0;
  }, [orders, drivers, thisWeekStart, thisWeekEnd]);

  // Pourcentage d'utilisateurs sans revenus la semaine dernière
  const noEarningsLastWeekPercent = useMemo(() => {
    const lastWeekOrders = orders.filter((o: any) => {
      // Use order_finished_timestamp for earnings calculations
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (!orderTs) return false;
      const orderDate = new Date(orderTs * 1000);
      return orderDate >= lastWeekStart && orderDate <= lastWeekEnd;
    });

    const workingDriverIds = new Set(
      lastWeekOrders.map((o: any) => o.driver_uuid).filter(Boolean)
    );

    const totalDrivers = drivers.length;
    const driversWithEarnings = workingDriverIds.size;
    const driversWithoutEarnings = totalDrivers - driversWithEarnings;

    return totalDrivers > 0 ? (driversWithoutEarnings / totalDrivers) * 100 : 0;
  }, [orders, drivers, lastWeekStart, lastWeekEnd]);

  // Top users et No earning users
  const { topUsers, noEarningUsers } = useMemo(() => {
    const thisWeekOrders = orders.filter((o: any) => {
      // Use order_finished_timestamp for earnings calculations
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (!orderTs) return false;
      const orderDate = new Date(orderTs * 1000);
      return orderDate >= thisWeekStart && orderDate <= thisWeekEnd;
    });

    // Calculer les revenus par driver
    const driverEarnings = new Map<string, { earnings: number; driver: any }>();
    thisWeekOrders.forEach((o: any) => {
      if (o.driver_uuid) {
        const driver = drivers.find((d: any) => d.id === o.driver_uuid);
        if (driver) {
          const current = driverEarnings.get(o.driver_uuid) || {
            earnings: 0,
            driver,
          };
          current.earnings += o.net_earnings || 0;
          driverEarnings.set(o.driver_uuid, current);
        }
      }
    });

    // Trier et obtenir les top users
    const sortedUsers = Array.from(driverEarnings.values())
      .sort((a, b) => b.earnings - a.earnings)
      .map((item, index) => ({
        no: index + 1,
        driver: item.driver,
        earnings: item.earnings,
      }));

    // Trouver les users sans revenus
    const workingDriverIds = new Set(driverEarnings.keys());
    const noEarning = drivers
      .filter((d: any) => !workingDriverIds.has(d.id))
      .slice(0, 10)
      .map((driver: any, index: number) => ({
        no: index + 1,
        driver,
        earnings: 0,
      }));

    return {
      topUsers: sortedUsers.slice(0, 10),
      noEarningUsers: noEarning,
    };
  }, [orders, drivers, thisWeekStart, thisWeekEnd]);

  // Données pour le graphique d'évolution temporelle
  const evolutionData = useMemo(() => {
    // Trouver la première et dernière date avec des earnings pour adapter l'échelle X
    const earningsDates: number[] = [];
    orders.forEach((o: any) => {
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (orderTs && (o.net_earnings || 0) > 0) {
        earningsDates.push(orderTs);
      }
    });

    if (earningsDates.length === 0) {
      // Pas de données d'earnings, retourner un tableau vide
      return [];
    }

    const minDate = Math.min(...earningsDates);
    const maxDate = Math.max(...earningsDates);
    const startDate = new Date(minDate * 1000);
    const endDate = new Date(maxDate * 1000);

    // Créer un map pour tous les jours entre la première et dernière date avec earnings
    const dailyData = new Map<string, { date: Date; earnings: number; connected: number }>();
    
    const currentDate = new Date(startDate);
    currentDate.setHours(0, 0, 0, 0);
    const end = new Date(endDate);
    end.setHours(23, 59, 59, 999);

    while (currentDate <= end) {
      const dateKey = currentDate.toISOString().slice(0, 10);
      dailyData.set(dateKey, {
        date: new Date(currentDate),
        earnings: 0,
        connected: 0,
      });
      currentDate.setDate(currentDate.getDate() + 1);
    }

    // Remplir avec les données d'earnings réelles
    orders.forEach((o: any) => {
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (orderTs && (o.net_earnings || 0) > 0) {
        const orderDate = new Date(orderTs * 1000);
        const dateKey = orderDate.toISOString().slice(0, 10);

        if (dailyData.has(dateKey)) {
          const dayData = dailyData.get(dateKey)!;
          dayData.earnings += o.net_earnings || 0;
        }
      }
    });

    // Calculer les connected drivers par jour en fonction de leur première commande
    // Trouver la première commande de chaque driver
    const driverFirstOrder = new Map<string, number>();
    orders.forEach((o: any) => {
      if (o.driver_uuid) {
        const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
        if (orderTs) {
          const existing = driverFirstOrder.get(o.driver_uuid);
          if (!existing || orderTs < existing) {
            driverFirstOrder.set(o.driver_uuid, orderTs);
          }
        }
      }
    });

    // Calculer le nombre de drivers connectés cumulatif par jour
    // Convertir en array et trier par date pour s'assurer de l'ordre chronologique
    const sortedData = Array.from(dailyData.values()).sort((a, b) => a.date.getTime() - b.date.getTime());
    
    sortedData.forEach((dayData) => {
      const dayTimestamp = Math.floor(dayData.date.getTime() / 1000);
      
      // Compter combien de drivers ont eu leur première commande avant ou à cette date
      let count = 0;
      driverFirstOrder.forEach((firstOrderTs) => {
        if (firstOrderTs <= dayTimestamp) {
          count++;
        }
      });
      
      dayData.connected = count;
    });

    return sortedData;
  }, [orders, drivers]);

  if (loading) {
    return (
      <div className="analytics-page__loading-container">
        <div className="spinner"></div>
        <span className="analytics-page__loading-text">Chargement des analytics...</span>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-page__header">
        <div className="analytics-page__header-left">
          <div className="analytics-page__title-section">
            <FiBarChart2 className="analytics-page__title-icon" />
            <h1 className="analytics-page__title">User Insights</h1>
          </div>
          <div className="analytics-page__tabs">
            <button className="analytics-page__tab analytics-page__tab--active">
              <span className="analytics-page__tab-icon">●</span>
              Vue d'ensemble
            </button>
          </div>
        </div>
        <div className="analytics-page__header-right">
        </div>
      </div>

      {/* Key Insights Metrics */}
      <div className="analytics-page__section">
        <div className="analytics-page__section-header">
          <h2 className="analytics-page__section-title">Key insights metrics</h2>
          <select className="analytics-page__period-select" value={period} onChange={(e) => setPeriod(e.target.value as "week" | "month")}>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>
        <div className="analytics-page__metrics-grid">
          <StatCard
            label="No. of Connected Users"
            value={thisWeekMetrics.connectedUsers}
            icon={<FiCheckCircle />}
            color="primary"
          />
          <StatCard
            label="No. of working Users"
            value={thisWeekMetrics.workingUsers}
            icon={<FiTrendingUp />}
            color="success"
          />
          <StatCard
            label="Total Gross Earnings"
            value={`${thisWeekMetrics.totalGrossEarnings.toFixed(2)} €`}
            icon={<FiDollarSign />}
            color="info"
          />
        </div>
      </div>

      {/* Income Distribution Charts */}
      <div className="analytics-page__charts-row">
        <div className="analytics-page__chart-card">
          <h3 className="analytics-page__chart-title">
            Working users income distribution of this week
          </h3>
          <DistributionChart data={thisWeekDistribution} />
          <div className="analytics-page__no-earnings-card">
            Users with no earnings this week
            <strong className="analytics-page__no-earnings-value">
              {noEarningsThisWeekPercent.toFixed(2)}%
            </strong>
          </div>
        </div>
        <div className="analytics-page__chart-card">
          <h3 className="analytics-page__chart-title">
            Working users income distribution of last week
          </h3>
          <DistributionChart data={lastWeekDistribution} />
          <div className="analytics-page__no-earnings-card">
            Users with no earnings last week
            <strong className="analytics-page__no-earnings-value">
              {noEarningsLastWeekPercent.toFixed(2)}%
            </strong>
          </div>
        </div>
      </div>

      {/* Top Users and No Earning Users Tables */}
      <div className="analytics-page__tables-row">
        <div className="analytics-page__table-card">
          <TopUsersTable users={topUsers} period={period} />
        </div>
        <div className="analytics-page__table-card">
          <NoEarningUsersTable users={noEarningUsers} period={period} />
        </div>
      </div>

      {/* Evolution Chart */}
      <div className="analytics-page__evolution-section">
        <h3 className="analytics-page__evolution-title">
          Total earnings & number of connected users evolution
        </h3>
        <EarningsEvolutionChart data={evolutionData} />
      </div>
    </div>
  );
}
