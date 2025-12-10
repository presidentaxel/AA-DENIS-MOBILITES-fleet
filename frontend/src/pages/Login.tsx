import { useState } from "react";
import { login } from "../api/fleetApi";

type Props = {
  onLogged: (token: string) => void;
};

export default function Login({ onLogged }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await login(email, password);
      onLogged(res.access_token);
      setError(null);
    } catch (err) {
      setError("Login failed");
    }
  };

  return (
    <form onSubmit={submit}>
      <h2>Login</h2>
      <div>
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <div>
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </div>
      <button type="submit">Login</button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </form>
  );
}

