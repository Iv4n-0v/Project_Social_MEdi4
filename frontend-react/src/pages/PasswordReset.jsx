import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { authApi } from '../api/auth';
import { friendlyMessage } from '../api/errors';

export function Forgot() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await authApi.forgot(email);
      setSent(true);
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="card narrow">
      <h2>Recuperar contraseña</h2>
      {sent ? (
        <div className="alert success" role="status">
          Si el correo está registrado, te enviamos un enlace para restablecer la contraseña. Vence en 60 minutos.
        </div>
      ) : (
        <form onSubmit={submit} className="stack">
          <label className="field"><span>Correo de tu cuenta</span>
            <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          {error && <div className="alert error" role="alert">{error}</div>}
          <button className="btn primary" disabled={busy}>{busy ? 'Enviando…' : 'Enviar enlace'}</button>
        </form>
      )}
      <p className="small"><Link to="/ingresar">Volver a ingresar</Link></p>
    </section>
  );
}

export function Reset() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const [password, setPassword] = useState('');
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await authApi.reset(token, password);
      setDone(true);
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }
  if (!token) {
    return (
      <section className="card narrow">
        <h2>Enlace incompleto</h2>
        <p>Abre el enlace completo que recibiste por correo o <Link to="/recuperar">solicita uno nuevo</Link>.</p>
      </section>
    );
  }
  return (
    <section className="card narrow">
      <h2>Nueva contraseña</h2>
      {done ? (
        <div className="alert success" role="status">
          Contraseña actualizada. <Link to="/ingresar">Inicia sesión</Link> con la nueva.
        </div>
      ) : (
        <form onSubmit={submit} className="stack">
          <label className="field"><span>Nueva contraseña</span>
            <input type="password" required minLength={8} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div className="alert error" role="alert">{error}</div>}
          <button className="btn primary" disabled={busy}>{busy ? 'Guardando…' : 'Guardar contraseña'}</button>
        </form>
      )}
    </section>
  );
}
