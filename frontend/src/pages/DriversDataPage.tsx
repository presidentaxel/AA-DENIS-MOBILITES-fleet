import React, { useEffect, useState, useMemo } from "react";
import { RiSearchLine, RiCalendarLine, RiArrowUpDownLine, RiArrowDownSLine, RiArrowRightSLine } from "react-icons/ri";
import { getDrivers, getBoltDrivers, getBoltOrders } from "../api/fleetApi";
import { PlatformLogo } from "../components/PlatformLogo";
import { DateRangePicker } from "../components/DateRangePicker";
import "../styles/drivers-data-page.css";

type DriverDataRow = {
  name: string;
  platform: string;
  gross: number;
  net: number;
  contributionBase: number;
  taxes: number;
  bonuses: number;
  platformFee: number;
  cardEarnings: number;
  cashEarnings: number;
  expenses: number;
  fare: number;
  otherAmount: number;
  tips: number;
  payouts: number;
  reimbursements: number;
  email: string;
  afternoonTripsTotal: number;
  afternoonTripsTotalPercent: number;
  currency: string;
  distancePerTrip: number;
  distanceTotal: number;
  morningTripsTotal: number;
  morningTripsTotalPercent: number;
  nightTripsTotal: number;
  nightTripsTotalPercent: number;
  priceTotal: number;
  pricePerKm: number;
  pricePerTrip: number;
  pricePerWorkingHour: number;
  pricePerDrivingHour: number;
  tripsTotal: number;
  lastUpdate: string;
  status: string;
  firstConnection: string;
  userCreatedAt: string;
  driverId: string;
  platformLogo: string;
};

type GroupedDriverData = {
  driverId: string;
  name: string;
  email: string;
  platforms: DriverDataRow[];
  totalGross: number;
  totalNet: number;
  isExpanded: boolean;
};

type DriversDataPageProps = {
  token: string;
};

type SortConfig = {
  field: string;
  direction: "asc" | "desc";
};

// Helper function to get initials from name
const getInitials = (name: string): string => {
  if (!name) return "";
  const parts = name.trim().split(" ");
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
};

