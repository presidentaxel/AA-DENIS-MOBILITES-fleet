import React, { useState } from "react";
import { login } from "../api/fleetApi";

type LoginPageProps = {
  onLogin: (token: string) => void;
};

export function LoginPage({ onLogin }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await login(email, password);
      if (data.access_token) {
        onLogin(data.access_token);
      }
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
        err?.message ||
        "Erreur de connexion. Vérifiez vos identifiants."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ justifyContent: "center", alignItems: "center" }}>
      <div className="card" style={{ maxWidth: "400px", width: "100%", margin: "2rem" }}>
        <div className="card-header">
          <h2 className="card-title">Connexion</h2>
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
                placeholder="votre@email.com"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Mot de passe</label>
              <input
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                placeholder="••••••••"
              />
            </div>
            {error && (
              <div className="text-error mb-4" style={{ fontSize: "0.875rem" }}>
                ⚠️ {error}
              </div>
            )}
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "100%" }}
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="spinner" style={{ width: "1rem", height: "1rem", borderWidth: "2px" }}></div>
                  Connexion...
                </>
              ) : (
                "Se connecter"
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

