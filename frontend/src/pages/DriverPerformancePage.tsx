import React, { useEffect, useState, useMemo, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getBoltDriver, getBoltOrders, getBoltStateLogs } from "../api/fleetApi";
import { DateRangePicker } from "../components/DateRangePicker";
import { PlatformLogo } from "../components/PlatformLogo";
import "../styles/driver-performance-page.css";

type DriverPerformancePageProps = {
  token: string;
  onLogout: () => void;
};

type PeriodOption = "Today" | "Last 7 days" | "Custom";

export function DriverPerformancePage({ token, onLogout }: DriverPerformancePageProps) {
  const { driverId } = useParams<{ driverId: string }>();
  const navigate = useNavigate();
  const [driver, setDriver] = useState<any>(null);
  const [orders, setOrders] = useState<any[]>([]);
  const [stateLogs, setStateLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [periodFilter, setPeriodFilter] = useState<PeriodOption>("Last 7 days");
  const [showPeriodMenu, setShowPeriodMenu] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [activeTab, setActiveTab] = useState("Performance");
  const [selectedActivityDate, setSelectedActivityDate] = useState<string>(() => {
    const today = new Date();
    return today.toISOString().slice(0, 10);
  });
  const [scrollToEventId, setScrollToEventId] = useState<string | null>(null);
  const eventRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // Calculate date range based on period filter
  const dateRange = useMemo(() => {
    const now = new Date();
    let from: Date, to: Date = now;

    switch (periodFilter) {
      case "Today":
        from = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        from.setHours(0, 0, 0, 0);
        break;
      case "Last 7 days":
        from = new Date(now);
        from.setDate(from.getDate() - 7);
        from.setHours(0, 0, 0, 0);
        break;
      case "Custom":
        if (dateFrom && dateTo) {
          // Parse dates as local dates (YYYY-MM-DD format)
          const [fromYear, fromMonth, fromDay] = dateFrom.split('-').map(Number);
          const [toYear, toMonth, toDay] = dateTo.split('-').map(Number);
          from = new Date(fromYear, fromMonth - 1, fromDay, 0, 0, 0, 0);
          to = new Date(toYear, toMonth - 1, toDay, 23, 59, 59, 999);
        } else {
          from = new Date(now);
          from.setDate(from.getDate() - 7);
          from.setHours(0, 0, 0, 0);
        }
        break;
      default:
        from = new Date(now);
        from.setDate(from.getDate() - 7);
        from.setHours(0, 0, 0, 0);
    }

    return { from, to };
  }, [periodFilter, dateFrom, dateTo]);

  // Fetch driver and data
  useEffect(() => {
    if (!driverId) return;

    async function fetchData() {
      setLoading(true);
      try {
        // Helper function to format date as YYYY-MM-DD in local timezone
        const formatDateForAPI = (date: Date): string => {
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          return `${year}-${month}-${day}`;
        };

        const [driverData, ordersData, stateLogsData] = await Promise.all([
          getBoltDriver(token, driverId).catch(() => null),
          getBoltOrders(
            token,
            formatDateForAPI(dateRange.from),
            formatDateForAPI(dateRange.to),
            driverId
          ).catch(() => []),
          getBoltStateLogs(
            token,
            driverId,
            formatDateForAPI(dateRange.from),
            formatDateForAPI(dateRange.to)
          ).catch(() => []),
        ]);

        setDriver(driverData);
        setOrders(ordersData || []);
        setStateLogs(stateLogsData || []);
      } catch (err) {
        console.error("Error loading driver performance:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [token, driverId, dateRange.from, dateRange.to]);

  // Clean state logs: handle short disconnections and offline periods
  const cleanedStateLogs = useMemo(() => {
    if (!stateLogs || stateLogs.length === 0) return [];
    
    const sortedLogs = [...stateLogs].sort((a, b) => a.created - b.created);
    const cleaned: any[] = [];
    const SHORT_DISCONNECTION_THRESHOLD = 30 * 60; // 30 minutes in seconds
    const LONG_OFFLINE_THRESHOLD = 60 * 60; // 1 hour in seconds
    const skipIndices = new Set<number>(); // Track indices to skip
    
    for (let i = 0; i < sortedLogs.length; i++) {
      if (skipIndices.has(i)) continue;
      
      const current = sortedLogs[i];
      const prev = sortedLogs[i - 1];
      const next = sortedLogs[i + 1];
      
      const currentState = (current.state || "").toLowerCase();
      const prevState = prev ? (prev.state || "").toLowerCase() : null;
      const nextState = next ? (next.state || "").toLowerCase() : null;
      
      // Case 1: waiting → offline → waiting (short disconnection)
      // If we have: waiting → offline → waiting within SHORT_DISCONNECTION_THRESHOLD
      if (
        prevState === "waiting_orders" &&
        currentState === "inactive" &&
        nextState === "waiting_orders" &&
        (next.created - prev.created) <= SHORT_DISCONNECTION_THRESHOLD
      ) {
        // Skip this offline log - treat as continuous waiting
        skipIndices.add(i);
        continue;
      }
      
      // Case 2: offline → waiting then nothing, or offline > 1h
      if (currentState === "waiting_orders" && prevState === "inactive") {
        const offlineDuration = current.created - prev.created;
        
        // If offline was too long (> 1h) or there's no next log after waiting
        if (offlineDuration > LONG_OFFLINE_THRESHOLD || !next) {
          // Find the last waiting log before the offline period
          let lastWaitingLog = null;
          for (let j = i - 2; j >= 0; j--) {
            const checkState = (sortedLogs[j].state || "").toLowerCase();
            if (checkState === "waiting_orders") {
              lastWaitingLog = sortedLogs[j];
              break;
            }
          }
          
          if (lastWaitingLog) {
            // Check if we already added a log ending at prev.created
            const alreadyAdded = cleaned.some(
              log => log.created === prev.created && log.state === lastWaitingLog.state
            );
            
            if (!alreadyAdded) {
              // Add a log marking the end of the last waiting period (at start of offline)
              cleaned.push({
                ...lastWaitingLog,
                created: prev.created, // End of waiting period = start of offline
              });
            }
          }
          
          // Check if prev (offline) was already added
          const prevAlreadyAdded = cleaned.some(
            log => log.created === prev.created && log.state === prev.state
          );
          
          if (!prevAlreadyAdded) {
            cleaned.push(prev);
          }
          
          // If there's no next log, skip the waiting log (it's cancelled by offline)
          if (!next) {
            skipIndices.add(i);
            continue;
          }
          // Otherwise, add the waiting log normally (will be added in default case)
        }
      }
      
      // Case 3: Check if current offline period is too long (before adding it)
      if (currentState === "inactive" && next) {
        const offlineDuration = next.created - current.created;
        if (offlineDuration > LONG_OFFLINE_THRESHOLD) {
          // Find the last waiting log before this offline period
          let lastWaitingLog = null;
          for (let j = i - 1; j >= 0; j--) {
            const checkState = (sortedLogs[j].state || "").toLowerCase();
            if (checkState === "waiting_orders") {
              lastWaitingLog = sortedLogs[j];
              break;
            }
          }
          
          if (lastWaitingLog && lastWaitingLog.created < current.created) {
            // Check if we already added a log ending at current.created
            const alreadyAdded = cleaned.some(
              log => log.created === current.created && log.state === lastWaitingLog.state
            );
            
            if (!alreadyAdded) {
              // Insert a log marking the end of the last waiting period
              cleaned.push({
                ...lastWaitingLog,
                created: current.created, // End of waiting period = start of offline
              });
            }
          }
        }
      }
      
      // Default: add the log as-is (if not skipped)
      if (!skipIndices.has(i)) {
        cleaned.push(current);
      }
    }
    
    // Remove duplicates (same timestamp and state) and sort again
    const uniqueCleaned = cleaned.filter((log, idx, self) => 
      idx === self.findIndex((l) => l.created === log.created && l.state === log.state)
    );
    
    return uniqueCleaned.sort((a, b) => a.created - b.created);
  }, [stateLogs]);

  // Calculate KPIs
  const kpis = useMemo(() => {
    if (!orders.length) {
      return {
        totalEarnings: { gross: 0, net: 0 },
        earningsPerHour: { gross: 0, net: 0 },
        totalAcceptanceRate: 0,
        utilisation: 0,
        totalRideDistance: 0,
      };
    }

    // Filter orders by date range - convert timestamps to dates for comparison
    const dateRangeStartTs = Math.floor(dateRange.from.getTime() / 1000);
    const dateRangeEndTs = Math.floor(dateRange.to.getTime() / 1000);
    
    // Filter orders with earnings (within date range)
    // Include ALL orders that have earnings, not just "finished" ones
    // This includes: finished rides, cancelled orders with cancellation fees, etc.
    const ordersWithEarnings = orders.filter((o: any) => {
      // Use order_finished_timestamp if available, otherwise order_created_timestamp
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (!orderTs) return false;
      
      // Include orders that have any earnings:
      // - net_earnings > 0 (completed rides)
      // - cancellation_fee > 0 (cancelled orders with fees)
      // - ride_price > 0 (any order with a price)
      const hasEarnings = (o.net_earnings || 0) > 0 || 
                         (o.cancellation_fee || 0) > 0 || 
                         (o.ride_price || 0) > 0;
      
      if (!hasEarnings) return false;
      
      // Compare timestamps directly (both in seconds)
      return orderTs >= dateRangeStartTs && orderTs <= dateRangeEndTs;
    });
    
    // Finished orders (for distance and ride count)
    const finishedOrders = ordersWithEarnings.filter((o: any) => {
      const isFinished = o.order_status && o.order_status.toLowerCase().includes("finished");
      return isFinished && o.order_finished_timestamp;
    });
    
    // All orders in date range (for acceptance rate calculation)
    const ordersInRange = orders.filter((o: any) => {
      const orderTs = o.order_created_timestamp;
      if (!orderTs) return false;
      return orderTs >= dateRangeStartTs && orderTs <= dateRangeEndTs;
    });

    // Gross earnings = ride_price + tip + cancellation_fee (for all orders with earnings)
    const grossEarnings = ordersWithEarnings.reduce((sum: number, o: any) => {
      const ridePrice = o.ride_price || 0;
      const tip = o.tip || 0;
      const cancellationFee = o.cancellation_fee || 0;
      return sum + ridePrice + tip + cancellationFee;
    }, 0);
    
    // Net earnings = net_earnings + tip + cancellation_fee (for all orders with earnings)
    // Note: cancellation_fee is already included in net_earnings for cancelled orders,
    // but we add it explicitly to be sure we don't miss any earnings
    const netEarnings = ordersWithEarnings.reduce((sum: number, o: any) => {
      const netEarning = o.net_earnings || 0;
      const tip = o.tip || 0;
      const cancellationFee = o.cancellation_fee || 0;
      // If net_earnings is 0 but cancellation_fee exists, include it
      // Otherwise, use net_earnings (which may already include cancellation_fee)
      const totalNet = netEarning > 0 ? netEarning : cancellationFee;
      return sum + totalNet + tip;
    }, 0);
    
    // Total ride distance in km
    const totalRideDistance = finishedOrders.reduce((sum: number, o: any) => sum + ((o.ride_distance || 0) / 1000), 0);

    // Calculate working hours from state logs (filtered by date range)
    let totalWorkingSeconds = 0;
    let totalOnRideSeconds = 0;
    let totalWaitingSeconds = 0;

    if (cleanedStateLogs.length > 0) {
      // Filter state logs by date range
      const filteredLogs = cleanedStateLogs.filter(log => 
        log.created >= dateRangeStartTs && log.created <= dateRangeEndTs
      );
      
      const sortedLogs = [...filteredLogs].sort((a, b) => a.created - b.created);
      for (let i = 0; i < sortedLogs.length - 1; i++) {
        const current = sortedLogs[i];
        const next = sortedLogs[i + 1];
        const duration = next.created - current.created;

        // Map Bolt states to our categories
        // States: 'waiting_orders', 'has_order', 'inactive', 'busy'
        const state = current.state?.toLowerCase() || "";
        if (state === "has_order" || state === "busy") {
          // Driver has an order or is busy (on ride)
          totalWorkingSeconds += duration;
          totalOnRideSeconds += duration;
        } else if (state === "waiting_orders") {
          // Driver is waiting for orders
          totalWorkingSeconds += duration;
          totalWaitingSeconds += duration;
        } else if (state === "inactive") {
          // Driver is inactive/offline - not counted as working time
        }
      }
    }

    const workingHours = totalWorkingSeconds / 3600;
    const earningsPerHourGross = workingHours > 0 ? grossEarnings / workingHours : 0;
    const earningsPerHourNet = workingHours > 0 ? netEarnings / workingHours : 0;

    // Calculate acceptance rate: orders accepted (with order_accepted_timestamp) / total orders created
    const acceptedOrders = ordersInRange.filter((o: any) => 
      o.order_accepted_timestamp !== null && o.order_accepted_timestamp !== undefined
    );
    const totalAcceptanceRate = ordersInRange.length > 0 ? (acceptedOrders.length / ordersInRange.length) * 100 : 0;

    // Calculate utilisation (time on ride / total working time)
    const utilisation = totalWorkingSeconds > 0 ? (totalOnRideSeconds / totalWorkingSeconds) * 100 : 0;

    return {
      totalEarnings: { gross: grossEarnings, net: netEarnings },
      earningsPerHour: { gross: earningsPerHourGross, net: earningsPerHourNet },
      totalAcceptanceRate,
      utilisation,
      totalRideDistance,
      workingHours,
      onRideHours: totalOnRideSeconds / 3600,
      waitingHours: totalWaitingSeconds / 3600,
    };
  }, [orders, cleanedStateLogs, dateRange]);

  // Calculate activity summary
  const activitySummary = useMemo(() => {
    const totalHours = kpis.workingHours || 0;
    const onRideHours = kpis.onRideHours || 0;
    const waitingHours = kpis.waitingHours || 0;
    const breakHours = Math.max(0, totalHours - onRideHours - waitingHours);

    return {
      total: totalHours,
      onRide: onRideHours,
      waiting: waitingHours,
      onBreak: breakHours,
      onRidePercent: totalHours > 0 ? (onRideHours / totalHours) * 100 : 0,
      waitingPercent: totalHours > 0 ? (waitingHours / totalHours) * 100 : 0,
      onBreakPercent: totalHours > 0 ? (breakHours / totalHours) * 100 : 0,
    };
  }, [kpis]);

  // Calculate rides summary (filtered by date range)
  const ridesSummary = useMemo(() => {
    // Filter orders by date range
    const dateRangeStartTs = Math.floor(dateRange.from.getTime() / 1000);
    const dateRangeEndTs = Math.floor(dateRange.to.getTime() / 1000);
    
    const ordersInRange = orders.filter((o: any) => {
      const orderTs = o.order_created_timestamp;
      if (!orderTs) return false;
      return orderTs >= dateRangeStartTs && orderTs <= dateRangeEndTs;
    });
    
    const finishedRides = ordersInRange.filter((o: any) => o.order_status && o.order_status.toLowerCase().includes("finished"));
    const riderCancelled = ordersInRange.filter((o: any) => o.driver_cancelled_reason && o.driver_cancelled_reason.toLowerCase().includes("rider"));
    const riderNoShow = ordersInRange.filter((o: any) => o.order_status && o.order_status.toLowerCase().includes("no_show"));
    const driverCancelled = ordersInRange.filter((o: any) => o.driver_cancelled_reason && !o.driver_cancelled_reason.toLowerCase().includes("rider"));
    const driverRejected = ordersInRange.filter((o: any) => o.order_status && o.order_status.toLowerCase().includes("rejected"));
    const driverNoResponse = ordersInRange.filter((o: any) => !o.order_accepted_timestamp && o.order_created_timestamp);

    return {
      accepted: {
        finished: finishedRides.length,
        riderCancelled: riderCancelled.length,
        riderNoShow: riderNoShow.length,
      },
      declined: {
        driverCancelled: driverCancelled.length,
        driverRejected: driverRejected.length,
        driverNoResponse: driverNoResponse.length,
      },
    };
  }, [orders, dateRange]);

  // Prepare hourly overview data
  const hourlyOverviewData = useMemo(() => {
    // Helper function to format date as YYYY-MM-DD in local timezone
    const formatDateLocal = (date: Date): string => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    // Helper function to get day start/end timestamps in local timezone
    // This ensures the day boundaries match the local day, not UTC day
    const getLocalDayTimestamps = (year: number, month: number, day: number) => {
      // Create date at midnight local time
      const dayStart = new Date(year, month - 1, day, 0, 0, 0, 0);
      const dayEnd = new Date(year, month - 1, day, 23, 59, 59, 999);
      return {
        startTs: Math.floor(dayStart.getTime() / 1000),
        endTs: Math.floor(dayEnd.getTime() / 1000)
      };
    };

    // First, generate all days in the date range
    const allDays: { [key: string]: Date } = {};
    const currentDate = new Date(dateRange.from);
    currentDate.setHours(0, 0, 0, 0);
    const endDate = new Date(dateRange.to);
    endDate.setHours(23, 59, 59, 999);
    
    while (currentDate <= endDate) {
      // Use local date string (YYYY-MM-DD) as key for unique identification
      const dayKey = formatDateLocal(currentDate);
      allDays[dayKey] = new Date(currentDate);
      currentDate.setDate(currentDate.getDate() + 1);
    }

    const daysData: { [key: string]: any[] } = {};
    const sortedLogs = [...cleanedStateLogs].sort((a, b) => a.created - b.created);

    // Initialize all days with empty arrays
    Object.keys(allDays).forEach((dayKey) => {
      daysData[dayKey] = [];
    });

    // Helper function to format date as YYYY-MM-DD in local timezone
    const formatDateLocalForLog = (date: Date): string => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    // Group logs by day using local date string
    sortedLogs.forEach((log) => {
      const date = new Date(log.created * 1000);
      // Use local date string (YYYY-MM-DD) as key
      const dayKey = formatDateLocalForLog(date);
      if (daysData[dayKey]) {
        daysData[dayKey].push({
          timestamp: log.created,
          state: log.state,
          date,
        });
      }
    });

    // Generate segments for each day (including days without logs)
    return Object.entries(daysData).map(([day, logs]) => {
      const sortedDayLogs = logs.sort((a, b) => a.timestamp - b.timestamp);
      const segments: any[] = [];
      
      // Get day start and end timestamps using the day date from allDays
      // Parse dayKey to get year, month, day and calculate local day boundaries
      const [yearStr, monthStr, dayStr] = day.split('-');
      const dayYear = parseInt(yearStr, 10);
      const dayMonth = parseInt(monthStr, 10);
      const dayNum = parseInt(dayStr, 10);
      const { startTs: dayStartTs, endTs: dayEndTs } = getLocalDayTimestamps(dayYear, dayMonth, dayNum);
      const dayDuration = dayEndTs - dayStartTs;

      // If no logs for this day, return inactive for the whole day
      if (sortedDayLogs.length === 0) {
        segments.push({
          start: dayStartTs,
          end: dayEndTs,
          state: "inactive",
          duration: dayDuration,
        });
      } else {
        // Create segments from logs
        for (let i = 0; i < sortedDayLogs.length; i++) {
          const log = sortedDayLogs[i];
          const nextLog = sortedDayLogs[i + 1];
          
          // Add inactive segment before first log if needed
          if (i === 0 && log.timestamp > dayStartTs) {
            segments.push({
              start: dayStartTs,
              end: log.timestamp,
              state: "inactive",
              duration: log.timestamp - dayStartTs,
            });
          }

          // Add segment for current log
          const segmentEnd = nextLog ? nextLog.timestamp : dayEndTs;
          segments.push({
            start: log.timestamp,
            end: segmentEnd,
            state: log.state,
            duration: segmentEnd - log.timestamp,
          });
        }

        // Add inactive segment after last log if needed
        if (segments.length > 0 && segments[segments.length - 1].end < dayEndTs) {
          segments.push({
            start: segments[segments.length - 1].end,
            end: dayEndTs,
            state: "inactive",
            duration: dayEndTs - segments[segments.length - 1].end,
          });
        }
      }

      // Convert day key (YYYY-MM-DD) to display format
      const displayDay = allDays[day] ? allDays[day].toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" }) : day;
      
      return {
        day: displayDay,
        dayKey: day, // Keep the ISO key for reference
        dayDate: allDays[day] || new Date(),
        segments: segments.filter((s) => s.duration > 0),
        dayDuration,
      };
    }).sort((a, b) => {
      // Sort by date using the ISO key
        return a.dayKey.localeCompare(b.dayKey);
    });
  }, [cleanedStateLogs, dateRange]);

  // Prepare weekly performance summary (filtered by date range)
  const weeklySummary = useMemo(() => {
    const daysData: { [key: string]: any[] } = {};
    const dayDisplayNames: { [key: string]: string } = {};

    // Helper function to format date as YYYY-MM-DD in local timezone
    const formatDateLocalForOrder = (date: Date): string => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    // Filter orders by date range
    const dateRangeStartTs = Math.floor(dateRange.from.getTime() / 1000);
    const dateRangeEndTs = Math.floor(dateRange.to.getTime() / 1000);

    // Group orders by day based on order_created_timestamp (for counting)
    // But earnings will be calculated based on order_finished_timestamp
    orders.forEach((order) => {
      // Use order_created_timestamp for grouping by day (when the order was created/requested)
      const orderTs = order.order_created_timestamp;
      if (!orderTs) return;
      
      // Filter by date range (based on order_created_timestamp for grouping)
      if (orderTs < dateRangeStartTs || orderTs > dateRangeEndTs) return;
      
      const date = new Date(orderTs * 1000);
      // Use local date string (YYYY-MM-DD) as key for unique identification
      const dayKey = formatDateLocalForOrder(date);
      if (!daysData[dayKey]) {
        daysData[dayKey] = [];
        dayDisplayNames[dayKey] = date.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
      }
      daysData[dayKey].push(order);
    });

    return Object.entries(daysData)
      .map(([dayKey, dayOrders]) => {
        const day = dayDisplayNames[dayKey] || dayKey;
        
        // Parse dayKey to get day boundaries for filtering finished orders
        // Use local timezone to match the day grouping
        const [yearStr, monthStr, dayStr] = dayKey.split('-');
        const dayYear = parseInt(yearStr, 10);
        const dayMonth = parseInt(monthStr, 10);
        const dayNum = parseInt(dayStr, 10);
        const dayStart = new Date(dayYear, dayMonth - 1, dayNum, 0, 0, 0, 0);
        const dayEnd = new Date(dayYear, dayMonth - 1, dayNum, 23, 59, 59, 999);
        const dayStartTs = Math.floor(dayStart.getTime() / 1000);
        const dayEndTs = Math.floor(dayEnd.getTime() / 1000);
        
        // Filter orders with earnings for this day
        // Include ALL orders that have earnings, not just "finished" ones
        const ordersWithEarningsForDay = dayOrders.filter((o: any) => {
          // Use order_finished_timestamp if available, otherwise order_created_timestamp
          const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
          if (!orderTs) return false;
          
          // Include orders that have any earnings
          const hasEarnings = (o.net_earnings || 0) > 0 || 
                             (o.cancellation_fee || 0) > 0 || 
                             (o.ride_price || 0) > 0;
          
          if (!hasEarnings) return false;
          
          // Check if timestamp is within this day
          return orderTs >= dayStartTs && orderTs <= dayEndTs;
        });
        
        // Finished orders for distance and ride count (must have finished timestamp and status)
        const finishedOrdersForDay = ordersWithEarningsForDay.filter((o: any) => {
          const isFinished = o.order_status && o.order_status.toLowerCase().includes("finished");
          return isFinished && o.order_finished_timestamp;
        });
        
        // Gross earnings = ride_price + tip + cancellation_fee (for all orders with earnings)
        const gross = ordersWithEarningsForDay.reduce((sum: number, o: any) => {
          const ridePrice = o.ride_price || 0;
          const tip = o.tip || 0;
          const cancellationFee = o.cancellation_fee || 0;
          return sum + ridePrice + tip + cancellationFee;
        }, 0);
        
        // Net earnings = net_earnings + tip + cancellation_fee (for all orders with earnings)
        const net = ordersWithEarningsForDay.reduce((sum: number, o: any) => {
          const netEarning = o.net_earnings || 0;
          const tip = o.tip || 0;
          const cancellationFee = o.cancellation_fee || 0;
          // If net_earnings is 0 but cancellation_fee exists, include it
          const totalNet = netEarning > 0 ? netEarning : cancellationFee;
          return sum + totalNet + tip;
        }, 0);
        // Distance: sum of ride_distance for finished orders only (convert to km)
        const distance = finishedOrdersForDay.reduce((sum: number, o: any) => 
          sum + ((o.ride_distance || 0) / 1000), 0
        );
        
        // Finished rides: count orders with status "finished" that were finished on this day
        const finished = finishedOrdersForDay.length;
        
        // Accepted orders: orders that were accepted (have order_accepted_timestamp)
        const accepted = dayOrders.filter((o: any) => 
          o.order_accepted_timestamp !== null && o.order_accepted_timestamp !== undefined
        ).length;
        
        // Total orders created this day
        const total = dayOrders.length;

        // Calculate working hours for this day from state logs
        // Use the day boundaries already calculated above (dayStartTs, dayEndTs)

        // Filter state logs for this day, and also ensure they're within the selected date range
        const dateRangeStartTs = Math.floor(dateRange.from.getTime() / 1000);
        const dateRangeEndTs = Math.floor(dateRange.to.getTime() / 1000);
        
        const dayLogs = cleanedStateLogs.filter((log) => {
          return log.created >= dayStartTs && log.created <= dayEndTs &&
                 log.created >= dateRangeStartTs && log.created <= dateRangeEndTs;
        });

        let dayWorkingSeconds = 0;
        let dayOnRideSeconds = 0;
        if (dayLogs.length > 0) {
          const sortedDayLogs = [...dayLogs].sort((a, b) => a.created - b.created);
          for (let i = 0; i < sortedDayLogs.length - 1; i++) {
            const current = sortedDayLogs[i];
            const next = sortedDayLogs[i + 1];
            const duration = next.created - current.created;
            // States: 'waiting_orders', 'has_order', 'inactive', 'busy'
            const state = (current.state || "").toLowerCase();
            
            if (state === "has_order" || state === "busy") {
              dayWorkingSeconds += duration;
              dayOnRideSeconds += duration;
            } else if (state === "waiting_orders") {
              dayWorkingSeconds += duration;
            } else if (state === "inactive") {
              // Inactive time not counted
            }
          }
        }

        const dayWorkingHours = dayWorkingSeconds / 3600;
        const earningsPerHourGross = dayWorkingHours > 0 ? gross / dayWorkingHours : 0;
        const earningsPerHourNet = dayWorkingHours > 0 ? net / dayWorkingHours : 0;
        const finishRate = total > 0 ? (finished / total) * 100 : 0;
        const acceptanceRate = total > 0 ? (accepted / total) * 100 : 0;
        const utilisation = dayWorkingSeconds > 0 ? (dayOnRideSeconds / dayWorkingSeconds) * 100 : 0;

        return {
          day,
          dayKey, // Keep for sorting
          gross,
          net,
          earningsPerHourGross,
          earningsPerHourNet,
          finishRate,
          acceptanceRate,
          utilisation,
          finished,
          distance,
        };
      })
      .sort((a, b) => {
        // Sort by date using the dayKey (ISO format)
        return a.dayKey.localeCompare(b.dayKey);
      })
      .filter((daySummary) => {
        // Only include days that are within the selected date range
        // Parse dayKey (YYYY-MM-DD) and compare with dateRange
        const [yearStr, monthStr, dayStr] = daySummary.dayKey.split('-');
        const dayYear = parseInt(yearStr, 10);
        const dayMonth = parseInt(monthStr, 10);
        const dayNum = parseInt(dayStr, 10);
        const dayDate = new Date(dayYear, dayMonth - 1, dayNum);
        return dayDate >= dateRange.from && dayDate <= dateRange.to;
      });
  }, [orders, cleanedStateLogs, dateRange]);

  // Prepare detailed activity timeline
  const detailedActivity = useMemo(() => {
    const allEvents: any[] = [];
    const MIN_EVENT_DURATION_SECONDS = 10; // Filter events shorter than 10 seconds

    // Add state log events as timeline markers
    const sortedLogs = [...cleanedStateLogs].sort((a, b) => a.created - b.created);
    
    if (sortedLogs.length === 0) {
      // If no logs, return empty array (no state logs = no activity to display)
      return [];
    }

    // Group consecutive logs with the same state
    const groupedEvents: any[] = [];
    let currentGroup: any = null;

    for (let i = 0; i < sortedLogs.length; i++) {
      const currentLog = sortedLogs[i];
      const nextLog = sortedLogs[i + 1];
      
      const stateType = (currentLog.state || "").toLowerCase();
      let eventType = "offline";
      
      // Determine event type from state
      if (stateType === "has_order" || stateType === "busy") {
        eventType = "on_ride";
      } else if (stateType === "waiting_orders") {
        eventType = "waiting";
      } else if (stateType === "inactive") {
        eventType = "offline";
      } else {
        eventType = "offline";
      }
      
      // Group consecutive events with the same state
      if (!currentGroup || currentGroup.state !== currentLog.state || currentGroup.type !== eventType) {
        // Start a new group
        if (currentGroup) {
          // Set end time for previous group
          currentGroup.end = currentLog.created;
          groupedEvents.push(currentGroup);
        }
        currentGroup = {
          start: currentLog.created,
          end: nextLog ? nextLog.created : currentLog.created + 3600,
          type: eventType,
          state: currentLog.state,
          stateLogs: [currentLog],
          order: null, // Will be assigned later
          lat: currentLog.lat,
          lng: currentLog.lng,
        };
      } else {
        // Extend current group
        currentGroup.end = nextLog ? nextLog.created : currentLog.created + 3600;
        currentGroup.stateLogs.push(currentLog);
        // Keep the most recent lat/lng
        currentGroup.lat = currentLog.lat || currentGroup.lat;
        currentGroup.lng = currentLog.lng || currentGroup.lng;
      }
    }
    
    // Add the last group
    if (currentGroup) {
      groupedEvents.push(currentGroup);
    }

    // Now assign orders to groups more intelligently to avoid conflicts
    // This ensures each order is only assigned to the best matching group
    const assignedOrderRefs = new Set<string>(); // Track which orders have been assigned
    
    for (const group of groupedEvents) {
      if (group.type !== "on_ride") continue;
      
      // Find the best matching order for this group
      // Priority: order that overlaps the most with the group duration
      let bestOrder = null;
      let bestOverlap = 0;
      
      for (const order of orders) {
        const orderRef = order.order_reference;
        // Skip if this order was already assigned to another group
        if (assignedOrderRefs.has(orderRef)) continue;
        
        const orderStart = order.order_pickup_timestamp || order.order_accepted_timestamp || order.order_created_timestamp;
        const orderEnd = order.order_finished_timestamp || order.order_drop_off_timestamp;
        
        if (!orderStart) continue;
        
        // Calculate overlap between group and order
        const groupStart = group.start;
        const groupEnd = group.end;
        
        // Check if there's any overlap
        const overlapStart = Math.max(groupStart, orderStart);
        const overlapEnd = orderEnd ? Math.min(groupEnd, orderEnd) : groupEnd;
        
        if (overlapStart < overlapEnd) {
          // There's an overlap - calculate its duration
          const overlapDuration = overlapEnd - overlapStart;
          
          // Prefer orders with longer overlap
          if (overlapDuration > bestOverlap) {
            bestOverlap = overlapDuration;
            bestOrder = order;
          }
        }
      }
      
      // Assign the best matching order to this group
      if (bestOrder) {
        group.order = bestOrder;
        assignedOrderRefs.add(bestOrder.order_reference);
      }
    }

    // Filter out events shorter than MIN_EVENT_DURATION_SECONDS (except order events)
    const filteredGroupedEvents = groupedEvents.filter(event => {
      const duration = event.end - event.start;
      return duration >= MIN_EVENT_DURATION_SECONDS;
    });

    allEvents.push(...filteredGroupedEvents);

    // Note: Order events (driver_cancelled, driver_did_not_respond) are NOT added to the timeline
    // The detailed activity timeline is based solely on state logs to avoid noise.
    // These order events can be viewed in other views (e.g., orders list, performance metrics).

    // Sort all events by timestamp
    allEvents.sort((a, b) => a.start - b.start);

    // Add unique ID to each event for scrolling
    return allEvents.map((event, idx) => ({
      ...event,
      id: `event-${event.start}-${idx}-${event.stateLogs?.[0]?.id || event.stateLog?.id || event.order?.order_reference || idx}`,
      // Keep backward compatibility with stateLog (use first log from group)
      stateLog: event.stateLogs?.[0] || event.stateLog,
    }));
  }, [orders, cleanedStateLogs]);

  // Filter detailed activity by selected date
  const filteredDetailedActivity = useMemo(() => {
    if (!selectedActivityDate) return detailedActivity;
    
    // Parse date string (YYYY-MM-DD) and use local timezone to match day grouping
    const [yearStr, monthStr, dayStr] = selectedActivityDate.split('-');
    const year = parseInt(yearStr, 10);
    const month = parseInt(monthStr, 10);
    const day = parseInt(dayStr, 10);
    
    const dayStart = new Date(year, month - 1, day, 0, 0, 0, 0);
    const nextDay = new Date(year, month - 1, day + 1, 0, 0, 0, 0); // Start of next day
    
    const dayStartTs = Math.floor(dayStart.getTime() / 1000);
    const dayEndTs = Math.floor(nextDay.getTime() / 1000);
    
    return detailedActivity.filter((event) => {
      return event.start >= dayStartTs && event.start < dayEndTs;
    });
  }, [detailedActivity, selectedActivityDate]);

  // Scroll to event when scrollToEventId changes
  useEffect(() => {
    if (scrollToEventId && eventRefs.current[scrollToEventId]) {
      const element = eventRefs.current[scrollToEventId];
      if (element) {
        setTimeout(() => {
          element.scrollIntoView({ behavior: "smooth", block: "center" });
          setScrollToEventId(null);
        }, 100);
      }
    }
  }, [scrollToEventId, activeTab, filteredDetailedActivity]);

  // Helper function to format date as YYYY-MM-DD in local timezone
  const formatDateLocalForClick = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Handle click on hourly overview segment
  const handleSegmentClick = (segmentTimestamp: number, dayDate: Date) => {
    // Format the day date to match selectedActivityDate format (local timezone)
    const dateStr = formatDateLocalForClick(dayDate);
    
    // Find the closest event to this timestamp in all events (before filtering)
    const targetEvent = detailedActivity.find((event) => {
      const eventDate = new Date(event.start * 1000);
      const eventDateStr = formatDateLocalForClick(eventDate);
      if (eventDateStr === dateStr) {
        // Find event that contains this timestamp
        return event.start <= segmentTimestamp && event.end >= segmentTimestamp;
      }
      return false;
    }) || detailedActivity.find((event) => {
      const eventDate = new Date(event.start * 1000);
      const eventDateStr = formatDateLocalForClick(eventDate);
      if (eventDateStr === dateStr) {
        // Find the closest event by timestamp
        return Math.abs(event.start - segmentTimestamp) < 3600; // Within 1 hour
      }
      return false;
    }) || detailedActivity.find((event) => {
      const eventDate = new Date(event.start * 1000);
      const eventDateStr = formatDateLocalForClick(eventDate);
      return eventDateStr === dateStr;
    });
    
    // Update selected date and switch tab
    setSelectedActivityDate(dateStr);
    setActiveTab("Detailed activity");
    
    // Scroll to the event after state updates
    if (targetEvent && targetEvent.id) {
      setTimeout(() => {
        setScrollToEventId(targetEvent.id);
      }, 200);
    }
  };

  const formatHours = (hours: number) => {
    const h = Math.floor(hours);
    const m = Math.floor((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  const formatDateRange = () => {
    if (periodFilter === "Custom" && dateFrom && dateTo) {
      const from = new Date(dateFrom);
      const to = new Date(dateTo);
      return `${from.getDate()} ${from.toLocaleDateString("en-GB", { month: "short" })} - ${to.getDate()} ${to.toLocaleDateString("en-GB", { month: "short" })}`;
    } else if (periodFilter === "Today") {
      const today = new Date();
      return `${today.getDate()} ${today.toLocaleDateString("en-GB", { month: "short" })}`;
    } else if (periodFilter === "Last 7 days") {
      const to = new Date();
      const from = new Date();
      from.setDate(from.getDate() - 7);
      return `${from.getDate()} ${from.toLocaleDateString("en-GB", { month: "short" })} - ${to.getDate()} ${to.toLocaleDateString("en-GB", { month: "short" })}`;
    }
    return "";
  };

  // Construire le nom du driver de manière robuste avec useMemo pour être réactif
  // IMPORTANT: Les hooks doivent être appelés AVANT tout return conditionnel
  const driverName = useMemo(() => {
    if (!driver) return "Unknown Driver";
    const firstName = (driver.first_name || "").trim();
    const lastName = (driver.last_name || "").trim();
    const fullName = [firstName, lastName].filter(Boolean).join(" ");
    return fullName || driver.name || "Unknown Driver";
  }, [driver]);

  if (loading) {
    return (
      <div className="driver-performance-page">
        <div className="loading-state">Loading...</div>
      </div>
    );
  }

  if (!driver) {
    return (
      <div className="driver-performance-page">
        <div className="empty-state">Driver not found</div>
      </div>
    );
  }

  const driverScore = 100; // Placeholder
  const driverRating = 4.9; // Placeholder

  return (
    <div className="driver-performance-page">

        {/* Header */}
        <div className="driver-header">
          <div className="driver-header__left">
            <img
              src={driver.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(driverName)}&background=0061FF&color=fff`}
              alt="Driver profile"
              className="driver-header__avatar"
            />
            <div className="driver-header__info">
              <h1 className="driver-header__name">{driverName}</h1>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs">
          <div className="tabs__container">
            <button className={`tabs__tab ${activeTab === "Performance" ? "tabs__tab--active" : ""}`} onClick={() => setActiveTab("Performance")}>
              Performance
            </button>
            <button className={`tabs__tab ${activeTab === "Detailed activity" ? "tabs__tab--active" : ""}`} onClick={() => setActiveTab("Detailed activity")}>
              Detailed activity
            </button>
          </div>
        </div>

        {/* Date Range Selector */}
        {activeTab === "Performance" && (
          <div className="date-range-selector">
            <div className="date-range-selector__dates">
              <input
                type="text"
                className="date-input"
                placeholder="d MMM - d MMM"
                value={formatDateRange()}
                readOnly
                onClick={() => setShowDatePicker(true)}
              />
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="date-icon">
                <path fillRule="evenodd" clipRule="evenodd" d="M8 2C8.55228 2 9 2.44772 9 3V4H15V3C15 2.44772 15.4477 2 16 2C16.5523 2 17 2.44772 17 3V4H20C21.1046 4 22 4.89543 22 6V20C22 21.1046 21.1046 22 20 22H4C2.89543 22 2 21.1046 2 20V6C2 4.89543 2.89543 4 4 4H7V3C7 2.44772 7.44771 2 8 2ZM15 6V7C15 7.55228 15.4477 8 16 8C16.5523 8 17 7.55228 17 7V6H20V10H4V6H7V7C7 7.55228 7.44771 8 8 8C8.55228 8 9 7.55228 9 7V6H15Z" fill="currentColor" />
              </svg>
            </div>
          </div>
        )}

        {showDatePicker && (
          <DateRangePicker
            dateFrom={dateFrom}
            dateTo={dateTo}
            onApply={(from, to) => {
              setDateFrom(from);
              setDateTo(to);
              setPeriodFilter("Custom");
              setShowDatePicker(false);
            }}
            onClose={() => setShowDatePicker(false)}
          />
        )}

        {/* Performance Tab Content */}
        {activeTab === "Performance" && (
          <>
            {/* KPIs */}
            <div className="kpis-grid">
              <div className="kpi-card">
                <div className="kpi-card__header">
                  <span className="kpi-card__title">Total earnings</span>
                  <button className="kpi-card__info" aria-label="tooltip">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 6C11.3096 6 10.75 6.55964 10.75 7.25C10.75 7.94036 11.3096 8.5 12 8.5C12.6904 8.5 13.25 7.94036 13.25 7.25C13.25 6.55964 12.6904 6 12 6Z" fill="currentColor" />
                      <path d="M13 11.11L13 11.1192L13 11.1285V17.0996C13 17.6598 12.5523 18.114 12 18.114C11.4477 18.114 11 17.6598 11 17.0996V12.11H10C9.44772 12.11 9 11.6623 9 11.11C9 10.5577 9.44772 10.11 10 10.11H12C12.5523 10.11 13 10.5577 13 11.11Z" fill="currentColor" />
                      <path fillRule="evenodd" clipRule="evenodd" d="M4.22183 4.22183C6.21134 2.23231 8.96271 1 12 1C15.0373 1 17.7887 2.23231 19.7782 4.22183C21.7677 6.21134 23 8.96271 23 12C23 15.0373 21.7677 17.7887 19.7782 19.7782C17.7887 21.7677 15.0373 23 12 23C8.96271 23 6.21134 21.7677 4.22183 19.7782C2.23231 17.7887 1 15.0373 1 12C1 8.96271 2.23231 6.21134 4.22183 4.22183ZM12 3C9.51444 3 7.26581 4.00626 5.63604 5.63604C4.00626 7.26581 3 9.51444 3 12C3 14.4856 4.00626 16.7342 5.63604 18.364C7.26581 19.9937 9.51444 21 12 21C14.4856 21 16.7342 19.9937 18.364 18.364C19.9937 16.7342 21 14.4856 21 12C21 9.51444 19.9937 7.26581 18.364 5.63604C16.7342 4.00626 14.4856 3 12 3Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
                <div className="kpi-card__value">
                  <span className="kpi-card__value-main">{kpis.totalEarnings.gross.toFixed(1)}</span>
                  <span className="kpi-card__value-unit">€</span>
                </div>
                <div className="kpi-card__subvalue">
                  <span>{kpis.totalEarnings.net.toFixed(2)}€</span>
                  <span>Net</span>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-card__header">
                  <span className="kpi-card__title">Earnings per hour</span>
                  <button className="kpi-card__info" aria-label="tooltip">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 6C11.3096 6 10.75 6.55964 10.75 7.25C10.75 7.94036 11.3096 8.5 12 8.5C12.6904 8.5 13.25 7.94036 13.25 7.25C13.25 6.55964 12.6904 6 12 6Z" fill="currentColor" />
                      <path d="M13 11.11L13 11.1192L13 11.1285V17.0996C13 17.6598 12.5523 18.114 12 18.114C11.4477 18.114 11 17.6598 11 17.0996V12.11H10C9.44772 12.11 9 11.6623 9 11.11C9 10.5577 9.44772 10.11 10 10.11H12C12.5523 10.11 13 10.5577 13 11.11Z" fill="currentColor" />
                      <path fillRule="evenodd" clipRule="evenodd" d="M4.22183 4.22183C6.21134 2.23231 8.96271 1 12 1C15.0373 1 17.7887 2.23231 19.7782 4.22183C21.7677 6.21134 23 8.96271 23 12C23 15.0373 21.7677 17.7887 19.7782 19.7782C17.7887 21.7677 15.0373 23 12 23C8.96271 23 6.21134 21.7677 4.22183 19.7782C2.23231 17.7887 1 15.0373 1 12C1 8.96271 2.23231 6.21134 4.22183 4.22183ZM12 3C9.51444 3 7.26581 4.00626 5.63604 5.63604C4.00626 7.26581 3 9.51444 3 12C3 14.4856 4.00626 16.7342 5.63604 18.364C7.26581 19.9937 9.51444 21 12 21C14.4856 21 16.7342 19.9937 18.364 18.364C19.9937 16.7342 21 14.4856 21 12C21 9.51444 19.9937 7.26581 18.364 5.63604C16.7342 4.00626 14.4856 3 12 3Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
                <div className="kpi-card__value">
                  <span className="kpi-card__value-main">{kpis.earningsPerHour.gross.toFixed(2)}</span>
                  <span className="kpi-card__value-unit">€/h</span>
                </div>
                <div className="kpi-card__subvalue">
                  <span>{kpis.earningsPerHour.net.toFixed(2)}€/h</span>
                  <span>Net</span>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-card__header">
                  <span className="kpi-card__title">Total acceptance rate</span>
                  <button className="kpi-card__info" aria-label="tooltip">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 6C11.3096 6 10.75 6.55964 10.75 7.25C10.75 7.94036 11.3096 8.5 12 8.5C12.6904 8.5 13.25 7.94036 13.25 7.25C13.25 6.55964 12.6904 6 12 6Z" fill="currentColor" />
                      <path d="M13 11.11L13 11.1192L13 11.1285V17.0996C13 17.6598 12.5523 18.114 12 18.114C11.4477 18.114 11 17.6598 11 17.0996V12.11H10C9.44772 12.11 9 11.6623 9 11.11C9 10.5577 9.44772 10.11 10 10.11H12C12.5523 10.11 13 10.5577 13 11.11Z" fill="currentColor" />
                      <path fillRule="evenodd" clipRule="evenodd" d="M4.22183 4.22183C6.21134 2.23231 8.96271 1 12 1C15.0373 1 17.7887 2.23231 19.7782 4.22183C21.7677 6.21134 23 8.96271 23 12C23 15.0373 21.7677 17.7887 19.7782 19.7782C17.7887 21.7677 15.0373 23 12 23C8.96271 23 6.21134 21.7677 4.22183 19.7782C2.23231 17.7887 1 15.0373 1 12C1 8.96271 2.23231 6.21134 4.22183 4.22183ZM12 3C9.51444 3 7.26581 4.00626 5.63604 5.63604C4.00626 7.26581 3 9.51444 3 12C3 14.4856 4.00626 16.7342 5.63604 18.364C7.26581 19.9937 9.51444 21 12 21C14.4856 21 16.7342 19.9937 18.364 18.364C19.9937 16.7342 21 14.4856 21 12C21 9.51444 19.9937 7.26581 18.364 5.63604C16.7342 4.00626 14.4856 3 12 3Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
                <div className="kpi-card__value">
                  <span className="kpi-card__value-main">{kpis.totalAcceptanceRate.toFixed(0)}</span>
                  <span className="kpi-card__value-unit">%</span>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-card__header">
                  <span className="kpi-card__title">Utilisation</span>
                  <button className="kpi-card__info" aria-label="tooltip">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 6C11.3096 6 10.75 6.55964 10.75 7.25C10.75 7.94036 11.3096 8.5 12 8.5C12.6904 8.5 13.25 7.94036 13.25 7.25C13.25 6.55964 12.6904 6 12 6Z" fill="currentColor" />
                      <path d="M13 11.11L13 11.1192L13 11.1285V17.0996C13 17.6598 12.5523 18.114 12 18.114C11.4477 18.114 11 17.6598 11 17.0996V12.11H10C9.44772 12.11 9 11.6623 9 11.11C9 10.5577 9.44772 10.11 10 10.11H12C12.5523 10.11 13 10.5577 13 11.11Z" fill="currentColor" />
                      <path fillRule="evenodd" clipRule="evenodd" d="M4.22183 4.22183C6.21134 2.23231 8.96271 1 12 1C15.0373 1 17.7887 2.23231 19.7782 4.22183C21.7677 6.21134 23 8.96271 23 12C23 15.0373 21.7677 17.7887 19.7782 19.7782C17.7887 21.7677 15.0373 23 12 23C8.96271 23 6.21134 21.7677 4.22183 19.7782C2.23231 17.7887 1 15.0373 1 12C1 8.96271 2.23231 6.21134 4.22183 4.22183ZM12 3C9.51444 3 7.26581 4.00626 5.63604 5.63604C4.00626 7.26581 3 9.51444 3 12C3 14.4856 4.00626 16.7342 5.63604 18.364C7.26581 19.9937 9.51444 21 12 21C14.4856 21 16.7342 19.9937 18.364 18.364C19.9937 16.7342 21 14.4856 21 12C21 9.51444 19.9937 7.26581 18.364 5.63604C16.7342 4.00626 14.4856 3 12 3Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
                <div className="kpi-card__value">
                  <span className="kpi-card__value-main">{kpis.utilisation.toFixed(0)}</span>
                  <span className="kpi-card__value-unit">%</span>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-card__header">
                  <span className="kpi-card__title">Total ride distance</span>
                  <button className="kpi-card__info" aria-label="tooltip">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 6C11.3096 6 10.75 6.55964 10.75 7.25C10.75 7.94036 11.3096 8.5 12 8.5C12.6904 8.5 13.25 7.94036 13.25 7.25C13.25 6.55964 12.6904 6 12 6Z" fill="currentColor" />
                      <path d="M13 11.11L13 11.1192L13 11.1285V17.0996C13 17.6598 12.5523 18.114 12 18.114C11.4477 18.114 11 17.6598 11 17.0996V12.11H10C9.44772 12.11 9 11.6623 9 11.11C9 10.5577 9.44772 10.11 10 10.11H12C12.5523 10.11 13 10.5577 13 11.11Z" fill="currentColor" />
                      <path fillRule="evenodd" clipRule="evenodd" d="M4.22183 4.22183C6.21134 2.23231 8.96271 1 12 1C15.0373 1 17.7887 2.23231 19.7782 4.22183C21.7677 6.21134 23 8.96271 23 12C23 15.0373 21.7677 17.7887 19.7782 19.7782C17.7887 21.7677 15.0373 23 12 23C8.96271 23 6.21134 21.7677 4.22183 19.7782C2.23231 17.7887 1 15.0373 1 12C1 8.96271 2.23231 6.21134 4.22183 4.22183ZM12 3C9.51444 3 7.26581 4.00626 5.63604 5.63604C4.00626 7.26581 3 9.51444 3 12C3 14.4856 4.00626 16.7342 5.63604 18.364C7.26581 19.9937 9.51444 21 12 21C14.4856 21 16.7342 19.9937 18.364 18.364C19.9937 16.7342 21 14.4856 21 12C21 9.51444 19.9937 7.26581 18.364 5.63604C16.7342 4.00626 14.4856 3 12 3Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
                <div className="kpi-card__value">
                  <span className="kpi-card__value-main">{kpis.totalRideDistance.toFixed(1)}</span>
                  <span className="kpi-card__value-unit">km</span>
                </div>
              </div>
            </div>

            {/* Activity Summary & Rides Summary */}
            <div className="summary-grid">
              <div className="summary-card">
                <div className="summary-card__header">
                  <h3 className="summary-card__title">Activity summary</h3>
                  <span className="summary-card__total">Total: {formatHours(activitySummary.total)}</span>
                </div>
                <div className="activity-bars">
                  <div className="activity-bar">
                    <div className="activity-bar__label">
                      <span>On ride</span>
                      <span>{formatHours(activitySummary.onRide)}</span>
                    </div>
                    <div className="activity-bar__track">
                      <div className="activity-bar__fill activity-bar__fill--on-ride" style={{ width: `${activitySummary.onRidePercent}%` }} />
                    </div>
                  </div>
                  <div className="activity-bar">
                    <div className="activity-bar__label">
                      <span>Waiting</span>
                      <span>{formatHours(activitySummary.waiting)}</span>
                    </div>
                    <div className="activity-bar__track">
                      <div className="activity-bar__fill activity-bar__fill--waiting" style={{ width: `${activitySummary.waitingPercent}%` }} />
                    </div>
                  </div>
                  <div className="activity-bar">
                    <div className="activity-bar__label">
                      <span>On break</span>
                      <span>{formatHours(activitySummary.onBreak)}</span>
                    </div>
                    <div className="activity-bar__track">
                      <div className="activity-bar__fill activity-bar__fill--on-break" style={{ width: `${activitySummary.onBreakPercent}%` }} />
                    </div>
                  </div>
                </div>
              </div>

              <div className="summary-card">
                <h3 className="summary-card__title">Rides summary</h3>
                <div className="rides-summary">
                  <div className="rides-summary__section">
                    <h4 className="rides-summary__section-title">Accepted rides</h4>
                    <div className="rides-summary__item">
                      <span>Finished rides</span>
                      <span className="rides-summary__value">{ridesSummary.accepted.finished}</span>
                    </div>
                    <div className="rides-summary__item">
                      <span>Rider cancelled</span>
                      <span className="rides-summary__value">{ridesSummary.accepted.riderCancelled}</span>
                    </div>
                    <div className="rides-summary__item">
                      <span>Rider didn't show up</span>
                      <span className="rides-summary__value">{ridesSummary.accepted.riderNoShow}</span>
                    </div>
                  </div>
                  <div className="rides-summary__section">
                    <h4 className="rides-summary__section-title">Declined/cancelled rides</h4>
                    <div className="rides-summary__item">
                      <span>Driver cancelled</span>
                      <span className="rides-summary__value">{ridesSummary.declined.driverCancelled}</span>
                    </div>
                    <div className="rides-summary__item">
                      <span>Driver rejected</span>
                      <span className="rides-summary__value">{ridesSummary.declined.driverRejected}</span>
                    </div>
                    <div className="rides-summary__item">
                      <span>Driver didn't respond</span>
                      <span className="rides-summary__value">{ridesSummary.declined.driverNoResponse}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Hourly Overview */}
            <div className="hourly-overview-card">
              <h3 className="hourly-overview__title">Hourly overview</h3>
              <div className="hourly-overview__chart">
                {/* Hour labels */}
                <div className="hourly-overview__hours">
                  <div className="hourly-overview__day-label"></div>
                  <div className="hourly-overview__hour-labels">
                    {[2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 0].map((hour) => (
                      <div key={hour} className="hourly-overview__hour-label">
                        {hour}:00
                      </div>
                    ))}
                  </div>
                </div>
                {/* Day rows */}
                {hourlyOverviewData.length === 0 ? (
                  <div className="hourly-overview__empty">No activity data available</div>
                ) : (
                  hourlyOverviewData.map((dayData) => (
                    <div key={dayData.day} className="hourly-overview__day">
                      <div className="hourly-overview__day-name">{dayData.day}</div>
                      <div className="hourly-overview__day-bar">
                        {dayData.segments.map((segment, idx) => {
                          const widthPercent = dayData.dayDuration > 0 ? (segment.duration / dayData.dayDuration) * 100 : 0;
                          // Map Bolt states to CSS classes
                          // States: 'waiting_orders', 'has_order', 'inactive', 'busy'
                          const stateLower = (segment.state || "").toLowerCase();
                          const stateClass =
                            stateLower === "has_order" || stateLower === "busy"
                              ? "on-ride"
                              : stateLower === "waiting_orders"
                              ? "waiting"
                              : stateLower === "inactive"
                              ? "offline"
                              : "offline";
                          return (
                            <div
                              key={idx}
                              className={`hourly-overview__segment hourly-overview__segment--${stateClass}`}
                              style={{ width: `${widthPercent}%`, cursor: "pointer" }}
                              title={`${segment.state}: ${Math.floor(segment.duration / 60)} minutes`}
                              onClick={() => {
                                // Get the actual date from the segment timestamp
                                const segmentDate = new Date(segment.start * 1000);
                                handleSegmentClick(segment.start, segmentDate);
                              }}
                            />
                          );
                        })}
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="hourly-overview__legend">
                <div className="legend-item">
                  <div className="legend-item__color legend-item__color--offline"></div>
                  <span>Offline</span>
                </div>
                <div className="legend-item">
                  <div className="legend-item__color legend-item__color--on-break"></div>
                  <span>On break</span>
                </div>
                <div className="legend-item">
                  <div className="legend-item__color legend-item__color--waiting"></div>
                  <span>Waiting</span>
                </div>
                <div className="legend-item">
                  <div className="legend-item__color legend-item__color--on-ride"></div>
                  <span>On ride</span>
                </div>
              </div>
            </div>

            {/* Weekly Performance Summary Table */}
            <div className="weekly-summary-card">
              <h3 className="weekly-summary__title">Weekly performance summary</h3>
              <table className="weekly-summary__table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Earnings</th>
                    <th>Earnings per hour</th>
                    <th>Finish rate</th>
                    <th>Total acceptance rate</th>
                    <th>Utilisation</th>
                    <th>Finished rides</th>
                    <th>
                      Total ride distance
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path fillRule="evenodd" clipRule="evenodd" d="M12 1C8.96271 1 6.21134 2.23231 4.22183 4.22183C2.23231 6.21134 1 8.96271 1 12C1 15.0373 2.23231 17.7887 4.22183 19.7782C6.21134 21.7677 8.96271 23 12 23C15.0373 23 17.7887 21.7677 19.7782 19.7782C21.7677 17.7887 23 15.0373 23 12C23 8.96271 21.7677 6.21134 19.7782 4.22183C17.7887 2.23231 15.0373 1 12 1ZM12 6C11.3096 6 10.75 6.55964 10.75 7.25C10.75 7.94036 11.3096 8.5 12 8.5C12.6904 8.5 13.25 7.94036 13.25 7.25C13.25 6.55964 12.6904 6 12 6ZM13 11.1192L13 11.11C13 10.5577 12.5523 10.11 12 10.11H10C9.44772 10.11 9 10.5577 9 11.11C9 11.6623 9.44772 12.11 10 12.11H11V17.0996C11 17.6598 11.4477 18.114 12 18.114C12.5523 18.114 13 17.6598 13 17.0996V11.1285L13 11.1192Z" fill="currentColor" />
                      </svg>
                    </th>
                    <th></th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {weeklySummary.map((day, idx) => (
                    <tr key={idx}>
                      <td>{day.day}</td>
                      <td>
                        <div>
                          <span>{day.gross.toFixed(1)}</span>
                          <span className="table-unit">€</span>
                        </div>
                        <div className="table-subvalue">
                          <span>{day.net.toFixed(2)}€</span>
                          <span>Net</span>
                        </div>
                      </td>
                      <td>
                        <div>
                          <span>{day.earningsPerHourGross.toFixed(2)}</span>
                          <span className="table-unit">€/h</span>
                        </div>
                        <div className="table-subvalue">
                          <span>{day.earningsPerHourNet.toFixed(2)}€/h</span>
                          <span>Net</span>
                        </div>
                      </td>
                      <td>
                        <span>{day.finishRate.toFixed(0)}</span>
                        <span className="table-unit">%</span>
                      </td>
                      <td>
                        <span>{day.acceptanceRate.toFixed(0)}</span>
                        <span className="table-unit">%</span>
                      </td>
                      <td>
                        <span>{day.utilisation.toFixed(0)}</span>
                        <span className="table-unit">%</span>
                      </td>
                      <td>
                        <span>{day.finished}</span>
                      </td>
                      <td>
                        <span>{day.distance.toFixed(2)}</span>
                        <span className="table-unit">km</span>
                      </td>
                      <td></td>
                      <td>
                        <button className="table-action-button" aria-label="View detailed activity">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path fillRule="evenodd" clipRule="evenodd" d="M9.71294 4.2968C9.32241 4.68749 9.32241 5.32092 9.71294 5.71161L16.002 12.0038L9.71294 18.296C9.32241 18.6867 9.32241 19.3201 9.71294 19.7108C10.1035 20.1015 10.7366 20.1015 11.1272 19.7108L17.4163 13.4186C18.1973 12.6372 18.1973 11.3704 17.4163 10.589L11.1272 4.2968C10.7366 3.90611 10.1035 3.90611 9.71294 4.2968Z" fill="currentColor" />
                          </svg>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* Detailed activity tab */}
        {activeTab === "Detailed activity" && (
          <div className="detailed-activity">
            {/* Date selector for detailed activity */}
            <div className="detailed-activity__date-selector">
              <div className="date-range-selector__dates">
                <input
                  type="date"
                  className="date-input"
                  value={selectedActivityDate}
                  onChange={(e) => setSelectedActivityDate(e.target.value)}
                />
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="date-icon">
                  <path fillRule="evenodd" clipRule="evenodd" d="M8 2C8.55228 2 9 2.44772 9 3V4H15V3C15 2.44772 15.4477 2 16 2C16.5523 2 17 2.44772 17 3V4H20C21.1046 4 22 4.89543 22 6V20C22 21.1046 21.1046 22 20 22H4C2.89543 22 2 21.1046 2 20V6C2 4.89543 2.89543 4 4 4H7V3C7 2.44772 7.44771 2 8 2ZM15 6V7C15 7.55228 15.4477 8 16 8C16.5523 8 17 7.55228 17 7V6H20V10H4V6H7V7C7 7.55228 7.44771 8 8 8C8.55228 8 9 7.55228 9 7V6H15Z" fill="currentColor" />
                </svg>
              </div>
            </div>

            {filteredDetailedActivity.length === 0 ? (
              <div className="empty-state">No activity data available for selected date</div>
            ) : (
              <div className="activity-timeline">
                {filteredDetailedActivity.map((event, idx) => {
                  const startDate = new Date(event.start * 1000);
                  const endDate = new Date(event.end * 1000);
                  const duration = (event.end - event.start) / 60; // Duration in minutes
                  const hours = Math.floor(duration / 60);
                  const minutes = Math.floor(duration % 60);
                  const durationText = hours > 0 ? `${hours} h ${minutes} min` : `${minutes} min`;
                  
                  const formatTime = (timestamp: number) => {
                    const date = new Date(timestamp * 1000);
                    return date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
                  };

                  const getEventTypeClass = (type: string) => {
                    switch (type) {
                      case "on_ride":
                        return "activity-event--on-ride";
                      case "waiting":
                        return "activity-event--waiting";
                      case "offline":
                        return "activity-event--offline";
                      default:
                        // Handle direct state values
                        const stateLower = (type || "").toLowerCase();
                        if (stateLower === "has_order" || stateLower === "busy") {
                          return "activity-event--on-ride";
                        } else if (stateLower === "waiting_orders") {
                          return "activity-event--waiting";
                        } else if (stateLower === "inactive") {
                          return "activity-event--offline";
                        }
                        return "";
                    }
                  };

                  const getEventLabel = (type: string) => {
                    switch (type) {
                      case "on_ride":
                        return "On ride";
                      case "waiting":
                        return "Waiting";
                      case "offline":
                        return "Offline";
                      default:
                        // Handle direct state values from bolt_state_logs
                        const stateLower = (type || "").toLowerCase();
                        if (stateLower === "has_order" || stateLower === "busy") {
                          return "On ride";
                        } else if (stateLower === "waiting_orders") {
                          return "Waiting";
                        } else if (stateLower === "inactive") {
                          return "Offline";
                        }
                        return type;
                    }
                  };

                  const getAddress = () => {
                    if (event.order) {
                      const stops = event.order.order_stops || [];
                      if (stops.length > 0) {
                        const pickup = stops[0];
                        const dropoff = stops[stops.length - 1];
                        const pickupAddr = pickup.address || pickup.pickup_address || event.order.pickup_address || "";
                        const dropoffAddr = dropoff.address || dropoff.dropoff_address || "";
                        if (pickupAddr && dropoffAddr) {
                          return `${pickupAddr} → ${dropoffAddr}`;
                        }
                        return pickupAddr || dropoffAddr || event.order.pickup_address || "Unknown";
                      }
                      return event.order.pickup_address || "Unknown";
                    }
                    if (event.stateLog && (event.type === "waiting" || event.type === "offline")) {
                      return "Last location";
                    }
                    return "";
                  };

                  return (
                    <div
                      key={event.id || idx}
                      ref={(el) => {
                        if (event.id) {
                          eventRefs.current[event.id] = el;
                        }
                      }}
                      className={`activity-event ${getEventTypeClass(event.type)} ${scrollToEventId === event.id ? "activity-event--highlighted" : ""}`}
                    >
                      <div className="activity-event__header">
                        <div className="activity-event__time">
                          {formatTime(event.start)} - {formatTime(event.end)}
                        </div>
                        <div className={`activity-event__badge ${getEventTypeClass(event.state || event.type)}`}>
                          {getEventLabel(event.state || event.type)}
                        </div>
                      </div>
                      {(event.order || (event.stateLog && (event.type === "waiting" || event.type === "offline"))) && (
                        <div className="activity-event__address">{getAddress()}</div>
                      )}
                      <div className="activity-event__details">
                        <div className="activity-event__detail">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M11 6.00002C11 5.44773 11.4477 5.00002 12 5.00002C12.5523 5.00002 13 5.44773 13 6.00002V11.999C13 12.3039 12.8609 12.5922 12.6222 12.7819L8.74603 15.8624C8.31366 16.2061 7.6846 16.1341 7.34098 15.7018C6.99736 15.2694 7.0693 14.6403 7.50167 14.2967L11 11.5164V6.00002Z" fill="currentColor" />
                            <path fillRule="evenodd" clipRule="evenodd" d="M11.9991 1.00092C5.92399 1.00092 1 5.92692 1 12C1 18.075 5.9241 22.9991 11.9991 22.9991C18.0739 22.9991 23 18.0753 23 12C23 5.92669 18.074 1.00092 11.9991 1.00092ZM3 12C3 7.03126 7.02879 3.00092 11.9991 3.00092C16.9697 3.00092 21 7.03149 21 12C21 16.9702 16.9698 20.9991 11.9991 20.9991C7.02867 20.9991 3 16.9705 3 12Z" fill="currentColor" />
                          </svg>
                          <span>{durationText}</span>
                        </div>
                        {event.order && (
                          <>
                            {event.order.ride_distance > 0 && (
                              <div className="activity-event__detail">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                  <path fillRule="evenodd" clipRule="evenodd" d="M5.24886 20.7901C4.5601 20.7901 3.9993 20.2291 3.9993 19.5401C3.9993 18.8511 4.5601 18.2901 5.24886 18.2901C5.93762 18.2901 6.49843 18.8511 6.49843 19.5401C6.49843 20.2291 5.93762 20.7901 5.24886 20.7901ZM19.154 12.9701L5.4298 8.70008C4.58909 8.43808 4.02329 7.67008 4.02329 6.79008C4.02329 5.68708 4.92098 4.79008 6.02259 4.79008H18.7301L18.7331 4.79308L18.7301 4.79108L17.7105 5.90608C17.3376 6.31408 17.3646 6.94608 17.7725 7.31908C18.1793 7.69108 18.8111 7.66408 19.184 7.25708L21.7371 4.46508C22.088 4.08208 22.088 3.49708 21.7371 3.11408L19.184 0.324078C18.8111 -0.0829222 18.1793 -0.109922 17.7725 0.262078C17.3646 0.635078 17.3376 1.26708 17.7105 1.67508L18.7301 2.79008H6.02259C3.81736 2.79008 2.02399 4.58308 2.02399 6.79008C2.02399 8.55108 3.1536 10.0861 4.83601 10.6101L18.5602 14.8801C19.4009 15.1421 19.9667 15.9091 19.9667 16.7901C19.9667 17.8931 19.069 18.7901 17.9674 18.7901H8.40176C8.06088 17.3601 6.78133 16.2901 5.24886 16.2901C3.45749 16.2901 2 17.7481 2 19.5401C2 21.3321 3.45749 22.7901 5.24886 22.7901C6.59739 22.7901 7.75599 21.9631 8.24581 20.7901H17.9674C20.1726 20.7901 21.966 18.9961 21.966 16.7901C21.966 15.0281 20.8364 13.4931 19.154 12.9701Z" fill="currentColor" />
                                </svg>
                                <span>{(event.order.ride_distance / 1000).toFixed(1)} km</span>
                              </div>
                            )}
                            {event.order.category_name && (
                              <div className="activity-event__detail">
                                <span>{event.order.category_name}</span>
                              </div>
                            )}
                            {/* Revenus détaillés */}
                            {((event.order.net_earnings || 0) > 0 || (event.order.cancellation_fee || 0) > 0 || (event.order.ride_price || 0) > 0) && (
                              <div className="activity-event__earnings">
                                {(event.order.net_earnings || 0) > 0 && (
                                  <div className="activity-event__earnings-item activity-event__earnings-item--net">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                      <path d="M7.5 16C7.5 16.8284 6.82843 17.5 6 17.5C5.17157 17.5 4.5 16.8284 4.5 16C4.5 15.1716 5.17157 14.5 6 14.5C6.82843 14.5 7.5 15.1716 7.5 16Z" fill="currentColor" />
                                      <path fillRule="evenodd" clipRule="evenodd" d="M7.00002 3C5.89545 3 5.00002 3.89543 5.00002 5V7H3C1.89543 7 1 7.89543 1 9V19C1 20.1046 1.89543 21 3 21H17C18.1046 21 19 20.1046 19 19V17.0032H21C22.1046 17.0032 23 16.1078 23 15.0032V5C23 3.89543 22.1046 3 21 3H7.00002ZM19 15.0032H21V5H7.00002V7H17C18.1046 7 19 7.89543 19 9V15.0032ZM3 9H17V11H3V9ZM3 13V19H17V13H3Z" fill="currentColor" />
                                    </svg>
                                    <span className="activity-event__earnings-label">Net:</span>
                                    <span className="activity-event__earnings-value">+€{((event.order.net_earnings || 0) + (event.order.tip || 0)).toFixed(2)}</span>
                                    {(event.order.tip || 0) > 0 && (
                                      <span className="activity-event__earnings-tip">(+€{(event.order.tip || 0).toFixed(2)} tip)</span>
                                    )}
                                  </div>
                                )}
                                {(event.order.cancellation_fee || 0) > 0 && (event.order.net_earnings || 0) === 0 && (
                                  <div className="activity-event__earnings-item activity-event__earnings-item--cancellation">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                      <path d="M7.5 16C7.5 16.8284 6.82843 17.5 6 17.5C5.17157 17.5 4.5 16.8284 4.5 16C4.5 15.1716 5.17157 14.5 6 14.5C6.82843 14.5 7.5 15.1716 7.5 16Z" fill="currentColor" />
                                      <path fillRule="evenodd" clipRule="evenodd" d="M7.00002 3C5.89545 3 5.00002 3.89543 5.00002 5V7H3C1.89543 7 1 7.89543 1 9V19C1 20.1046 1.89543 21 3 21H17C18.1046 21 19 20.1046 19 19V17.0032H21C22.1046 17.0032 23 16.1078 23 15.0032V5C23 3.89543 22.1046 3 21 3H7.00002ZM19 15.0032H21V5H7.00002V7H17C18.1046 7 19 7.89543 19 9V15.0032ZM3 9H17V11H3V9ZM3 13V19H17V13H3Z" fill="currentColor" />
                                    </svg>
                                    <span className="activity-event__earnings-label">Frais annulation:</span>
                                    <span className="activity-event__earnings-value">+€{(event.order.cancellation_fee || 0).toFixed(2)}</span>
                                  </div>
                                )}
                                {(event.order.ride_price || 0) > 0 && (
                                  <div className="activity-event__earnings-item activity-event__earnings-item--gross">
                                    <span className="activity-event__earnings-label">Brut:</span>
                                    <span className="activity-event__earnings-value">€{((event.order.ride_price || 0) + (event.order.tip || 0)).toFixed(2)}</span>
                                  </div>
                                )}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Other tabs content */}
        {activeTab !== "Performance" && activeTab !== "Detailed activity" && (
          <div className="tab-content">
            <p>Content for {activeTab} tab will be implemented later.</p>
          </div>
        )}
      </div>
  );
}