// Helper function to get avatar color
const getAvatarColor = (name: string): string => {
  const colors = [
    "#0061FF",
    "#5983FC",
    "#8FB571",
    "#F52922",
    "#FF6B35",
    "#4ECDC4",
    "#45B7D1",
    "#96CEB4",
    "#FFEAA7",
    "#DDA0DD",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
};

export function DriversDataPage({ token }: DriversDataPageProps) {
  const [uberDrivers, setUberDrivers] = useState<any[]>([]);
  const [boltDrivers, setBoltDrivers] = useState<any[]>([]);
  const [allOrders, setAllOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: "net", direction: "desc" });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [expandedDrivers, setExpandedDrivers] = useState<Set<string>>(new Set());

  // Set default dates (today)
  useEffect(() => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    setDateFrom(yesterday.toISOString().slice(0, 10));
    setDateTo(today.toISOString().slice(0, 10));
  }, []);

  // Fetch drivers and orders
  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [uberData, boltData] = await Promise.all([
          getDrivers(token, { limit: 200 }).catch(() => []),
          getBoltDrivers(token, { limit: 200 }).catch(() => []),
        ]);
        setUberDrivers(uberData || []);
        setBoltDrivers(boltData || []);

        // Fetch all orders for the last 2 years
        const now = new Date();
        const twoYearsAgo = new Date(now.getFullYear() - 2, 0, 1);
        const orders = await getBoltOrders(
          token,
          twoYearsAgo.toISOString().slice(0, 10),
          now.toISOString().slice(0, 10),
          undefined
        );
        setAllOrders(Array.isArray(orders) ? orders : []);
      } catch (err: any) {
        console.error("Erreur chargement drivers:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [token]);

  // Process data for grid - group by driver
  const groupedData = useMemo<GroupedDriverData[]>(() => {
    const driverMap = new Map<string, Map<string, DriverDataRow>>();

    // Process Bolt drivers
    boltDrivers.forEach((driver) => {
      const driverId = driver.id || driver.email;
      const email = driver.email || "";
      const fullName = `${driver.first_name || ""} ${driver.last_name || ""}`.trim() || driver.name || "";

      if (!driverMap.has(driverId)) {
        driverMap.set(driverId, new Map());
      }

      const platformMap = driverMap.get(driverId)!;
      if (!platformMap.has("bolt")) {
        // Filter orders by driver
        let driverOrders = allOrders.filter(
          (o: any) => o.driver_uuid === driverId || o.driver_id === driverId
        );

        // Apply date filter if dates are set
        if (dateFrom && dateTo) {
          const fromDate = new Date(dateFrom);
          fromDate.setHours(0, 0, 0, 0);
          const toDate = new Date(dateTo);
          toDate.setHours(23, 59, 59, 999);
          const fromTimestamp = fromDate.getTime();
          const toTimestamp = toDate.getTime();
          
          driverOrders = driverOrders.filter((o: any) => {
            // Use order_finished_timestamp for date filtering (when ride actually finished)
            const orderTimestamp = (o.order_finished_timestamp || o.order_created_timestamp || 0) * 1000;
            if (!orderTimestamp) return false;
            return orderTimestamp >= fromTimestamp && orderTimestamp <= toTimestamp;
          });
        }

        const gross = driverOrders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
        const net = driverOrders.reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
        const platformFee = driverOrders.reduce((sum: number, o: any) => sum + (o.commission || 0), 0);
        const tips = driverOrders.reduce((sum: number, o: any) => sum + (o.tip || 0), 0);
        const fare = driverOrders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
        const cashEarnings = driverOrders
          .filter((o: any) => o.payment_method === "cash")
          .reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
        const cardEarnings = net - cashEarnings;
        // Convert meters to kilometers (ride_distance is in meters)
        const distanceTotalMeters = driverOrders.reduce((sum: number, o: any) => sum + (o.ride_distance || 0), 0);
        const distanceTotal = distanceTotalMeters / 1000; // Convert to km
        const tripsTotal = driverOrders.length;
        const distancePerTrip = tripsTotal > 0 ? distanceTotal / tripsTotal : 0;
        const pricePerKm = distanceTotal > 0 ? fare / distanceTotal : 0;
        const pricePerTrip = tripsTotal > 0 ? fare / tripsTotal : 0;

        let morningTrips = 0;
        let afternoonTrips = 0;
        let nightTrips = 0;
        let totalWorkingSeconds = 0;

        driverOrders.forEach((o: any) => {
          // Use order_finished_timestamp for time-based calculations
          const orderTimestamp = o.order_finished_timestamp || o.order_created_timestamp;
          if (orderTimestamp) {
            const date = new Date(orderTimestamp * 1000);
            const hour = date.getHours();
            if (hour >= 5 && hour < 12) morningTrips++;
            else if (hour >= 12 && hour < 18) afternoonTrips++;
            else nightTrips++;
          }
          if (o.order_pickup_timestamp && o.order_drop_off_timestamp) {
            totalWorkingSeconds += o.order_drop_off_timestamp - o.order_pickup_timestamp;
          }
        });

        const workingHours = totalWorkingSeconds / 3600;
        const pricePerWorkingHour = workingHours > 0 ? net / workingHours : 0;
        const pricePerDrivingHour = workingHours > 0 ? net / workingHours : 0;

        const afternoonTripsTotalPercent = tripsTotal > 0 ? (afternoonTrips / tripsTotal) * 100 : 0;
        const morningTripsTotalPercent = tripsTotal > 0 ? (morningTrips / tripsTotal) * 100 : 0;
        const nightTripsTotalPercent = tripsTotal > 0 ? (nightTrips / tripsTotal) * 100 : 0;

        let lastUpdate = "";
        if (driverOrders.length > 0) {
          const sortedOrders = [...driverOrders].sort(
            (a: any, b: any) => {
              const aTs = a.order_finished_timestamp || a.order_created_timestamp || 0;
              const bTs = b.order_finished_timestamp || b.order_created_timestamp || 0;
              return bTs - aTs;
            }
          );
          const lastOrderTs = sortedOrders[0].order_finished_timestamp || sortedOrders[0].order_created_timestamp;
          if (lastOrderTs) {
            lastUpdate = new Date(lastOrderTs * 1000).toISOString();
          }
        }

        let firstConnection = "";
        if (driverOrders.length > 0) {
          const sortedOrders = [...driverOrders].sort(
            (a: any, b: any) => {
              const aTs = a.order_finished_timestamp || a.order_created_timestamp || 0;
              const bTs = b.order_finished_timestamp || b.order_created_timestamp || 0;
              return aTs - bTs;
            }
          );
          const firstOrderTs = sortedOrders[0].order_finished_timestamp || sortedOrders[0].order_created_timestamp;
          if (firstOrderTs) {
            firstConnection = new Date(firstOrderTs * 1000).toISOString();
          }
        }

        platformMap.set("bolt", {
          name: fullName,
          platform: "bolt",
          gross,
          net,
          contributionBase: 0,
          taxes: 0,
          bonuses: tips,
          platformFee,
          cardEarnings,
          cashEarnings,
          expenses: 0,
          fare,
          otherAmount: 0,
          tips,
          payouts: 0,
          reimbursements: 0,
          email,
          afternoonTripsTotal: afternoonTrips,
          afternoonTripsTotalPercent,
          currency: "€",
          distancePerTrip,
          distanceTotal,
          morningTripsTotal: morningTrips,
          morningTripsTotalPercent,
          nightTripsTotal: nightTrips,
          nightTripsTotalPercent,
          priceTotal: fare,
          pricePerKm,
          pricePerTrip,
          pricePerWorkingHour,
          pricePerDrivingHour,
          tripsTotal,
          lastUpdate,
          status: tripsTotal > 0 ? "connected" : "disconnected",
          firstConnection: firstConnection || driver.created_at || driver.connected_at || "",
          userCreatedAt: driver.created_at || driver.connected_at || "",
          driverId,
          platformLogo: "bolt",
        });
      }
    });

    // Process Uber drivers
    uberDrivers.forEach((driver) => {
      const driverId = driver.uuid || driver.id || driver.email;
      const email = driver.email || "";
      const fullName = `${driver.first_name || ""} ${driver.last_name || ""}`.trim() || driver.name || "";

      if (!driverMap.has(driverId)) {
        driverMap.set(driverId, new Map());
      }

      const platformMap = driverMap.get(driverId)!;
      if (!platformMap.has("uber")) {
        platformMap.set("uber", {
          name: fullName,
          platform: "uber",
          gross: 0,
          net: 0,
          contributionBase: 0,
          taxes: 0,
          bonuses: 0,
          platformFee: 0,
          cardEarnings: 0,
          cashEarnings: 0,
          expenses: 0,
          fare: 0,
          otherAmount: 0,
          tips: 0,
          payouts: 0,
          reimbursements: 0,
          email,
          afternoonTripsTotal: 0,
          afternoonTripsTotalPercent: 0,
          currency: "€",
          distancePerTrip: 0,
          distanceTotal: 0,
          morningTripsTotal: 0,
          morningTripsTotalPercent: 0,
          nightTripsTotal: 0,
          nightTripsTotalPercent: 0,
          priceTotal: 0,
          pricePerKm: 0,
          pricePerTrip: 0,
          pricePerWorkingHour: 0,
          pricePerDrivingHour: 0,
          tripsTotal: 0,
          lastUpdate: "",
          status: "connected",
          firstConnection: driver.created_at || driver.connected_at || "",
          userCreatedAt: driver.created_at || driver.connected_at || "",
          driverId,
          platformLogo: "uber",
        });
      }
    });

    // Group by driver
    const grouped: GroupedDriverData[] = [];
    driverMap.forEach((platformMap, driverId) => {
      const platforms = Array.from(platformMap.values());
      const firstPlatform = platforms[0];
      const totalGross = platforms.reduce((sum, p) => sum + p.gross, 0);
      const totalNet = platforms.reduce((sum, p) => sum + p.net, 0);

      grouped.push({
        driverId,
        name: firstPlatform.name,
        email: firstPlatform.email,
        platforms,
        totalGross,
        totalNet,
        isExpanded: expandedDrivers.has(driverId),
      });
    });

    return grouped;
  }, [uberDrivers, boltDrivers, allOrders, expandedDrivers, dateFrom, dateTo]);

  // Filter and sort grouped data
  const filteredAndSortedData = useMemo(() => {
    let filtered = groupedData;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (group) =>
          group.name.toLowerCase().includes(query) ||
          group.email.toLowerCase().includes(query) ||
          group.platforms.some((p) => p.platform.toLowerCase().includes(query))
      );
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      if (sortConfig.field === "name") {
        aValue = a.name;
        bValue = b.name;
      } else if (sortConfig.field === "net" || sortConfig.field === "gross") {
        aValue = sortConfig.field === "net" ? a.totalNet : a.totalGross;
        bValue = sortConfig.field === "net" ? b.totalNet : b.totalGross;
      } else {
        // For other fields, use first platform's value
        aValue = a.platforms[0] ? (a.platforms[0] as any)[sortConfig.field] : 0;
        bValue = b.platforms[0] ? (b.platforms[0] as any)[sortConfig.field] : 0;
      }

      if (aValue === bValue) return 0;

      if (typeof aValue === "number" && typeof bValue === "number") {
        return sortConfig.direction === "asc" ? aValue - bValue : bValue - aValue;
      }

      const aStr = String(aValue || "").toLowerCase();
      const bStr = String(bValue || "").toLowerCase();

      if (sortConfig.direction === "asc") {
        return aStr.localeCompare(bStr);
      }
      return bStr.localeCompare(aStr);
    });

    return sorted;
  }, [groupedData, searchQuery, sortConfig]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedData = filteredAndSortedData.slice(startIndex, endIndex);

  const handleSort = (field: string) => {
    setSortConfig({
      field,
      direction: sortConfig.field === field && sortConfig.direction === "asc" ? "desc" : "asc",
    });
    setCurrentPage(1);
  };

  const toggleExpand = (driverId: string) => {
    const newExpanded = new Set(expandedDrivers);
    if (newExpanded.has(driverId)) {
      newExpanded.delete(driverId);
    } else {
      newExpanded.add(driverId);
    }
    setExpandedDrivers(newExpanded);
  };

  const formatDateRange = (from: string, to: string) => {
    if (!from || !to) return "";
    try {
      const fromDate = new Date(from);
      const toDate = new Date(to);
      const formatDate = (date: Date) => {
        const day = date.getDate().toString().padStart(2, "0");
        const month = (date.getMonth() + 1).toString().padStart(2, "0");
        const year = date.getFullYear();
        return `${day} / ${month} / ${year}`;
      };
      return `${formatDate(fromDate)} - ${formatDate(toDate)}`;
    } catch {
      return "";
    }
  };

  const formatCurrency = (value: number) => `€${value.toFixed(2)}`;

  const formatDate = (dateString: string) => {
    if (!dateString) return "";
    try {
      return new Date(dateString).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    } catch {
      return "";
    }
  };

  // Column definitions - ALL columns visible
  const columns = [
    { key: "name", label: "Name", width: 250 },
    { key: "platform", label: "Platform", width: 150 },
    { key: "gross", label: "Gross", width: 140, align: "right" },
    { key: "net", label: "Net", width: 140, align: "right" },
    { key: "contributionBase", label: "Contribution base", width: 150, align: "right" },
    { key: "taxes", label: "Taxes", width: 140, align: "right" },
    { key: "bonuses", label: "Bonuses", width: 140, align: "right" },
    { key: "platformFee", label: "Platform Fee", width: 140, align: "right" },
    { key: "cardEarnings", label: "Card Earnings", width: 160, align: "right" },
    { key: "cashEarnings", label: "Cash Earnings", width: 160, align: "right" },
    { key: "expenses", label: "Expenses", width: 140, align: "right" },
    { key: "fare", label: "Fare", width: 140, align: "right" },
    { key: "otherAmount", label: "Other amount", width: 150, align: "right" },
    { key: "tips", label: "Tips", width: 140, align: "right" },
    { key: "payouts", label: "Payouts", width: 140, align: "right" },
    { key: "reimbursements", label: "Reimbursements", width: 180, align: "right" },
    { key: "email", label: "Email", width: 220 },
    { key: "afternoonTripsTotal", label: "Afternoon Trips Total", width: 200, align: "right" },
    { key: "afternoonTripsTotalPercent", label: "Afternoon Trips Total %", width: 220, align: "right" },
    { key: "currency", label: "Currency", width: 120 },
    { key: "distancePerTrip", label: "Distance Per Trip", width: 170, align: "right" },
    { key: "distanceTotal", label: "Distance Total", width: 160, align: "right" },
    { key: "morningTripsTotal", label: "Morning Trips Total", width: 180, align: "right" },
    { key: "morningTripsTotalPercent", label: "Morning Trips Total %", width: 210, align: "right" },
    { key: "nightTripsTotal", label: "Night Trips Total", width: 170, align: "right" },
    { key: "nightTripsTotalPercent", label: "Night Trips Total %", width: 190, align: "right" },
    { key: "priceTotal", label: "Price Total", width: 140, align: "right" },
    { key: "pricePerKm", label: "Price per km", width: 150, align: "right" },
    { key: "pricePerTrip", label: "Price per trip", width: 160, align: "right" },
    { key: "pricePerWorkingHour", label: "Price per working hour", width: 210, align: "right" },
    { key: "pricePerDrivingHour", label: "Price per driving hour", width: 210, align: "right" },
    { key: "tripsTotal", label: "Trips Total", width: 140, align: "right" },
    { key: "lastUpdate", label: "Last Update", width: 170 },
    { key: "status", label: "Status", width: 140 },
    { key: "firstConnection", label: "First connection", width: 170 },
    { key: "userCreatedAt", label: "User created at", width: 170 },
  ];

  const renderCellValue = (row: DriverDataRow, col: typeof columns[0]) => {
    const value = (row as any)[col.key];
    if (col.key === "platform") {
      return (
        <div className="platform-cell">
          <PlatformLogo platform={value} size={32} />
        </div>
      );
    }
    if (col.key === "status") {
      return (
        <div className="status-cell">
          <div className={`status-dot ${value === "connected" ? "connected" : "disconnected"}`} />
          <span>{value}</span>
        </div>
      );
    }
    if (typeof value === "number" && col.key.includes("Percent")) {
      return `${value.toFixed(2)}%`;
    }
    if (
      typeof value === "number" &&
      (col.key.includes("Earnings") ||
        col.key.includes("gross") ||
        col.key.includes("net") ||
        col.key.includes("taxes") ||
        col.key.includes("bonuses") ||
        col.key.includes("Fee") ||
        col.key.includes("expenses") ||
        col.key.includes("fare") ||
        col.key.includes("amount") ||
        col.key.includes("tips") ||
        col.key.includes("payouts") ||
        col.key.includes("reimbursements") ||
        col.key.includes("Price") ||
        col.key.includes("contribution"))
    ) {
      return formatCurrency(value);
    }
    if (typeof value === "number" && col.key.includes("distance")) {
      // Value is already in km (converted from meters)
      return `${value.toFixed(2)} km`;
    }
    if (typeof value === "number") {
      return value.toLocaleString();
    }
    if (col.key.includes("Update") || col.key.includes("Connection") || col.key.includes("Created")) {
      return formatDate(value);
    }
    return value || "—";
  };

  return (
    <div className="drivers-data-page">
      {/* Header */}
      <div className="header">
        <div className="header__left">
          <div className="header__title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M2 22C2 19.8783 2.84285 17.8434 4.34315 16.3431C5.84344 14.8429 7.87827 14 10 14C12.1217 14 14.1566 14.8429 15.6569 16.3431C17.1571 17.8434 18 19.8783 18 22H2ZM10 13C6.685 13 4 10.315 4 7C4 3.685 6.685 1 10 1C13.315 1 16 3.685 16 7C16 10.315 13.315 13 10 13ZM17.363 15.233C18.8926 15.6261 20.2593 16.4918 21.2683 17.7068C22.2774 18.9218 22.8774 20.4242 22.983 22H20C20 19.39 19 17.014 17.363 15.233ZM15.34 12.957C16.178 12.2075 16.8482 11.2893 17.3066 10.2627C17.765 9.23616 18.0013 8.12429 18 7C18.0021 5.63347 17.6526 4.28937 16.985 3.097C18.1176 3.32459 19.1365 3.93737 19.8685 4.8312C20.6004 5.72502 21.0002 6.84473 21 8C21.0003 8.71247 20.8482 9.41676 20.5541 10.0657C20.26 10.7146 19.8305 11.2931 19.2946 11.7625C18.7586 12.2319 18.1285 12.5814 17.4464 12.7874C16.7644 12.9934 16.0462 13.0512 15.34 12.957Z"
                fill="#0061FF"
              />
              <path
                d="M10 13C6.685 13 4 10.315 4 7C4 3.685 6.685 1 10 1C13.315 1 16 3.685 16 7C16 10.315 13.315 13 10 13Z"
                fill="#0093FD"
              />
              <path
                d="M17.363 15.2361C18.8926 15.6292 20.2592 16.4949 21.2683 17.7099C22.2773 18.9249 22.8774 20.4273 22.983 22.0031H20C20 19.3931 19 17.0171 17.363 15.2361ZM15.34 12.9601C16.178 12.2106 16.8481 11.2924 17.3065 10.2658C17.7649 9.23925 18.0012 8.12739 18 7.0031C18.0021 5.63656 17.6526 4.29247 16.985 3.1001C18.1176 3.32769 19.1365 3.94047 19.8684 4.83429C20.6004 5.72812 21.0002 6.84782 21 8.0031C21.0002 8.71556 20.8482 9.41986 20.5541 10.0688C20.2599 10.7177 19.8305 11.2962 19.2945 11.7656C18.7585 12.235 18.1284 12.5845 17.4464 12.7905C16.7644 12.9965 16.0462 13.0543 15.34 12.9601Z"
                fill="#0093FD"
              />
            </svg>
            <span>Users</span>
          </div>
          <div className="header__total">{filteredAndSortedData.length} in total</div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="controls">
        <div className="controls__row">
          <div className="search-container">
            <RiSearchLine className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by any column"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
          <div className="date-picker">
            <RiCalendarLine className="date-icon" />
            <input
              type="text"
              className="date-input"
              value={formatDateRange(dateFrom, dateTo)}
              readOnly
              onClick={() => setShowDatePicker(true)}
            />
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className="date-arrow">
              <path d="M4 6L8 10L12 6" stroke="#A8AFBC" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          {showDatePicker && (
            <DateRangePicker
              dateFrom={dateFrom}
              dateTo={dateTo}
              onApply={(from, to) => {
                setDateFrom(from);
                setDateTo(to);
                setCurrentPage(1);
              }}
              onClose={() => setShowDatePicker(false)}
            />
          )}
        </div>
        <div className="applied-filters">
          <span className="applied-filters__label">Applied Filters:</span>
        </div>
      </div>

      {/* Custom Grid */}
      <div className="custom-grid">
        <div className="grid-container">
          <table className="grid-table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    style={{ width: col.width, textAlign: (col.align || "left") as "left" | "right" | "center" }}
                    className={sortConfig.field === col.key ? "sorted" : ""}
                  >
                    <div className="th-content" onClick={() => handleSort(col.key)}>
                      <span>{col.label}</span>
                      {sortConfig.field === col.key && (
                        <span className="sort-indicator">
                          {sortConfig.direction === "asc" ? "↑" : "↓"}
                        </span>
                      )}
                      {sortConfig.field !== col.key && <RiArrowUpDownLine className="sort-icon" />}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={columns.length} className="loading-cell">
                    Loading...
                  </td>
                </tr>
              ) : paginatedData.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="empty-cell">
                    No data found
                  </td>
                </tr>
              ) : (
                paginatedData.flatMap((group) => {
                  const isExpanded = expandedDrivers.has(group.driverId);
                  const rows: JSX.Element[] = [];

                  // Main row (aggregated)
                  rows.push(
                    <tr key={group.driverId} className="main-row">
                      {columns.map((col) => {
                        if (col.key === "name") {
                          return (
                            <td key={col.key}>
                              <div className="name-cell">
                                <div
                                  className="expand-icon-wrapper"
                                  onClick={() => toggleExpand(group.driverId)}
                                >
                                  {isExpanded ? (
                                    <RiArrowDownSLine className="expand-icon" />
                                  ) : (
                                    <RiArrowRightSLine className="expand-icon" />
                                  )}
                                </div>
                                <div
                                  className="avatar"
                                  style={{ backgroundColor: getAvatarColor(group.name) }}
                                >
                                  {getInitials(group.name)}
                                </div>
                                <span>{group.name}</span>
                              </div>
                            </td>
                          );
                        }
                        if (col.key === "platform") {
                          return (
                            <td key={col.key}>
                              <div className="platform-cell">
                                {group.platforms.map((p) => (
                                  <PlatformLogo key={p.platform} platform={p.platform} size={32} />
                                ))}
                              </div>
                            </td>
                          );
                        }
                        if (col.key === "gross") {
                          return (
                            <td key={col.key} style={{ textAlign: "right" }}>
                              {formatCurrency(group.totalGross)}
                            </td>
                          );
                        }
                        if (col.key === "net") {
                          return (
                            <td key={col.key} style={{ textAlign: "right" }}>
                              {formatCurrency(group.totalNet)}
                            </td>
                          );
                        }
                        // For other columns, use first platform or aggregate
                        const firstPlatform = group.platforms[0];
                        return (
                          <td
                            key={col.key}
                            style={{ textAlign: (col.align || "left") as "left" | "right" | "center" }}
                          >
                            {firstPlatform ? renderCellValue(firstPlatform, col) : "—"}
                          </td>
                        );
                      })}
                    </tr>
                  );

                  // Expanded rows (one per platform)
                  if (isExpanded) {
                    group.platforms.forEach((platform, idx) => {
                      rows.push(
                        <tr key={`${group.driverId}-${platform.platform}-${idx}`} className="expanded-row">
                          {columns.map((col) => {
                            if (col.key === "name") {
                              return (
                                <td key={col.key}>
                                  <div className="name-cell expanded-name-cell">
                                    <div className="expand-icon-placeholder" />
                                    <div
                                      className="avatar"
                                      style={{ backgroundColor: getAvatarColor(platform.name) }}
                                    >
                                      {getInitials(platform.name)}
                                    </div>
                                    <span>{platform.name}</span>
                                  </div>
                                </td>
                              );
                            }
                            return (
                              <td
                                key={col.key}
                                style={{ textAlign: (col.align || "left") as "left" | "right" | "center" }}
                              >
                                {renderCellValue(platform, col)}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    });
                  }

                  return rows;
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            <button
              className="pagination-btn"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <div className="pagination-info">
              Page {currentPage} of {totalPages}
            </div>
            <button
              className="pagination-btn"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
