import React from "react";
import { Sidebar } from "./Sidebar";

type MainLayoutProps = {
  children: React.ReactNode;
  onLogout: () => void;
};

export function MainLayout({ children, onLogout }: MainLayoutProps) {
  return (
    <div style={{ display: "flex", minHeight: "100vh", backgroundColor: "#f8fafc" }}>
      <Sidebar onLogout={onLogout} />
      <main style={{
        marginLeft: "260px",
        flex: 1,
        padding: "2rem",
        minHeight: "100vh",
      }}>
        {children}
      </main>
    </div>
  );
}

