import React, { useEffect, useState, useMemo } from "react";
import { FiTruck, FiSearch, FiChevronDown, FiExternalLink } from "react-icons/fi";
import { getBoltVehicles, getBoltOrders } from "../api/fleetApi";
import { PlatformLogo } from "../components/PlatformLogo";
import { VehiclePerformanceDrawer } from "../components/VehiclePerformanceDrawer";

type VehiclesPageProps = {
  token: string;
};

type VehicleWithStats = {
  id: string;
  plate: string;
  model?: string;
  platforms: string[];
  totalOrders: number;
  totalEarnings: number;
  totalDistance: number;
  connectedOn?: string;
  status: "connected" | "disconnected";
};

export function VehiclesPage({ token }: VehiclesPageProps) {
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [platformFilter, setPlatformFilter] = useState<string>("all");
  const [selectedVehicle, setSelectedVehicle] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(12);
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().slice(0, 10));

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [vehiclesData, ordersData] = await Promise.all([
          getBoltVehicles(token, { limit: 200 }),
          getBoltOrders(token, dateFrom, dateTo).catch(() => []),
        ]);
        setVehicles(vehiclesData);
        setOrders(ordersData);
      } catch (err: any) {
        console.error("Erreur chargement vehicles:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [token, dateFrom, dateTo]);

  // Calculer les stats par véhicule
  const vehiclesWithStats = useMemo<VehicleWithStats[]>(() => {
    const statsMap = new Map<string, any>();

    orders.forEach((order: any) => {
      if (!order.vehicle_license_plate) return;
      const plate = order.vehicle_license_plate;

      if (!statsMap.has(plate)) {
        statsMap.set(plate, {
          plate,
          totalOrders: 0,
          totalEarnings: 0,
          totalDistance: 0,
          platforms: new Set<string>(),
          firstOrderDate: null,
        });
      }

      const stats = statsMap.get(plate);
      stats.totalOrders += 1;
      stats.totalEarnings += order.net_earnings || 0;
      stats.totalDistance += order.ride_distance || 0;
      stats.platforms.add("bolt");

      if (order.order_created_timestamp && (!stats.firstOrderDate || order.order_created_timestamp < stats.firstOrderDate)) {
        stats.firstOrderDate = order.order_created_timestamp;
      }
    });

    return vehicles.map((vehicle) => {
      const stats = statsMap.get(vehicle.plate) || {
        totalOrders: 0,
        totalEarnings: 0,
        totalDistance: 0,
        platforms: new Set<string>(),
        firstOrderDate: null,
      };

      const connectedOn = stats.firstOrderDate
        ? new Date(stats.firstOrderDate * 1000).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
        : undefined;

      return {
        id: vehicle.id,
        plate: vehicle.plate,
        model: vehicle.model,
        platforms: Array.from(stats.platforms),
        totalOrders: stats.totalOrders,
        totalEarnings: stats.totalEarnings,
        totalDistance: stats.totalDistance,
        connectedOn,
        status: stats.platforms.size > 0 ? "connected" as const : "disconnected" as const,
      };
    });
  }, [vehicles, orders]);

  // Filtrer
  const filtered = useMemo(() => {
    let filtered = vehiclesWithStats;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (v) =>
          v.plate.toLowerCase().includes(query) ||
          (v.model && v.model.toLowerCase().includes(query))
      );
    }

    if (statusFilter !== "all") {
      filtered = filtered.filter((v) => v.status === statusFilter);
    }

    if (platformFilter !== "all") {
      filtered = filtered.filter((v) => v.platforms.includes(platformFilter));
    }

    return filtered;
  }, [vehiclesWithStats, searchQuery, statusFilter, platformFilter]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedVehicles = filtered.slice(startIndex, endIndex);

  useEffect(() => {
    // Reset to page 1 when filters change
    setCurrentPage(1);
  }, [searchQuery, statusFilter, platformFilter]);

  const handleRowClick = (vehicleId: string) => {
    setSelectedVehicle(vehicleId);
    setDrawerOpen(true);
  };

  const handleArrowClick = (e: React.MouseEvent, vehicleId: string) => {
    e.stopPropagation();
    handleRowClick(vehicleId);
  };

  const selectedVehicleObj = vehicles.find((v) => v.id === selectedVehicle);

  if (loading && vehicles.length === 0) {
    return (
      <div className="vehicles-page__loading-container">
        <div className="spinner"></div>
        <span className="vehicles-page__loading-text">Chargement des véhicules...</span>
      </div>
    );
  }

  return (
    <div className="vehicles-page">
      {/* Header */}
      <div className="vehicles-page__header">
        <div className="vehicles-page__header-left">
          <div className="vehicles-page__title-section">
            <FiTruck className="vehicles-page__title-icon" />
            <h1 className="vehicles-page__title">Vehicles</h1>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="vehicles-page__filters">
        <div className="vehicles-page__search-wrapper">
          <FiSearch className="vehicles-page__search-icon" />
          <input
            type="text"
            className="vehicles-page__search-input"
            placeholder="Search by plate or model"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="vehicles-page__filter-selects">
          <select
            className="vehicles-page__filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">Status: All</option>
            <option value="connected">Connected</option>
            <option value="disconnected">Disconnected</option>
          </select>
          <select
            className="vehicles-page__filter-select"
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
          >
            <option value="all">Platforms: All</option>
            <option value="bolt">Bolt</option>
            <option value="uber">Uber</option>
            <option value="heetch">Heetch</option>
            <option value="freenow">FreeNow</option>
          </select>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="vehicles-page__layout">
        {/* Left Panel - Vehicle List */}
        <div className="vehicles-page__left-panel">
          <table className="vehicles-page__table">
            <thead className="vehicles-page__table-head">
              <tr>
                <th className="vehicles-page__table-th">Plate</th>
                <th className="vehicles-page__table-th">Model</th>
                <th className="vehicles-page__table-th">Platforms</th>
                <th className="vehicles-page__table-th">Connected On</th>
                <th className="vehicles-page__table-th">Status</th>
              </tr>
            </thead>
            <tbody className="vehicles-page__table-body">
              {paginatedVehicles.map((vehicle) => {
                const isHovered = hoveredRow === vehicle.id;
                const isSelected = selectedVehicle === vehicle.id;

                return (
                  <tr
                    key={vehicle.id}
                    className={`vehicles-page__table-row ${isSelected ? "vehicles-page__table-row--selected" : ""}`}
                    onMouseEnter={() => setHoveredRow(vehicle.id)}
                    onMouseLeave={() => setHoveredRow(null)}
                    onClick={() => handleRowClick(vehicle.id)}
                  >
                    <td className="vehicles-page__table-td">
                      <div className="vehicles-page__vehicle-name">
                        <div className="vehicles-page__vehicle-avatar-wrapper">
                          {isHovered ? (
                            <button
                              className="vehicles-page__arrow-btn"
                              onClick={(e) => handleArrowClick(e, vehicle.id)}
                            >
                              <FiExternalLink />
                            </button>
                          ) : (
                            <div className="vehicles-page__vehicle-icon">
                              🚗
                            </div>
                          )}
                        </div>
                        <div className="vehicles-page__vehicle-plate">
                          {vehicle.plate}
                        </div>
                      </div>
                    </td>
                    <td className="vehicles-page__table-td">{vehicle.model || "—"}</td>
                    <td className="vehicles-page__table-td">
                      <div className="vehicles-page__platforms">
                        {vehicle.platforms.map((platform) => (
                          <PlatformLogo key={platform} platform={platform} size={32} />
                        ))}
                      </div>
                    </td>
                    <td className="vehicles-page__table-td">{vehicle.connectedOn || "—"}</td>
                    <td className="vehicles-page__table-td">
                      <span className={`vehicles-page__status vehicles-page__status--${vehicle.status}`}>
                        <span className="vehicles-page__status-icon">
                          {vehicle.status === "connected" ? "✓" : "!"}
                        </span>
                        {vehicle.status === "connected" ? "Connected" : "Disconnected"}
                        <span className="vehicles-page__status-count">{vehicle.platforms.length}</span>
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Right Panel - Vehicle Details */}
        {selectedVehicleObj && (
          <div className="vehicles-page__right-panel">
            <VehiclePerformanceDrawer
              vehicle={selectedVehicleObj}
              isOpen={drawerOpen}
              onClose={() => {
                setDrawerOpen(false);
                setSelectedVehicle(null);
              }}
              orders={orders}
              dateFrom={dateFrom}
              dateTo={dateTo}
            />
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="vehicles-page__pagination">
          <button
            className="vehicles-page__pagination-btn vehicles-page__pagination-btn--prev"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            <FiChevronDown style={{ transform: 'rotate(90deg)' }} />
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button
              key={page}
              className={`vehicles-page__pagination-btn vehicles-page__pagination-btn--number ${
                currentPage === page ? "vehicles-page__pagination-btn--active" : ""
              }`}
              onClick={() => setCurrentPage(page)}
            >
              {page}
            </button>
          ))}
          <button
            className="vehicles-page__pagination-btn vehicles-page__pagination-btn--next"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            <FiChevronDown style={{ transform: 'rotate(-90deg)' }} />
          </button>
        </div>
      )}
    </div>
  );
}
