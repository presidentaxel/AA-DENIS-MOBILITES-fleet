import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/global.css";
import "./styles/sidebar.css";
import "./styles/drivers-page.css";
import "./styles/user-performance-drawer.css";
import "./styles/vehicles-page.css";
import "./styles/vehicle-performance-drawer.css";
import "./styles/analytics-page.css";
import "./styles/top-users-table.css";
import "./styles/no-earning-users-table.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

