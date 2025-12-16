import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { FiLayout, FiUsers, FiTruck, FiPackage, FiTrendingUp, FiSettings, FiChevronDown, FiChevronRight } from "react-icons/fi";
import { HiHome } from "react-icons/hi";
import { FiLogOut } from "react-icons/fi";

type MenuItem = {
  id: string;
  label: string;
  icon?: React.ReactNode;
  path: string;
  children?: Omit<MenuItem, "icon">[];
};

const menuItems: MenuItem[] = [
  { id: "overview", label: "Overview", icon: <FiLayout />, path: "/" },
  {
    id: "drivers",
    label: "Chauffeurs",
    icon: <FiUsers />,
    path: "/drivers",
    children: [
      { id: "drivers-management", label: "Gestion", path: "/drivers" },
      { id: "drivers-data", label: "Data", path: "/drivers/data" },
    ],
  },
  { id: "vehicles", label: "Véhicules", icon: <FiTruck />, path: "/vehicles" },
  { id: "orders", label: "Commandes", icon: <FiPackage />, path: "/orders" },
  { id: "analytics", label: "Analytics", icon: <FiTrendingUp />, path: "/analytics" },
  { id: "settings", label: "Paramètres", icon: <FiSettings />, path: "/settings" },
];

type SidebarProps = {
  onLogout: () => void;
};

export function Sidebar({ onLogout }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  // Ouvrir automatiquement les menus dont un enfant est actif
  const getInitialOpenMenus = () => {
    const open = new Set<string>();
    menuItems.forEach((item) => {
      if (item.children && item.children.some((child) => isActive(child.path))) {
        open.add(item.id);
      }
    });
    return open;
  };

  const [openMenus, setOpenMenus] = useState<Set<string>>(getInitialOpenMenus);

  // Mettre à jour les menus ouverts quand la route change
  useEffect(() => {
    setOpenMenus(getInitialOpenMenus());
  }, [location.pathname]);

  const toggleMenu = (menuId: string) => {
    setOpenMenus((prev) => {
      const next = new Set(prev);
      if (next.has(menuId)) {
        next.delete(menuId);
      } else {
        next.add(menuId);
      }
      return next;
    });
  };

  const handleMenuItemClick = (item: MenuItem, e: React.MouseEvent) => {
    if (item.children) {
      e.stopPropagation();
      toggleMenu(item.id);
    } else {
      navigate(item.path);
    }
  };

  const handleChildClick = (childPath: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(childPath);
  };

  return (
    <div className="sidebar-container">
      {/* Logo */}
      <div className="sidebar-logo">
          <img src="/favicon.svg" alt="Logo axel" />
      </div>

      {/* Organization */}
      <div className="sidebar-org">
        <HiHome className="sidebar-org__icon" />
        <div className="sidebar-org__content">
          <div className="sidebar-org__name">AA Denis Mobilités</div>
          <div className="sidebar-org__type">Organisation</div>
        </div>
        <FiChevronDown className="sidebar-org__chevron" />
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const hasChildren = item.children && item.children.length > 0;
          const isOpen = openMenus.has(item.id);
          const isItemActive = isActive(item.path) || (hasChildren && item.children?.some((child) => isActive(child.path)));

          return (
            <div key={item.id}>
              <div
                onClick={(e) => handleMenuItemClick(item, e)}
                className={`sidebar-nav__item ${isItemActive ? "sidebar-nav__item--active" : ""}`}
              >
                <span className="sidebar-nav__icon">{item.icon}</span>
                <span className="sidebar-nav__label">{item.label}</span>
                {hasChildren && (
                  <span className="sidebar-nav__chevron">
                    {isOpen ? <FiChevronDown size={16} /> : <FiChevronRight size={16} />}
                  </span>
                )}
              </div>
              {hasChildren && isOpen && (
                <div className="sidebar-nav__children">
                  {item.children?.map((child) => (
                    <div
                      key={child.id}
                      onClick={(e) => handleChildClick(child.path, e)}
                      className={`sidebar-nav__child ${isActive(child.path) ? "sidebar-nav__child--active" : ""}`}
                    >
                      <span className="sidebar-nav__child-label">{child.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>
    </div>
  );
}
