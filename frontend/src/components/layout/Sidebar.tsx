import React from "react";
import { useNavigate, useLocation } from "react-router-dom";

type MenuItem = {
  id: string;
  label: string;
  icon: string;
  path: string;
  children?: MenuItem[];
};

const menuItems: MenuItem[] = [
  { id: "overview", label: "Overview", icon: "📊", path: "/" },
  { id: "drivers", label: "Chauffeurs", icon: "👥", path: "/drivers" },
  { id: "vehicles", label: "Véhicules", icon: "🚗", path: "/vehicles" },
  { id: "orders", label: "Commandes", icon: "📦", path: "/orders" },
  { id: "analytics", label: "Analytics", icon: "📈", path: "/analytics" },
  { id: "settings", label: "Paramètres", icon: "⚙️", path: "/settings" },
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

  return (
    <div style={{
      width: "260px",
      backgroundColor: "#1e293b",
      color: "#f8fafc",
      height: "100vh",
      position: "fixed",
      left: 0,
      top: 0,
      display: "flex",
      flexDirection: "column",
      padding: "1.5rem",
      boxShadow: "2px 0 8px rgba(0,0,0,0.1)",
    }}>
      {/* Logo */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        marginBottom: "2rem",
        paddingBottom: "1.5rem",
        borderBottom: "1px solid rgba(255,255,255,0.1)",
      }}>
        <div style={{
          width: "32px",
          height: "32px",
          borderRadius: "8px",
          background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontSize: "1.25rem",
          fontWeight: "bold",
        }}>
          AA
        </div>
        <span style={{ fontSize: "1.25rem", fontWeight: "600" }}>AA Denis Fleet</span>
      </div>

      {/* Organization */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.75rem",
        borderRadius: "8px",
        backgroundColor: "rgba(255,255,255,0.05)",
        marginBottom: "1.5rem",
        cursor: "pointer",
      }}>
        <span style={{ fontSize: "1.25rem" }}>🏠</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "0.875rem", fontWeight: "500" }}>AA Denis Mobilités</div>
          <div style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.6)" }}>Organisation</div>
        </div>
        <span style={{ fontSize: "0.75rem" }}>▼</span>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1 }}>
        {menuItems.map((item) => (
          <div
            key={item.id}
            onClick={() => navigate(item.path)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              padding: "0.75rem",
              borderRadius: "8px",
              marginBottom: "0.5rem",
              cursor: "pointer",
              backgroundColor: isActive(item.path) ? "rgba(59, 130, 246, 0.2)" : "transparent",
              borderLeft: isActive(item.path) ? "3px solid #3b82f6" : "3px solid transparent",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              if (!isActive(item.path)) {
                e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.05)";
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive(item.path)) {
                e.currentTarget.style.backgroundColor = "transparent";
              }
            }}
          >
            <span style={{ fontSize: "1.25rem" }}>{item.icon}</span>
            <span style={{
              fontSize: "0.875rem",
              fontWeight: isActive(item.path) ? "600" : "400",
              color: isActive(item.path) ? "#fff" : "rgba(255,255,255,0.8)",
            }}>
              {item.label}
            </span>
          </div>
        ))}
      </nav>

      {/* Logout */}
      <div
        onClick={onLogout}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          padding: "0.75rem",
          borderRadius: "8px",
          cursor: "pointer",
          color: "rgba(255,255,255,0.7)",
          marginTop: "auto",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.2)";
          e.currentTarget.style.color = "#fff";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = "transparent";
          e.currentTarget.style.color = "rgba(255,255,255,0.7)";
        }}
      >
        <span style={{ fontSize: "1.25rem" }}>🚪</span>
        <span style={{ fontSize: "0.875rem" }}>Déconnexion</span>
      </div>
    </div>
  );
}

