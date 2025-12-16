import React from "react";
import { FiX, FiClock, FiArrowRight, FiChevronUp, FiInfo } from "react-icons/fi";
import { PlatformLogo } from "./PlatformLogo";
import { calculatePerformanceScores, PerformanceScores } from "../utils/performanceCalculator";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";

type UserPerformanceDrawerProps = {
  driver: any;
  isOpen: boolean;
  onClose: () => void;
  orders: any[];
  dateFrom: string;
  dateTo: string;
};

export function UserPerformanceDrawer({
  driver,
  isOpen,
  onClose,
  orders,
  dateFrom,
  dateTo,
}: UserPerformanceDrawerProps) {
  if (!isOpen || !driver) return null;

  // Calculer les stats depuis les orders
  const stats = React.useMemo(() => {
    const driverOrders = orders.filter((o: any) => o.driver_uuid === driver.id);
    
    const grossEarnings = driverOrders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
    const netEarnings = driverOrders.reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
    const tips = driverOrders.reduce((sum: number, o: any) => sum + (o.tip || 0), 0);
    const fare = driverOrders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
    const cashEarnings = driverOrders.filter((o: any) => o.payment_method === "cash")
      .reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
    
    const totalTrips = driverOrders.length;
    const totalDistance = driverOrders.reduce((sum: number, o: any) => sum + (o.ride_distance || 0), 0);
    
    // Calculer le temps total (approximatif - basé sur les timestamps)
    let totalTimeSeconds = 0;
    driverOrders.forEach((o: any) => {
      if (o.order_pickup_timestamp && o.order_drop_off_timestamp) {
        totalTimeSeconds += (o.order_drop_off_timestamp - o.order_pickup_timestamp);
      }
    });
    const hours = Math.floor(totalTimeSeconds / 3600);
    const minutes = Math.floor((totalTimeSeconds % 3600) / 60);
    const seconds = Math.floor(totalTimeSeconds % 60);
    const timeOnTrips = `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    const hourlyEarning = hours > 0 ? (netEarnings / hours).toFixed(2) : "0.00";
    const tripsPerHour = hours > 0 ? (totalTrips / hours).toFixed(2) : "0.00";
    const pricePerKm = totalDistance > 0 ? (fare / totalDistance).toFixed(2) : "0.00";
    
    return {
      grossEarnings,
      netEarnings,
      tips,
      fare,
      cashEarnings,
      totalTrips,
      totalDistance,
      timeOnTrips,
      hourlyEarning,
      tripsPerHour,
      pricePerKm,
    };
  }, [orders, driver]);

  const platforms = React.useMemo(() => {
    const driverOrders = orders.filter((o: any) => o.driver_uuid === driver.id);
    const platformSet = new Set<string>();
    driverOrders.forEach((o: any) => {
      // Pour l'instant, on détecte Bolt uniquement
      platformSet.add("bolt");
    });
    return Array.from(platformSet);
  }, [orders, driver]);

  // Calculate performance scores
  const performanceScores = React.useMemo<PerformanceScores>(() => {
    return calculatePerformanceScores(orders, driver.id);
  }, [orders, driver.id]);

  // Prepare radar chart data
  const radarData = React.useMemo(() => {
    return [
      {
        subject: 'Income Score',
        score: performanceScores.incomeScore,
        fullMark: 100,
      },
      {
        subject: 'Working Efficiency Score',
        score: performanceScores.workingEfficiencyScore,
        fullMark: 100,
      },
      {
        subject: 'Working Stability Score',
        score: performanceScores.workingSustainabilityScore,
        fullMark: 100,
      },
    ];
  }, [performanceScores]);

  return (
    <div className={`user-performance-drawer ${isOpen ? "user-performance-drawer--open" : ""}`}>
      <div className="user-performance-drawer__overlay" onClick={onClose}></div>
      <div className="user-performance-drawer__content">
        <div className="user-performance-drawer__header">
          <div className="user-performance-drawer__header-left">
            <h2 className="user-performance-drawer__title">{driver.first_name} {driver.last_name}</h2>
            <span className="user-performance-drawer__status user-performance-drawer__status--connected">
              <span className="user-performance-drawer__status-icon">✓</span>
              Connected
            </span>
          </div>
          <button className="user-performance-drawer__close" onClick={onClose}>
            <FiX />
          </button>
        </div>

        <div className="user-performance-drawer__body">
          {/* Performance Scores */}
          <div className="user-performance-drawer__scores-section">
            <div className="user-performance-drawer__score-card">
              <div className="user-performance-drawer__score-label">Income Score</div>
              <div className="user-performance-drawer__score-value">
                {performanceScores.incomeScore} of 100
              </div>
            </div>
            <div className="user-performance-drawer__score-card">
              <div className="user-performance-drawer__score-label">Working Efficiency Score</div>
              <div className="user-performance-drawer__score-value">
                {performanceScores.workingEfficiencyScore} of 100
              </div>
            </div>
            <div className="user-performance-drawer__score-card">
              <div className="user-performance-drawer__score-label">
                Working Sustainability Score
                <FiChevronUp className="user-performance-drawer__score-expand-icon" />
              </div>
              <div className="user-performance-drawer__score-value">
                {performanceScores.workingSustainabilityScore} of 100
              </div>
            </div>
            <div className="user-performance-drawer__score-card user-performance-drawer__score-card--overall">
              <div className="user-performance-drawer__score-label">
                Overall Performance Score
                <FiInfo className="user-performance-drawer__score-info-icon" />
              </div>
              <div className="user-performance-drawer__score-value">
                {performanceScores.overallPerformanceScore} of 100
              </div>
            </div>
          </div>

          {/* Radar Chart */}
          <div className="user-performance-drawer__chart-section">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis 
                  dataKey="subject" 
                  tick={{ fontSize: 12, fill: '#64748b' }}
                />
                <PolarRadiusAxis 
                  angle={90} 
                  domain={[0, 100]}
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  ticks={[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]}
                />
                <Radar
                  name="Performance"
                  dataKey="score"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
            <div className="user-performance-drawer__chart-period">Last 90 days</div>
          </div>

          {/* Platform Info */}
          <div className="user-performance-drawer__platform-info">
            {platforms.map((platform) => (
              <div key={platform} className="user-performance-drawer__platform-tag">
                <PlatformLogo platform={platform} size={24} />
                <span>{platform} from {new Date(dateFrom).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })}</span>
              </div>
            ))}
          </div>

          {/* Profile Section */}
          <div className="user-performance-drawer__section">
            <h3 className="user-performance-drawer__section-title">Profile</h3>
            <div className="user-performance-drawer__section-content">
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Full Name:</span>
                <span className="user-performance-drawer__field-value">{driver.first_name} {driver.last_name}</span>
              </div>
              {driver.phone && (
                <div className="user-performance-drawer__field">
                  <span className="user-performance-drawer__field-label">Phone:</span>
                  <span className="user-performance-drawer__field-value">{driver.phone}</span>
                </div>
              )}
              {driver.email && (
                <div className="user-performance-drawer__field">
                  <span className="user-performance-drawer__field-label">Email:</span>
                  <span className="user-performance-drawer__field-value">{driver.email}</span>
                </div>
              )}
            </div>
          </div>

          {/* Income Section */}
          <div className="user-performance-drawer__section">
            <h3 className="user-performance-drawer__section-title">Income</h3>
            <div className="user-performance-drawer__section-content">
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Gross Earnings:</span>
                <span className="user-performance-drawer__field-value">€ {stats.grossEarnings.toFixed(2)}</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Net Earnings:</span>
                <span className="user-performance-drawer__field-value">€ {stats.netEarnings.toFixed(2)}</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Bonuses:</span>
                <span className="user-performance-drawer__field-value">€ {stats.tips.toFixed(2)}</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Tips:</span>
                <span className="user-performance-drawer__field-value">€ {stats.tips.toFixed(2)}</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Fare:</span>
                <span className="user-performance-drawer__field-value">€ {stats.fare.toFixed(2)}</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Cash Earnings:</span>
                <span className="user-performance-drawer__field-value">€ {stats.cashEarnings.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Activity Section */}
          <div className="user-performance-drawer__section">
            <h3 className="user-performance-drawer__section-title">Activity</h3>
            <div className="user-performance-drawer__section-content">
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Time On Trips:</span>
                <span className="user-performance-drawer__field-value">{stats.timeOnTrips}</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Total Trips:</span>
                <span className="user-performance-drawer__field-value">{stats.totalTrips}</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Distance:</span>
                <span className="user-performance-drawer__field-value">{stats.totalDistance.toFixed(2)} km</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Hourly Earning:</span>
                <span className="user-performance-drawer__field-value">{stats.hourlyEarning} €</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Trips / Hour:</span>
                <span className="user-performance-drawer__field-value">{stats.tripsPerHour}</span>
              </div>
              <div className="user-performance-drawer__field">
                <span className="user-performance-drawer__field-label">Price / Kilometer:</span>
                <span className="user-performance-drawer__field-value">{stats.pricePerKm} €</span>
              </div>
            </div>
          </div>

          {/* Bottom Actions */}
          <div className="user-performance-drawer__footer">
            <div className="user-performance-drawer__footer-label">
              <FiClock className="user-performance-drawer__footer-icon" />
              Performance Index
            </div>
            <button className="user-performance-drawer__details-btn">
              User Details
              <FiArrowRight className="user-performance-drawer__details-icon" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

