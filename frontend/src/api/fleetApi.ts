import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

export const login = async (email: string, password: string) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const res = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  const data = res.data as { access_token: string; token_type: string };
  // Stocker le token dans localStorage pour persister entre les rechargements
  if (data.access_token) {
    localStorage.setItem("auth_token", data.access_token);
  }
  return data;
};

export const getMe = async (token: string) => {
  const res = await api.get("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getDrivers = async (token: string, params?: { limit?: number; offset?: number }) => {
  const res = await api.get("/fleet/drivers", {
    params,
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getDriverMetrics = async (token: string, driverUuid: string, from: string, to: string) => {
  const res = await api.get(`/fleet/drivers/${driverUuid}/metrics`, {
    params: { from, to },
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getDriverPayments = async (token: string, driverUuid: string, from: string, to: string) => {
  const res = await api.get(`/fleet/drivers/${driverUuid}/payments`, {
    params: { from, to },
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

// Bolt endpoints
export const getBoltDrivers = async (token: string, params?: { limit?: number; offset?: number }) => {
  const res = await api.get("/bolt/drivers", {
    params,
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getBoltDriver = async (token: string, driverId: string) => {
  const res = await api.get(`/bolt/drivers/${driverId}`, { headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

export const getBoltTrips = async (token: string, driverId: string, from: string, to: string) => {
  const res = await api.get(`/bolt/drivers/${driverId}/trips`, {
    params: { from, to },
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getBoltEarnings = async (token: string, driverId: string, from: string, to: string) => {
  const res = await api.get(`/bolt/drivers/${driverId}/earnings`, {
    params: { from, to },
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getBoltDriverEarnings = async (token: string, driverId: string, from?: string, to?: string) => {
  const res = await api.get(`/bolt/drivers/${driverId}/earnings`, {
    params: from && to ? { from, to } : {},
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getBoltOrders = async (token: string, from: string, to: string, driverUuid?: string) => {
  const res = await api.get(`/bolt/orders`, {
    params: { from, to, ...(driverUuid && { driver_uuid: driverUuid }) },
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getBoltVehicles = async (token: string, params?: { limit?: number; offset?: number }) => {
  const res = await api.get("/bolt/vehicles", {
    params,
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getBoltVehicle = async (token: string, vehicleId: string) => {
  const res = await api.get(`/bolt/vehicles/${vehicleId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

