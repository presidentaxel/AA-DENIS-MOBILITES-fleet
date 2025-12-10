import { useEffect, useMemo, useState } from "react";
import { DriverTable } from "./components/DriverTable";
import { DriverDetail } from "./components/DriverDetail";
import { MetricsCards } from "./components/MetricsCards";
import { PaymentList } from "./components/PaymentList";
import {
  getDrivers,
  getDriverMetrics,
  getDriverPayments,
  getBoltDrivers,
  getBoltDriver,
  getBoltTrips,
  getBoltEarnings,
  getMe,
} from "./api/fleetApi";
import Login from "./pages/Login";

type Driver = { uuid?: string; name?: string; email?: string };
type BoltDriver = { id?: string; first_name?: string; last_name?: string; email?: string; phone?: string };

export default function App() {
  // Récupérer le token depuis localStorage au démarrage
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem("auth_token");
  });
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [boltDrivers, setBoltDrivers] = useState<BoltDriver[]>([]);
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null);
  const [selectedBoltDriver, setSelectedBoltDriver] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [trips, setTrips] = useState<any[]>([]);
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().slice(0, 10);
  });
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(!navigator.onLine);
  const [provider, setProvider] = useState<"uber" | "bolt">("uber");

  useEffect(() => {
    const handler = () => setOffline(!navigator.onLine);
    window.addEventListener("online", handler);
    window.addEventListener("offline", handler);
    return () => {
      window.removeEventListener("online", handler);
      window.removeEventListener("offline", handler);
    };
  }, []);

  useEffect(() => {
    async function fetchDrivers() {
      if (!token) return;
      setLoading(true);
      try {
        if (provider === "uber") {
          const data = await getDrivers(token, { limit, offset });
          setDrivers(data);
          if (data.length) setSelectedDriver(data[0].uuid);
        } else {
          const data = await getBoltDrivers(token, { limit, offset });
          setBoltDrivers(data);
          if (data.length) setSelectedBoltDriver(data[0].id || null);
        }
        setError(null);
      } catch (err: any) {
        const errorMsg = err?.response?.data?.detail || err?.message || "Erreur chargement chauffeurs";
        setError(errorMsg);
        console.error("Erreur fetchDrivers:", err);
        // Si erreur 401, déconnecter
        if (err?.response?.status === 401) {
          handleLogout();
        }
      } finally {
        setLoading(false);
      }
    }
    fetchDrivers();
  }, [token, limit, offset, provider]);

  useEffect(() => {
    async function fetchDetails() {
      if (!token) return;
      setLoading(true);
      try {
        if (provider === "uber" && selectedDriver) {
          const metricsRes = await getDriverMetrics(token, selectedDriver, dateFrom, dateTo);
          const paymentsRes = await getDriverPayments(token, selectedDriver, dateFrom, dateTo);
          setMetrics(metricsRes);
          setPayments(paymentsRes);
          setTrips([]);
        }
        if (provider === "bolt" && selectedBoltDriver) {
          const metricsRes = await getBoltTrips(token, selectedBoltDriver, dateFrom, dateTo);
          const paymentsRes = await getBoltEarnings(token, selectedBoltDriver, dateFrom, dateTo);
          setMetrics([]);
          setTrips(metricsRes);
          setPayments(paymentsRes);
        }
        setError(null);
      } catch (err: any) {
        const errorMsg = err?.response?.data?.detail || err?.message || "Erreur chargement métriques/paiements";
        setError(errorMsg);
        console.error("Erreur fetchDetails:", err);
        // Si erreur 401, déconnecter
        if (err?.response?.status === 401) {
          handleLogout();
        }
      } finally {
        setLoading(false);
      }
    }
    fetchDetails();
  }, [token, selectedDriver, selectedBoltDriver, dateFrom, dateTo, provider]);

  const selectedDriverObj = useMemo(() => drivers.find((d) => d.uuid === selectedDriver), [drivers, selectedDriver]);
  const selectedBoltDriverObj = useMemo(
    () => boltDrivers.find((d) => d.id === selectedBoltDriver),
    [boltDrivers, selectedBoltDriver]
  );

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    setToken(null);
  };

  const copyToken = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      alert("Token copié dans le presse-papiers !");
    }
  };

  // Vérifier que le token est valide au chargement (une seule fois)
  useEffect(() => {
    async function verifyToken() {
      if (!token) return;
      try {
        await getMe(token);
      } catch (err) {
        // Token invalide ou expiré
        console.error("Token invalide, déconnexion...", err);
        handleLogout();
      }
    }
    // Vérifier seulement au premier chargement
    if (token) {
      verifyToken();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Exécuter seulement au montage

  if (!token) {
    return (
      <div style={{ padding: 24 }}>
        <Login
          onLogged={(newToken) => {
            setToken(newToken);
            localStorage.setItem("auth_token", newToken);
          }}
        />
      </div>
    );
  }

  return (
    <div style={{ padding: 24, display: "flex", gap: 24 }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h1>AA Denis Mobilités – Fleet</h1>
          <button onClick={handleLogout} style={{ padding: "8px 16px" }}>
            Déconnexion
          </button>
        </div>
        
        {/* Section JWT Token */}
        <div style={{ 
          background: "#f5f5f5", 
          padding: 12, 
          borderRadius: 8, 
          marginBottom: 16,
          fontSize: "12px"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <strong>JWT Token :</strong>
            <button onClick={copyToken} style={{ padding: "4px 8px", fontSize: "12px" }}>
              📋 Copier
            </button>
          </div>
          <div style={{ 
            wordBreak: "break-all", 
            fontFamily: "monospace", 
            background: "white", 
            padding: 8, 
            borderRadius: 4,
            maxHeight: "60px",
            overflow: "auto"
          }}>
            {token}
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <button onClick={() => setProvider("uber")} disabled={provider === "uber"}>
            Uber
          </button>
          <button onClick={() => setProvider("bolt")} disabled={provider === "bolt"}>
            Bolt
          </button>
        </div>
        {offline && <p style={{ color: "orange" }}>Hors ligne</p>}
        {loading && <p>Chargement...</p>}
        {error && <p style={{ color: "red" }}>{error}</p>}
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
          <label>Limit</label>
          <input type="number" min={1} max={200} value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
          <label>Offset</label>
          <input type="number" min={0} value={offset} onChange={(e) => setOffset(Number(e.target.value))} />
        </div>
        <DriverTable drivers={drivers} selected={selectedDriver} onSelect={setSelectedDriver} />
        {provider === "bolt" && (
          <DriverTable
            drivers={boltDrivers.map((b) => ({ uuid: b.id, name: `${b.first_name} ${b.last_name}`, email: b.email }))}
            selected={selectedBoltDriver}
            onSelect={setSelectedBoltDriver}
          />
        )}
      </div>
      <div style={{ flex: 1 }}>
        <DriverDetail driver={provider === "uber" ? selectedDriverObj : selectedBoltDriverObj} />
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label>Du</label>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          <label>Au</label>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
        {provider === "uber" && (
          <>
            <h3>Métriques</h3>
            <MetricsCards metrics={metrics} />
            <h3>Paiements</h3>
            <PaymentList payments={payments} />
          </>
        )}
        {provider === "bolt" && (
          <>
            <h3>Trips</h3>
            <PaymentList
              payments={trips.map((t) => ({
                id: t.id,
                occurred_at: t.start_time,
                amount: t.price,
                currency: t.currency,
                description: t.status,
              }))}
            />
            <h3>Earnings</h3>
            <PaymentList payments={payments} />
          </>
        )}
      </div>
    </div>
  );
}

