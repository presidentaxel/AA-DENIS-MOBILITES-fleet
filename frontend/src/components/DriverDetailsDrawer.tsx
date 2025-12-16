import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { RiCloseLine, RiArrowRightUpLine, RiPieChart2Line } from "react-icons/ri";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from "recharts";
import { PlatformLogo } from "./PlatformLogo";
import { calculatePerformanceScores } from "../utils/performanceCalculator";
import { getBoltOrders } from "../api/fleetApi";
import "../styles/driver-details-drawer.css";

type DriverDetailsDrawerProps = {
  driver: CombinedDriver;
  isOpen: boolean;
  onClose: () => void;
  token: string;
};

import { CombinedDriver } from "../pages/DriversManagementPage";

export function DriverDetailsDrawer({ driver, isOpen, onClose, token }: DriverDetailsDrawerProps) {
  const navigate = useNavigate();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [periodFilter, setPeriodFilter] = useState("Current Year");
  const [showPeriodMenu, setShowPeriodMenu] = useState(false);
  const periodMenuRef = React.useRef<HTMLDivElement>(null);

  // Calculer les dates selon la période
  const dateRange = useMemo(() => {
    const now = new Date();
    const currentYear = now.getFullYear();
    
    switch (periodFilter) {
      case "Last 2 Weeks":
        return {
          from: new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
          to: now.toISOString().slice(0, 10),
        };
      case "Last Month":
        return {
          from: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
          to: now.toISOString().slice(0, 10),
        };
      case "Last 3 Months":
        return {
          from: new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
          to: now.toISOString().slice(0, 10),
        };
      case "Last Year":
        return {
          from: new Date(currentYear - 1, 0, 1).toISOString().slice(0, 10),
          to: new Date(currentYear - 1, 11, 31).toISOString().slice(0, 10),
        };
      case "Last 2 Years":
        return {
          from: new Date(currentYear - 2, 0, 1).toISOString().slice(0, 10),
          to: now.toISOString().slice(0, 10),
        };
      case "Current Year":
      default:
        return {
          from: new Date(currentYear, 0, 1).toISOString().slice(0, 10),
          to: now.toISOString().slice(0, 10),
        };
    }
  }, [periodFilter]);

  useEffect(() => {
    if (isOpen && driver) {
      async function fetchOrders() {
        setLoading(true);
        try {
          // Récupérer les orders pour toutes les plateformes du driver
          const allOrders: any[] = [];
          
          if (driver.platforms.includes("bolt")) {
            try {
              const boltOrders = await getBoltOrders(token, dateRange.from, dateRange.to, driver.id);
              allOrders.push(...(Array.isArray(boltOrders) ? boltOrders : []));
            } catch (err) {
              console.error("Error fetching Bolt orders:", err);
            }
          }
          
          setOrders(allOrders);
        } catch (err) {
          console.error("Error fetching orders:", err);
        } finally {
          setLoading(false);
        }
      }
      fetchOrders();
    }
  }, [isOpen, driver, token, dateRange]);

  // Fermer le menu au clic extérieur
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (periodMenuRef.current && !periodMenuRef.current.contains(event.target as Node)) {
        setShowPeriodMenu(false);
      }
    }
    if (showPeriodMenu) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showPeriodMenu]);

  // Calculer les stats depuis les orders
  const stats = useMemo(() => {
    const driverOrders = orders.filter((o: any) => o.driver_uuid === driver.id || o.driver_id === driver.id);
    
    const grossEarnings = driverOrders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
    const netEarnings = driverOrders.reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
    const tips = driverOrders.reduce((sum: number, o: any) => sum + (o.tip || 0), 0);
    const fare = driverOrders.reduce((sum: number, o: any) => sum + (o.ride_price || 0), 0);
    const cashEarnings = driverOrders
      .filter((o: any) => o.payment_method === "cash")
      .reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
    const cardEarnings = driverOrders
      .filter((o: any) => o.payment_method !== "cash")
      .reduce((sum: number, o: any) => sum + (o.net_earnings || 0), 0);
    
    const totalTrips = driverOrders.length;
    
    // Calculer l'heure la plus active
    const hourCounts: Record<number, number> = {};
    driverOrders.forEach((o: any) => {
      // Use order_finished_timestamp for time-based calculations
      const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
      if (orderTs) {
        const date = new Date(orderTs * 1000);
        const hour = date.getHours();
        hourCounts[hour] = (hourCounts[hour] || 0) + 1;
      }
    });
    
    let mostActiveHour = "Afternoon";
    if (Object.keys(hourCounts).length > 0) {
      const maxHour = Object.keys(hourCounts).reduce((a, b) => 
        hourCounts[parseInt(a)] > hourCounts[parseInt(b)] ? a : b
      );
      const hour = parseInt(maxHour);
      if (hour >= 6 && hour < 12) mostActiveHour = "Morning";
      else if (hour >= 12 && hour < 18) mostActiveHour = "Afternoon";
      else if (hour >= 18 && hour < 22) mostActiveHour = "Evening";
      else mostActiveHour = "Night";
    }
    
    return {
      grossEarnings,
      netEarnings,
      tips,
      fare,
      cashEarnings,
      cardEarnings,
      totalTrips,
      mostActiveHour,
    };
  }, [orders, driver]);

  // Calculer les scores de performance
  const performanceScores = useMemo(() => {
    return calculatePerformanceScores(orders, driver.id);
  }, [orders, driver.id]);

  // Préparer les données pour le graphique radar
  const radarData = useMemo(() => {
    return [
      {
        subject: "Income Score",
        score: performanceScores.incomeScore,
        fullMark: 100,
      },
      {
        subject: "Working Stability Score",
        score: performanceScores.workingSustainabilityScore,
        fullMark: 100,
      },
      {
        subject: "Working Efficiency Score",
        score: performanceScores.workingEfficiencyScore,
        fullMark: 100,
      },
    ];
  }, [performanceScores]);

  if (!isOpen || !driver) return null;

  const formatDate = (dateString: string) => {
    if (!dateString) return "";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    } catch {
      return "";
    }
  };

  return (
    <>
      {isOpen && <div className="user-drawer__overlay" onClick={onClose}></div>}
      <div className="user-drawer" style={{ transform: isOpen ? "translateX(0%)" : "translateX(100%)", opacity: isOpen ? 1 : 0 }}>
        <div className="header">
        <div className="header__title">
          <h3>{driver.fullName}</h3>
          <p>
            <span className="circle circle--green"></span>
            <span className="status status--green">Connected</span>
          </p>
        </div>
        <div className="header__close" onClick={onClose}>
          <i className="ri-close-line"></i>
        </div>
      </div>

      <div className="content">
        {/* Scores Section */}
        <div className="content__graph">
          <div className="graph">
            <div className="header__item">
              <h4 className="header__title">Income Score</h4>
              <p>
                <span>{performanceScores.incomeScore}</span> of 100
              </p>
            </div>
            <div className="header__item">
              <h4 className="header__title">Working Efficiency Score</h4>
              <p>
                <span>{performanceScores.workingEfficiencyScore}</span> of 100
              </p>
            </div>
            <div className="header__item">
              <h4 className="header__title">Working Sustainability Score</h4>
              <p>
                <span>{performanceScores.workingSustainabilityScore}</span> of 100
              </p>
            </div>
            <div className="header__item">
              <svg width="32" height="32" viewBox="10 10 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className="header__icon">
                <mask id="path-1-inside-1_15102_58310" fill="white">
                  <path d="M0 0H52V52H0V0Z"></path>
                </mask>
                <path d="M0 0H52V52H0V0Z" fill="transparent"></path>
                <path d="M52 51H0V53H52V51Z" fill="#EDF2F8" mask="url(#path-1-inside-1_15102_58310)"></path>
                <g clipPath="url(#clip0_15102_58310)">
                  <path
                    d="M26.9766 26.0001L22.8516 21.8751L24.0299 20.6968L29.3332 26.0001L24.0299 31.3034L22.8516 30.1251L26.9766 26.0001Z"
                    fill="#A8AFBC"
                  />
                </g>
                <defs>
                  <clipPath id="clip0_15102_58310">
                    <rect width="20" height="20" fill="white" transform="translate(16 16)"></rect>
                  </clipPath>
                </defs>
              </svg>
            </div>
          </div>
          <div className="line"></div>
          <div className="graph">
            <div className="header__item">
              <h4 className="header__title">Overall Performance Score</h4>
              <p>
                <span>{performanceScores.overallPerformanceScore}</span> of 100
              </p>
            </div>
          </div>
        </div>

        {/* Radar Chart */}
        <div className="graph__radar">
          <ResponsiveContainer width="100%" height={194}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e8e8e8" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fontSize: 11, fill: "#253858", fontFamily: "'Nunito Sans', sans-serif" }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: "#7a808b", fontFamily: "'Nunito Sans', sans-serif" }}
                ticks={[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]}
              />
              <Radar
                name="Performance"
                dataKey="score"
                stroke="#0061ff"
                fill="#0061ff"
                fillOpacity={0.2}
                strokeWidth={2}
                dot={{ fill: "#0061ff", r: 6, strokeWidth: 2, stroke: "#ffffff" }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="graph__desc">
          <p>Last 90 days</p>
        </div>
        <div className="graph__tooltip">
          <div className="tooltip-container">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <g clipPath="url(#clip0_4763_43310)">
                <path
                  d="M8.00004 14.6666C4.31804 14.6666 1.33337 11.682 1.33337 7.99998C1.33337 4.31798 4.31804 1.33331 8.00004 1.33331C11.682 1.33331 14.6667 4.31798 14.6667 7.99998C14.6667 11.682 11.682 14.6666 8.00004 14.6666ZM7.33337 7.33331V11.3333H8.66671V7.33331H7.33337ZM7.33337 4.66665V5.99998H8.66671V4.66665H7.33337Z"
                  fill="#A8AFBC"
                />
              </g>
              <defs>
                <clipPath id="clip0_4763_43310">
                  <rect width="16" height="16" fill="white"></rect>
                </clipPath>
              </defs>
            </svg>
          </div>
        </div>

        {/* Data Sources */}
        <div className="content__datasources">
          <nav className="nav-toolbar">
            <ul className="nav-list">
              {driver.platforms.map((platform) => (
                <li key={platform}>
                  <div className="nav-item active">
                    <PlatformLogo platform={platform} size={24} />
                    <h5 className="nav-title">{platform.charAt(0).toUpperCase() + platform.slice(1)}</h5>
                    <p className="nav-subtitle">from {formatDate(driver.connectedOn)}</p>
                  </div>
                </li>
              ))}
            </ul>
          </nav>
          <div className="selector__wrapper" ref={periodMenuRef}>
            <div className="input selector" company="true" icon="false">
              <input
                type="text"
                readOnly
                value={periodFilter}
                onClick={() => setShowPeriodMenu(!showPeriodMenu)}
              />
              <i className="input__icon input__icon--right noselect ri-arrow-down-s-fill"></i>
              {showPeriodMenu && (
                <div className="input-menu">
                  <ul className="input-items">
                    {["Last 2 Weeks", "Last Month", "Last 3 Months", "Last Year", "Last 2 Years", "Current Year"].map((period) => (
                      <li
                        key={period}
                        className={periodFilter === period ? "active" : ""}
                        onClick={() => {
                          setPeriodFilter(period);
                          setShowPeriodMenu(false);
                        }}
                      >
                        {period}
                        {periodFilter === period && (
                          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <g clipPath="url(#clip0_6509_48691)">
                              <path
                                d="M6.24996 9.48244L11.995 3.73682L12.8793 4.62057L6.24996 11.2499L2.27246 7.27244L3.15621 6.38869L6.24996 9.48244Z"
                                fill="#8FB571"
                              />
                            </g>
                            <defs>
                              <clipPath id="clip0_6509_48691">
                                <rect width="15" height="15" fill="white" />
                              </clipPath>
                            </defs>
                          </svg>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="line"></div>

        {/* Profile Section */}
        <div className="content__section">
          <div className="section__title">
            <h4>Profile</h4>
          </div>
          <table cellPadding="0" cellSpacing="0">
            <tbody>
              <tr>
                <td>Full Name</td>
                <td>{driver.fullName}</td>
              </tr>
              {driver.phone && (
                <tr>
                  <td>Phone</td>
                  <td>{driver.phone}</td>
                </tr>
              )}
              {driver.email && (
                <tr>
                  <td>Email</td>
                  <td>{driver.email}</td>
                </tr>
              )}
              {driver.countryPhoneCode && (
                <tr>
                  <td>Country Phone Code</td>
                  <td>{driver.countryPhoneCode}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Income Section */}
        <div className="content__section">
          <div className="line"></div>
          <div className="section__title">
            <h4>Income</h4>
            <div className="section__selector"></div>
          </div>
          <table cellPadding="0" cellSpacing="0">
            <tbody>
              <tr>
                <td>Gross Earnings</td>
                <td>
                  <span className="grey">€</span> {stats.grossEarnings.toFixed(2)}
                </td>
              </tr>
              <tr>
                <td>Net Earnings</td>
                <td>
                  <span className="grey">€</span> {stats.netEarnings.toFixed(2)}
                </td>
              </tr>
              <tr>
                <td>Bonuses</td>
                <td>
                  <span className="grey">€</span> 0.00
                </td>
              </tr>
              <tr>
                <td>Tips</td>
                <td>
                  <span className="grey">€</span> {stats.tips.toFixed(2)}
                </td>
              </tr>
              <tr>
                <td>Fare</td>
                <td>
                  <span className="grey">€</span> {stats.fare.toFixed(2)}
                </td>
              </tr>
              <tr>
                <td>Cash Earnings</td>
                <td>
                  <span className="grey">€</span> {stats.cashEarnings.toFixed(2)}
                </td>
              </tr>
              <tr>
                <td>Card Earnings</td>
                <td>
                  <span className="grey">€</span> {stats.cardEarnings.toFixed(2)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Activity Section */}
        <div className="content__section">
          <div className="line"></div>
          <div className="section__title">
            <h4>Activity</h4>
          </div>
          <table cellPadding="0" cellSpacing="0">
            <tbody>
              <tr>
                <td>Total Trips</td>
                <td>{stats.totalTrips}</td>
              </tr>
              <tr>
                <td>Hours Most Active</td>
                <td>{stats.mostActiveHour}</td>
              </tr>
              <tr>
                <td>Currency Sign</td>
                <td>€</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer */}
      <div className="footer">
        <div className="cta">
          <button
            className="button button--primary w-full"
            onClick={() => {
              // Utiliser boltId si disponible (pour la navigation vers la page de performance Bolt)
              // Sinon utiliser l'ID principal
              const driverIdToUse = driver.boltId || driver.id;
              navigate(`/drivers/performance/${driverIdToUse}`);
            }}
          >
            Performance Index <i className="ri-arrow-right-up-line after"></i>
          </button>
        </div>
        </div>
      </div>
    </>
  );
}

