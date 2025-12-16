import React from "react";
import { FiX, FiClock, FiArrowRight } from "react-icons/fi";
import { PlatformLogo } from "./PlatformLogo";

type VehiclePerformanceDrawerProps = {
  vehicle: any;
  isOpen: boolean;
  onClose: () => void;
  orders: any[];
  dateFrom: string;
  dateTo: string;
};

export function VehiclePerformanceDrawer({
  vehicle,
  isOpen,
  onClose,
  orders,
  dateFrom,
  dateTo,
}: VehiclePerformanceDrawerProps) {
  if (!isOpen || !vehicle) return null;

  // Calculer les stats depuis les orders
  const stats = React.useMemo(() => {
    const vehicleOrders = orders.filter((o: any) => o.vehicle_license_plate === vehicle.plate);
    
    const grossEarnings = vehicleOrders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
    const netEarnings = vehicleOrders.reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
    const totalTrips = vehicleOrders.length;
    const totalDistance = vehicleOrders.reduce((sum: number, o: any) => sum + (o.ride_distance || 0), 0);
    
    const completedOrders = vehicleOrders.filter((o: any) => 
      o.order_status && o.order_status.toLowerCase().includes("finished")
    ).length;
    
    // Calculer le temps total
    let totalTimeSeconds = 0;
    vehicleOrders.forEach((o: any) => {
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
    const pricePerKm = totalDistance > 0 ? (grossEarnings / totalDistance).toFixed(2) : "0.00";
    const cancellationRate = totalTrips > 0 ? ((totalTrips - completedOrders) / totalTrips * 100) : 0;
    
    return {
      grossEarnings,
      netEarnings,
      totalTrips,
      totalDistance,
      timeOnTrips,
      hourlyEarning,
      tripsPerHour,
      pricePerKm,
      completedOrders,
      cancellationRate,
    };
  }, [orders, vehicle]);

  const platforms = React.useMemo(() => {
    const vehicleOrders = orders.filter((o: any) => o.vehicle_license_plate === vehicle.plate);
    const platformSet = new Set<string>();
    vehicleOrders.forEach((o: any) => {
      platformSet.add("bolt");
    });
    return Array.from(platformSet);
  }, [orders, vehicle]);

  return (
    <div className={`vehicle-performance-drawer ${isOpen ? "vehicle-performance-drawer--open" : ""}`}>
      <div className="vehicle-performance-drawer__overlay" onClick={onClose}></div>
      <div className="vehicle-performance-drawer__content">
        <div className="vehicle-performance-drawer__header">
          <div className="vehicle-performance-drawer__header-left">
            <h2 className="vehicle-performance-drawer__title">{vehicle.plate}</h2>
            {vehicle.model && (
              <span className="vehicle-performance-drawer__subtitle">{vehicle.model}</span>
            )}
            <span className="vehicle-performance-drawer__status vehicle-performance-drawer__status--connected">
              <span className="vehicle-performance-drawer__status-icon">✓</span>
              Connected
            </span>
          </div>
          <button className="vehicle-performance-drawer__close" onClick={onClose}>
            <FiX />
          </button>
        </div>

        <div className="vehicle-performance-drawer__body">
          {/* Platform Info */}
          <div className="vehicle-performance-drawer__platform-info">
            {platforms.map((platform) => (
              <div key={platform} className="vehicle-performance-drawer__platform-tag">
                <PlatformLogo platform={platform} size={24} />
                <span>{platform} from {new Date(dateFrom).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })}</span>
              </div>
            ))}
          </div>

          {/* Vehicle Info Section */}
          <div className="vehicle-performance-drawer__section">
            <h3 className="vehicle-performance-drawer__section-title">Vehicle Information</h3>
            <div className="vehicle-performance-drawer__section-content">
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Plate:</span>
                <span className="vehicle-performance-drawer__field-value">{vehicle.plate}</span>
              </div>
              {vehicle.model && (
                <div className="vehicle-performance-drawer__field">
                  <span className="vehicle-performance-drawer__field-label">Model:</span>
                  <span className="vehicle-performance-drawer__field-value">{vehicle.model}</span>
                </div>
              )}
              {vehicle.provider_vehicle_id && (
                <div className="vehicle-performance-drawer__field">
                  <span className="vehicle-performance-drawer__field-label">Provider ID:</span>
                  <span className="vehicle-performance-drawer__field-value">{vehicle.provider_vehicle_id}</span>
                </div>
              )}
            </div>
          </div>

          {/* Earnings Section */}
          <div className="vehicle-performance-drawer__section">
            <h3 className="vehicle-performance-drawer__section-title">Earnings</h3>
            <div className="vehicle-performance-drawer__section-content">
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Gross Earnings:</span>
                <span className="vehicle-performance-drawer__field-value">€ {stats.grossEarnings.toFixed(2)}</span>
              </div>
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Net Earnings:</span>
                <span className="vehicle-performance-drawer__field-value">€ {stats.netEarnings.toFixed(2)}</span>
              </div>
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Price / Kilometer:</span>
                <span className="vehicle-performance-drawer__field-value">{stats.pricePerKm} €</span>
              </div>
            </div>
          </div>

          {/* Activity Section */}
          <div className="vehicle-performance-drawer__section">
            <h3 className="vehicle-performance-drawer__section-title">Activity</h3>
            <div className="vehicle-performance-drawer__section-content">
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Time On Trips:</span>
                <span className="vehicle-performance-drawer__field-value">{stats.timeOnTrips}</span>
              </div>
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Total Trips:</span>
                <span className="vehicle-performance-drawer__field-value">{stats.totalTrips}</span>
              </div>
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Completed Trips:</span>
                <span className="vehicle-performance-drawer__field-value">{stats.completedOrders}</span>
              </div>
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Distance:</span>
                <span className="vehicle-performance-drawer__field-value">{stats.totalDistance.toFixed(2)} km</span>
              </div>
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Hourly Earning:</span>
                <span className="vehicle-performance-drawer__field-value">{stats.hourlyEarning} €</span>
              </div>
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Trips / Hour:</span>
                <span className="vehicle-performance-drawer__field-value">{stats.tripsPerHour}</span>
              </div>
              <div className="vehicle-performance-drawer__field">
                <span className="vehicle-performance-drawer__field-label">Cancellation Rate:</span>
                <span className="vehicle-performance-drawer__field-value">{stats.cancellationRate.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Bottom Actions */}
          <div className="vehicle-performance-drawer__footer">
            <div className="vehicle-performance-drawer__footer-label">
              <FiClock className="vehicle-performance-drawer__footer-icon" />
              Performance Index
            </div>
            <button className="vehicle-performance-drawer__details-btn">
              Vehicle Details
              <FiArrowRight className="vehicle-performance-drawer__details-icon" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

