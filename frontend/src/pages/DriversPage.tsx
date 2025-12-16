import React, { useEffect, useState, useMemo } from "react";
import { FiUsers, FiCalendar, FiSearch, FiChevronDown, FiChevronRight, FiChevronLeft } from "react-icons/fi";
import { HiOutlineFilter } from "react-icons/hi";
import { RiFileList3Line } from "react-icons/ri";
import { FiExternalLink } from "react-icons/fi";
import { getBoltDrivers, getBoltOrders } from "../api/fleetApi";
import { PlatformLogo } from "../components/PlatformLogo";
import { UserPerformanceDrawer } from "../components/UserPerformanceDrawer";

type DriversPageProps = {
  token: string;
};

type DriverWithStats = {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  platforms: string[];
  gross: number;
  net: number;
  contributions: number;
  taxes: number;
  bonuses: number;
  platformEarnings: number;
  cardEarnings: number;
  cashEarnings: number;
  expenses: number;
  connectedOn?: string;
  status: "connected" | "disconnected";
};

export function DriversPage({ token }: DriversPageProps) {
  const [drivers, setDrivers] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [platformFilter, setPlatformFilter] = useState<string>("all");
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null);
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
        const [driversData, ordersData] = await Promise.all([
          getBoltDrivers(token, { limit: 200 }),
          getBoltOrders(token, dateFrom, dateTo).catch(() => []),
        ]);
        setDrivers(driversData);
        setOrders(ordersData);
      } catch (err: any) {
        console.error("Erreur chargement drivers:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [token, dateFrom, dateTo]);

  // Calculer les stats par driver
  const driversWithStats = useMemo<DriverWithStats[]>(() => {
    const statsMap = new Map<string, any>();

    orders.forEach((order: any) => {
      if (!order.driver_uuid) return;

      if (!statsMap.has(order.driver_uuid)) {
        statsMap.set(order.driver_uuid, {
          id: order.driver_uuid,
          gross: 0,
          net: 0,
          taxes: 0,
          bonuses: 0,
          platformEarnings: 0,
          cardEarnings: 0,
          cashEarnings: 0,
          expenses: 0,
          platforms: new Set<string>(),
          firstOrderDate: null,
        });
      }

      const stats = statsMap.get(order.driver_uuid);
      const ridePrice = order.ride_price || 0;
      const netEarnings = order.net_earnings || 0;
      const commission = order.commission || 0;

      stats.gross += ridePrice;
      stats.net += netEarnings;
      stats.platformEarnings += commission;
      stats.taxes += 0;
      stats.bonuses += order.tip || 0;
      
      if (order.payment_method === "cash") {
        stats.cashEarnings += netEarnings;
      } else {
        stats.cardEarnings += netEarnings;
      }

      stats.platforms.add("bolt");
      
      if (order.order_created_timestamp && (!stats.firstOrderDate || order.order_created_timestamp < stats.firstOrderDate)) {
        stats.firstOrderDate = order.order_created_timestamp;
      }
    });

    return drivers.map((driver) => {
      const stats = statsMap.get(driver.id) || {
        gross: 0,
        net: 0,
        taxes: 0,
        bonuses: 0,
        platformEarnings: 0,
        cardEarnings: 0,
        cashEarnings: 0,
        expenses: 0,
        platforms: new Set<string>(),
        firstOrderDate: null,
      };

      const connectedOn = stats.firstOrderDate 
        ? new Date(stats.firstOrderDate * 1000).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
        : undefined;

      return {
        id: driver.id,
        first_name: driver.first_name || "",
        last_name: driver.last_name || "",
        email: driver.email,
        phone: driver.phone,
        platforms: Array.from(stats.platforms),
        gross: stats.gross,
        net: stats.net,
        contributions: 0,
        taxes: stats.taxes,
        bonuses: stats.bonuses,
        platformEarnings: stats.platformEarnings,
        cardEarnings: stats.cardEarnings,
        cashEarnings: stats.cashEarnings,
        expenses: stats.expenses,
        connectedOn,
        status: stats.platforms.size > 0 ? "connected" as const : "disconnected" as const,
      };
    });
  }, [drivers, orders]);

  // Filtrer
  const filtered = useMemo(() => {
    let filtered = driversWithStats;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          `${d.first_name} ${d.last_name}`.toLowerCase().includes(query) ||
          d.email?.toLowerCase().includes(query) ||
          d.phone?.includes(query)
      );
    }

    if (statusFilter !== "all") {
      filtered = filtered.filter((d) => d.status === statusFilter);
    }

    if (platformFilter !== "all") {
      filtered = filtered.filter((d) => d.platforms.includes(platformFilter));
    }

    return filtered;
  }, [driversWithStats, searchQuery, statusFilter, platformFilter]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedDrivers = filtered.slice(startIndex, endIndex);

  useEffect(() => {
    // Reset to page 1 when filters change
    setCurrentPage(1);
  }, [searchQuery, statusFilter, platformFilter]);

  const handleRowClick = (driverId: string) => {
    setSelectedDriver(driverId);
    setDrawerOpen(true);
  };

  const handleArrowClick = (e: React.MouseEvent, driverId: string) => {
    e.stopPropagation();
    handleRowClick(driverId);
  };

  const getInitials = (firstName: string, lastName: string): string => {
    const first = firstName?.charAt(0).toUpperCase() || "";
    const last = lastName?.charAt(0).toUpperCase() || "";
    return first + last;
  };

  const selectedDriverObj = drivers.find((d) => d.id === selectedDriver);

  return (
    <div className="drivers-page">
      {/* Header */}
      <div className="drivers-page__header">
        <div className="drivers-page__header-left">
          <div className="drivers-page__title-section">
            <FiUsers className="drivers-page__title-icon" />
            <h1 className="drivers-page__title">Users</h1>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="drivers-page__filters">
        <div className="drivers-page__search-wrapper">
          <FiSearch className="drivers-page__search-icon" />
          <input
            type="text"
            className="drivers-page__search-input"
            placeholder="Search by name"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="drivers-page__filter-selects">
          <select
            className="drivers-page__filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">Status: All</option>
            <option value="connected">Connected</option>
            <option value="disconnected">Disconnected</option>
          </select>
          <select
            className="drivers-page__filter-select"
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
      <div className="drivers-page__layout">
        {/* Left Panel - User List */}
        <div className="drivers-page__left-panel">
          <table className="drivers-page__table">
            <thead className="drivers-page__table-head">
              <tr>
                <th className="drivers-page__table-th">Full Name</th>
                <th className="drivers-page__table-th">Platforms</th>
                <th className="drivers-page__table-th">Email</th>
                <th className="drivers-page__table-th">Connected On</th>
                <th className="drivers-page__table-th">Status</th>
              </tr>
            </thead>
            <tbody className="drivers-page__table-body">
              {paginatedDrivers.map((driver) => {
                const isHovered = hoveredRow === driver.id;
                const isSelected = selectedDriver === driver.id;

                return (
                  <tr
                    key={driver.id}
                    className={`drivers-page__table-row ${isSelected ? "drivers-page__table-row--selected" : ""}`}
                    onMouseEnter={() => setHoveredRow(driver.id)}
                    onMouseLeave={() => setHoveredRow(null)}
                    onClick={() => handleRowClick(driver.id)}
                  >
                    <td className="drivers-page__table-td">
                      <div className="drivers-page__driver-name">
                        <div className="drivers-page__driver-avatar-wrapper">
                          {isHovered ? (
                            <button
                              className="drivers-page__arrow-btn"
                              onClick={(e) => handleArrowClick(e, driver.id)}
                            >
                              <FiExternalLink />
                            </button>
                          ) : (
                            <div className="drivers-page__driver-avatar" style={{
                              backgroundColor: `hsl(${driver.id.charCodeAt(0) * 137.508 % 360}, 50%, 60%)`,
                            }}>
                              {getInitials(driver.first_name, driver.last_name)}
                            </div>
                          )}
                        </div>
                        <div className="drivers-page__driver-fullname">
                          {driver.first_name} {driver.last_name}
                        </div>
                      </div>
                    </td>
                    <td className="drivers-page__table-td">
                      <div className="drivers-page__platforms">
                        {driver.platforms.map((platform) => (
                          <PlatformLogo key={platform} platform={platform} size={32} />
                        ))}
                      </div>
                    </td>
                    <td className="drivers-page__table-td">{driver.email || "—"}</td>
                    <td className="drivers-page__table-td">{driver.connectedOn || "—"}</td>
                    <td className="drivers-page__table-td">
                      <span className={`drivers-page__status drivers-page__status--${driver.status}`}>
                        <span className="drivers-page__status-icon">
                          {driver.status === "connected" ? "✓" : "!"}
                        </span>
                        {driver.status === "connected" ? "Connected" : "Disconnected"}
                        <span className="drivers-page__status-count">{driver.platforms.length}</span>
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Right Panel - User Details */}
        {selectedDriverObj && (
          <div className="drivers-page__right-panel">
            <UserPerformanceDrawer
              driver={selectedDriverObj}
              isOpen={drawerOpen}
              onClose={() => {
                setDrawerOpen(false);
                setSelectedDriver(null);
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
        <div className="drivers-page__pagination">
          <button
            className="drivers-page__pagination-btn drivers-page__pagination-btn--prev"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            <FiChevronDown style={{ transform: 'rotate(90deg)' }} />
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button
              key={page}
              className={`drivers-page__pagination-btn drivers-page__pagination-btn--number ${
                currentPage === page ? "drivers-page__pagination-btn--active" : ""
              }`}
              onClick={() => setCurrentPage(page)}
            >
              {page}
            </button>
          ))}
          <button
            className="drivers-page__pagination-btn drivers-page__pagination-btn--next"
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
