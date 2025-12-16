import React, { useEffect, useState, useMemo, useRef } from "react";
import { RiSearchLine, RiArrowRightUpLine, RiArrowDownSLine } from "react-icons/ri";
import { getDrivers, getBoltDrivers } from "../api/fleetApi";
import { PlatformLogo } from "../components/PlatformLogo";
import { DriverDetailsDrawer } from "../components/DriverDetailsDrawer";
import "../styles/drivers-management-page.css";

type DriversManagementPageProps = {
  token: string;
};

export type CombinedDriver = {
  id: string;
  fullName: string;
  email: string;
  platforms: string[];
  connectedOn: string;
  status: "connected" | "disconnected";
  platformCount: number;
  phone?: string;
  countryPhoneCode?: string;
  boltId?: string; // ID Bolt spécifique pour la navigation vers la page de performance
  uberId?: string; // ID Uber pour référence
};

export function DriversManagementPage({ token }: DriversManagementPageProps) {
  const [uberDrivers, setUberDrivers] = useState<any[]>([]);
  const [boltDrivers, setBoltDrivers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [platformFilter, setPlatformFilter] = useState<string>("all");
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const [showPlatformMenu, setShowPlatformMenu] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(12);
  const [selectedDriver, setSelectedDriver] = useState<CombinedDriver | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const statusMenuRef = useRef<HTMLDivElement>(null);
  const platformMenuRef = useRef<HTMLDivElement>(null);

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
      } catch (err: any) {
        console.error("Erreur chargement drivers:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [token]);

  // Combiner et normaliser les drivers
  const combinedDrivers = useMemo<CombinedDriver[]>(() => {
    // Utiliser l'email comme clé pour combiner les drivers de différentes plateformes
    const driverMap = new Map<string, CombinedDriver>();

    // Traiter les drivers Bolt d'abord (pour prioriser l'ID Bolt comme ID principal)
    boltDrivers.forEach((driver) => {
      const email = driver.email || "";
      const fullName = `${driver.first_name || ""} ${driver.last_name || ""}`.trim();
      const boltDriverId = driver.id || "";
      
      if (!driverMap.has(email)) {
        const driverId = boltDriverId || email;
        driverMap.set(email, {
          id: driverId, // ID principal = ID Bolt si disponible
          fullName,
          email,
          platforms: [],
          connectedOn: driver.created_at || driver.connected_at || "",
          status: "connected",
          platformCount: 0,
          phone: driver.phone,
          countryPhoneCode: driver.country_phone_code || driver.country_phone_code,
          boltId: boltDriverId || undefined,
        });
      }
      
      const combined = driverMap.get(email)!;
      if (!combined.platforms.includes("bolt")) {
        combined.platforms.push("bolt");
        combined.platformCount++;
      }
      // Mettre à jour les infos si elles manquent
      if (!combined.phone && driver.phone) combined.phone = driver.phone;
      if (!combined.countryPhoneCode && (driver.country_phone_code || driver.country_phone_code)) {
        combined.countryPhoneCode = driver.country_phone_code || driver.country_phone_code;
      }
      // S'assurer que boltId et id sont à jour
      if (boltDriverId) {
        combined.boltId = boltDriverId;
        combined.id = boltDriverId; // Prioriser l'ID Bolt comme ID principal
      }
    });

    // Traiter les drivers Uber
    uberDrivers.forEach((driver) => {
      const email = driver.email || "";
      const fullName = `${driver.first_name || ""} ${driver.last_name || ""}`.trim();
      const uberDriverId = driver.uuid || driver.id || "";
      
      if (!driverMap.has(email)) {
        const driverId = uberDriverId || email;
        driverMap.set(email, {
          id: driverId, // ID principal = ID Uber si pas de driver Bolt avec cet email
          fullName,
          email,
          platforms: [],
          connectedOn: driver.created_at || driver.connected_at || "",
          status: "connected",
          platformCount: 0,
          phone: driver.phone,
          countryPhoneCode: driver.country_phone_code || driver.country_phone_code,
          uberId: uberDriverId || undefined,
        });
      }
      
      const combined = driverMap.get(email)!;
      if (!combined.platforms.includes("uber")) {
        combined.platforms.push("uber");
        combined.platformCount++;
      }
      // Mettre à jour les infos si elles manquent
      if (!combined.phone && driver.phone) combined.phone = driver.phone;
      if (!combined.countryPhoneCode && (driver.country_phone_code || driver.country_phone_code)) {
        combined.countryPhoneCode = driver.country_phone_code || driver.country_phone_code;
      }
      // Stocker l'ID Uber mais ne pas changer l'ID principal si on a déjà un ID Bolt
      if (uberDriverId) {
        combined.uberId = uberDriverId;
        // Ne pas écraser l'ID si on a déjà un boltId
        if (!combined.boltId && !combined.id) {
          combined.id = uberDriverId;
        }
      }
    });

    return Array.from(driverMap.values()).map((driver) => ({
      ...driver,
      status: driver.platformCount > 0 ? ("connected" as const) : ("disconnected" as const),
    }));
  }, [uberDrivers, boltDrivers]);

  // Filtrer les drivers
  const filtered = useMemo(() => {
    let filtered = combinedDrivers;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          d.fullName.toLowerCase().includes(query) ||
          d.email.toLowerCase().includes(query)
      );
    }

    if (statusFilter !== "all") {
      filtered = filtered.filter((d) => d.status === statusFilter);
    }

    if (platformFilter !== "all") {
      filtered = filtered.filter((d) => d.platforms.includes(platformFilter));
    }

    return filtered;
  }, [combinedDrivers, searchQuery, statusFilter, platformFilter]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedDrivers = filtered.slice(startIndex, endIndex);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, statusFilter, platformFilter]);

  // Fermer les menus au clic extérieur
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (statusMenuRef.current && !statusMenuRef.current.contains(event.target as Node)) {
        setShowStatusMenu(false);
      }
      if (platformMenuRef.current && !platformMenuRef.current.contains(event.target as Node)) {
        setShowPlatformMenu(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const formatDate = (dateString: string) => {
    if (!dateString) return "";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    } catch {
      return "";
    }
  };

  const handleStatusSelect = (value: string) => {
    setStatusFilter(value);
    setShowStatusMenu(false);
  };

  const handlePlatformSelect = (value: string) => {
    setPlatformFilter(value);
    setShowPlatformMenu(false);
  };

  const handleRowClick = (driver: CombinedDriver) => {
    setSelectedDriver(driver);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setSelectedDriver(null);
  };

  return (
    <div className="users-page">
      {/* Header */}
      <div className="header">
        <div className="header__title">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 22C2 19.8783 2.84285 17.8434 4.34315 16.3431C5.84344 14.8429 7.87827 14 10 14C12.1217 14 14.1566 14.8429 15.6569 16.3431C17.1571 17.8434 18 19.8783 18 22H2ZM10 13C6.685 13 4 10.315 4 7C4 3.685 6.685 1 10 1C13.315 1 16 3.685 16 7C16 10.315 13.315 13 10 13ZM17.363 15.233C18.8926 15.6261 20.2593 16.4918 21.2683 17.7068C22.2774 18.9218 22.8774 20.4242 22.983 22H20C20 19.39 19 17.014 17.363 15.233ZM15.34 12.957C16.178 12.2075 16.8482 11.2893 17.3066 10.2627C17.765 9.23616 18.0013 8.12429 18 7C18.0021 5.63347 17.6526 4.28937 16.985 3.097C18.1176 3.32459 19.1365 3.93737 19.8685 4.8312C20.6004 5.72502 21.0002 6.84473 21 8C21.0003 8.71247 20.8482 9.41676 20.5541 10.0657C20.26 10.7146 19.8305 11.2931 19.2946 11.7625C18.7586 12.2319 18.1285 12.5814 17.4464 12.7874C16.7644 12.9934 16.0462 13.0512 15.34 12.957Z" fill="#0061FF"/>
            <path d="M10 13C6.685 13 4 10.315 4 7C4 3.685 6.685 1 10 1C13.315 1 16 3.685 16 7C16 10.315 13.315 13 10 13Z" fill="#0093FD"/>
            <path d="M17.363 15.2361C18.8926 15.6292 20.2592 16.4949 21.2683 17.7099C22.2773 18.9249 22.8774 20.4273 22.983 22.0031H20C20 19.3931 19 17.0171 17.363 15.2361ZM15.34 12.9601C16.178 12.2106 16.8481 11.2924 17.3065 10.2658C17.7649 9.23925 18.0012 8.12739 18 7.0031C18.0021 5.63656 17.6526 4.29247 16.985 3.1001C18.1176 3.32769 19.1365 3.94047 19.8684 4.83429C20.6004 5.72812 21.0002 6.84782 21 8.0031C21.0002 8.71556 20.8482 9.41986 20.5541 10.0688C20.2599 10.7177 19.8305 11.2962 19.2945 11.7656C18.7585 12.235 18.1284 12.5845 17.4464 12.7905C16.7644 12.9965 16.0462 13.0543 15.34 12.9601Z" fill="#0093FD"/>
          </svg>
          <span>Users</span>
          <span className="header__title--total"></span>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="users__header">
        <div className="users__search-container users__search-container--multi">
          <div className="users__search-column">
            <div className="users__search-wrapper">
              <input
                type="text"
                className="users__search"
                placeholder="Search by name"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <i className="icon ri-search-line"></i>
            </div>
          </div>
          <div className="users__search-column">
            <div className="selector__wrapper" ref={statusMenuRef}>
          <div className="input selector">
            <input
              type="text"
              readOnly
              value={statusFilter === "all" ? "All" : statusFilter === "connected" ? "Connected" : "Disconnected"}
              onClick={() => setShowStatusMenu(!showStatusMenu)}
            />
            <i className="input__icon input__icon--right noselect ri-arrow-down-s-fill"></i>
            {showStatusMenu && (
              <div className="input-menu">
                <ul className="input-items">
                  <li className={statusFilter === "all" ? "active" : ""} onClick={() => handleStatusSelect("all")}>
                    All {statusFilter === "all" && (
                      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g clipPath="url(#clip0_6509_48691)">
                          <path d="M6.24996 9.48244L11.995 3.73682L12.8793 4.62057L6.24996 11.2499L2.27246 7.27244L3.15621 6.38869L6.24996 9.48244Z" fill="#8FB571"/>
                        </g>
                        <defs>
                          <clipPath id="clip0_6509_48691">
                            <rect width="15" height="15" fill="white"/>
                          </clipPath>
                        </defs>
                      </svg>
                    )}
                  </li>
                  <li className={statusFilter === "connected" ? "active" : ""} onClick={() => handleStatusSelect("connected")}>
                    Connected {statusFilter === "connected" && (
                      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g clipPath="url(#clip0_6509_48691)">
                          <path d="M6.24996 9.48244L11.995 3.73682L12.8793 4.62057L6.24996 11.2499L2.27246 7.27244L3.15621 6.38869L6.24996 9.48244Z" fill="#8FB571"/>
                        </g>
                        <defs>
                          <clipPath id="clip0_6509_48691">
                            <rect width="15" height="15" fill="white"/>
                          </clipPath>
                        </defs>
                      </svg>
                    )}
                  </li>
                  <li className={statusFilter === "disconnected" ? "active" : ""} onClick={() => handleStatusSelect("disconnected")}>
                    Disconnected {statusFilter === "disconnected" && (
                      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g clipPath="url(#clip0_6509_48691)">
                          <path d="M6.24996 9.48244L11.995 3.73682L12.8793 4.62057L6.24996 11.2499L2.27246 7.27244L3.15621 6.38869L6.24996 9.48244Z" fill="#8FB571"/>
                        </g>
                        <defs>
                          <clipPath id="clip0_6509_48691">
                            <rect width="15" height="15" fill="white"/>
                          </clipPath>
                        </defs>
                      </svg>
                    )}
                  </li>
                </ul>
              </div>
            )}
            </div>
          </div>
          </div>
          <div className="users__search-column">
            <div className="selector__wrapper" ref={platformMenuRef}>
          <div className="input selector selector--platforms">
            <input
              type="text"
              readOnly
              value={platformFilter === "all" ? "All" : platformFilter.charAt(0).toUpperCase() + platformFilter.slice(1) + " Fleet"}
              onClick={() => setShowPlatformMenu(!showPlatformMenu)}
            />
            <i className="input__icon input__icon--right noselect ri-arrow-down-s-fill"></i>
            {showPlatformMenu && (
              <div className="input-menu">
                <ul className="input-items">
                  <li className={platformFilter === "all" ? "active" : ""} onClick={() => handlePlatformSelect("all")}>
                    All {platformFilter === "all" && (
                      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g clipPath="url(#clip0_6509_48691)">
                          <path d="M6.24996 9.48244L11.995 3.73682L12.8793 4.62057L6.24996 11.2499L2.27246 7.27244L3.15621 6.38869L6.24996 9.48244Z" fill="#8FB571"/>
                        </g>
                        <defs>
                          <clipPath id="clip0_6509_48691">
                            <rect width="15" height="15" fill="white"/>
                          </clipPath>
                        </defs>
                      </svg>
                    )}
                  </li>
                  <li className={platformFilter === "uber" ? "active" : ""} onClick={() => handlePlatformSelect("uber")}>
                    Uber Fleet {platformFilter === "uber" && (
                      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g clipPath="url(#clip0_6509_48691)">
                          <path d="M6.24996 9.48244L11.995 3.73682L12.8793 4.62057L6.24996 11.2499L2.27246 7.27244L3.15621 6.38869L6.24996 9.48244Z" fill="#8FB571"/>
                        </g>
                        <defs>
                          <clipPath id="clip0_6509_48691">
                            <rect width="15" height="15" fill="white"/>
                          </clipPath>
                        </defs>
                      </svg>
                    )}
                  </li>
                  <li className={platformFilter === "bolt" ? "active" : ""} onClick={() => handlePlatformSelect("bolt")}>
                    Bolt Fleet {platformFilter === "bolt" && (
                      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g clipPath="url(#clip0_6509_48691)">
                          <path d="M6.24996 9.48244L11.995 3.73682L12.8793 4.62057L6.24996 11.2499L2.27246 7.27244L3.15621 6.38869L6.24996 9.48244Z" fill="#8FB571"/>
                        </g>
                        <defs>
                          <clipPath id="clip0_6509_48691">
                            <rect width="15" height="15" fill="white"/>
                          </clipPath>
                        </defs>
                      </svg>
                    )}
                  </li>
                  <li className={platformFilter === "heetch" ? "active" : ""} onClick={() => handlePlatformSelect("heetch")}>
                    Heetch Fleet {platformFilter === "heetch" && (
                      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g clipPath="url(#clip0_6509_48691)">
                          <path d="M6.24996 9.48244L11.995 3.73682L12.8793 4.62057L6.24996 11.2499L2.27246 7.27244L3.15621 6.38869L6.24996 9.48244Z" fill="#8FB571"/>
                        </g>
                        <defs>
                          <clipPath id="clip0_6509_48691">
                            <rect width="15" height="15" fill="white"/>
                          </clipPath>
                        </defs>
                      </svg>
                    )}
                  </li>
                </ul>
              </div>
            )}
            </div>
          </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="users__table">
        <table className="table" cellSpacing="0">
          <thead>
            <tr>
              <th style={{ width: "30px" }}></th>
              <th style={{ width: "300px" }}>Full Name</th>
              <th style={{ width: "140px" }}>Platforms</th>
              <th style={{ width: "200px" }}>Email</th>
              <th style={{ width: "130px" }}>Connected On</th>
              <th style={{ width: "160px" }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ textAlign: "center", padding: "2rem" }}>
                  Loading...
                </td>
              </tr>
            ) : paginatedDrivers.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: "center", padding: "2rem" }}>
                  No drivers found
                </td>
              </tr>
            ) : (
              paginatedDrivers.map((driver) => (
                <tr key={driver.id} className="click-row" onClick={() => handleRowClick(driver)}>
                  <td style={{ width: "40px" }} className="table__arrow">
                    <i className="ri-arrow-right-up-line"></i>
                  </td>
                  <td>{driver.fullName}</td>
                  <td style={{ width: "160px" }}>
                    <div className="table__platforms">
                      {driver.platforms.map((platform) => (
                        <div key={platform} className="table__platform">
                          <PlatformLogo platform={platform} size={32} />
                        </div>
                      ))}
                    </div>
                  </td>
                  <td>{driver.email || "—"}</td>
                  <td>{formatDate(driver.connectedOn) || "—"}</td>
                  <td style={{ width: "160px" }}>
                    <div className="table__status">
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 20 20"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                        className="status-icon--success"
                      >
                        <path
                          d="M10.0001 18.3332C5.39758 18.3332 1.66675 14.6023 1.66675 9.99984C1.66675 5.39734 5.39758 1.6665 10.0001 1.6665C14.6026 1.6665 18.3334 5.39734 18.3334 9.99984C18.3334 14.6023 14.6026 18.3332 10.0001 18.3332ZM10.0001 16.6665C11.7682 16.6665 13.4639 15.9641 14.7141 14.7139C15.9644 13.4636 16.6667 11.7679 16.6667 9.99984C16.6667 8.23173 15.9644 6.53604 14.7141 5.28579C13.4639 4.03555 11.7682 3.33317 10.0001 3.33317C8.23197 3.33317 6.53628 4.03555 5.28604 5.28579C4.03579 6.53604 3.33341 8.23173 3.33341 9.99984C3.33341 11.7679 4.03579 13.4636 5.28604 14.7139C6.53628 15.9641 8.23197 16.6665 10.0001 16.6665ZM9.16925 13.3332L5.63341 9.79734L6.81175 8.619L9.16925 10.9765L13.8826 6.26234L15.0617 7.44067L9.16925 13.3332Z"
                          fill="currentColor"
                        />
                      </svg>
                      <p>connected</p>
                      <p className="count">{driver.platformCount}</p>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="users__pagination">
          <div className="pagination">
            <div className="pagination__controls">
              <button
                className="pagination__btn pagination__btn--prev"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              >
                <svg width="32" height="32" viewBox="10 10 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ transform: 'rotate(90deg)' }}>
                  <mask id="path-1-inside-1_15102_58310_prev" fill="white">
                    <path d="M0 0H52V52H0V0Z"></path>
                  </mask>
                  <path d="M0 0H52V52H0V0Z" fill="transparent"></path>
                  <path d="M52 51H0V53H52V51Z" fill="#EDF2F8" mask="url(#path-1-inside-1_15102_58310_prev)"></path>
                  <g clipPath="url(#clip0_15102_58310_prev)">
                    <path
                      d="M26.9766 26.0001L22.8516 21.8751L24.0299 20.6968L29.3332 26.0001L24.0299 31.3034L22.8516 30.1251L26.9766 26.0001Z"
                      fill="#A8AFBC"
                    />
                  </g>
                  <defs>
                    <clipPath id="clip0_15102_58310_prev">
                      <rect width="20" height="20" fill="white" transform="translate(16 16)"></rect>
                    </clipPath>
                  </defs>
                </svg>
              </button>
              <div className="pagination__pages">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    className={`pagination__page ${currentPage === page ? "pagination__page--active" : ""}`}
                    onClick={() => setCurrentPage(page)}
                  >
                    {page}
                  </button>
                ))}
              </div>
              <button
                className="pagination__btn pagination__btn--next"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              >
                <svg width="32" height="32" viewBox="10 10 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ transform: 'rotate(-90deg)' }}>
                  <mask id="path-1-inside-1_15102_58310_next" fill="white">
                    <path d="M0 0H52V52H0V0Z"></path>
                  </mask>
                  <path d="M0 0H52V52H0V0Z" fill="transparent"></path>
                  <path d="M52 51H0V53H52V51Z" fill="#EDF2F8" mask="url(#path-1-inside-1_15102_58310_next)"></path>
                  <g clipPath="url(#clip0_15102_58310_next)">
                    <path
                      d="M26.9766 26.0001L22.8516 21.8751L24.0299 20.6968L29.3332 26.0001L24.0299 31.3034L22.8516 30.1251L26.9766 26.0001Z"
                      fill="#A8AFBC"
                    />
                  </g>
                  <defs>
                    <clipPath id="clip0_15102_58310_next">
                      <rect width="20" height="20" fill="white" transform="translate(16 16)"></rect>
                    </clipPath>
                  </defs>
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Driver Details Drawer */}
      {selectedDriver && (
        <DriverDetailsDrawer
          driver={selectedDriver}
          isOpen={drawerOpen}
          onClose={handleCloseDrawer}
          token={token}
        />
      )}
    </div>
  );
}

