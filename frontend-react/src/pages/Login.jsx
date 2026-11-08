import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '../api/auth';
import { friendlyMessage } from '../api/errors';
import { useAuth } from '../auth/AuthContext';
import { homeFor, safeNext } from '../utils';

export function OAuthButtons({ role }) {
  const [providers, setProviders] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    authApi.providers().then(setProviders).catch(() => setProviders({}));
  }, []);
  if (!providers) return null;
  const shown = [
    ['google', 'Google'],
    ['facebook', 'Facebook'],
  ].filter(([key]) => providers[key]);
  // Solo se muestran los proveedores realmente configurados: nada de botones muertos.
  if (shown.length === 0) return null;

  async function go(key) {
    setError('');
    try {
      const { url } = await authApi.oauthStart(key, role);
      window.location.assign(url);
    } catch (e) {
      setError(friendlyMessage(e));
    }
  }
  return (
    <div className="stack">
      {shown.map(([key, label]) => (
        <button key={key} type="button" className="btn" onClick={() => go(key)}>Continuar con {label}</button>
      ))}
      {error && <div className="alert error" role="alert">{error}</div>}
      <p className="muted small center">o con tu correo</p>
    </div>
  );
}

export default function Login() {
  const { login, account, ready } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const role = params.get('rol') === 'entrepreneur' ? 'entrepreneur' : 'visitor';
  const next = safeNext(params.get('next'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(params.get('oauth_error') || '');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (ready && account) navigate(next || homeFor(account), { replace: true });
  }, [ready, account, next, navigate]);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const acc = await login(email, password);
      navigate(next || homeFor(acc), { replace: true });
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const suffix = `?rol=${role}${next ? `&next=${encodeURIComponent(next)}` : ''}`;
  return (
    <section className="card narrow">
      <h2>{role === 'entrepreneur' ? 'Ingresa a tu panel de emprendedor' : 'Iniciar sesión'}</h2>
      <OAuthButtons role={role} />
      <form onSubmit={submit} className="stack">
        <label className="field"><span>Correo</span>
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="field"><span>Contraseña</span>
          <input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <div className="alert error" role="alert">{error}</div>}
        <button className="btn primary" disabled={busy}>{busy ? 'Ingresando…' : 'Ingresar'}</button>
      </form>
      <p className="small"><Link to="/recuperar">¿Olvidaste tu contraseña?</Link></p>
      <p className="small">¿No tienes cuenta? <Link to={`/registro${suffix}`}>Regístrate</Link></p>
    </section>
  );
}
