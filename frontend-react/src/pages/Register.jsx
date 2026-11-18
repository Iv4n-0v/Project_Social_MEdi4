import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { friendlyMessage } from '../api/errors';
import { useAuth } from '../auth/AuthContext';
import { homeFor, safeNext } from '../utils';
import { OAuthButtons } from './Login';

export default function Register() {
  const { register, account, ready } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const next = safeNext(params.get('next'));
  const [role, setRole] = useState(params.get('rol') === 'entrepreneur' ? 'entrepreneur' : 'visitor');
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (ready && account) navigate(next || homeFor(account), { replace: true });
  }, [ready, account, next, navigate]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const acc = await register({ ...form, role });
      navigate(next || homeFor(acc), { replace: true });
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card narrow">
      <h2>Crear cuenta</h2>
      <fieldset className="role-pick">
        <legend>¿Cómo quieres empezar?</legend>
        <label className={`role-option${role === 'visitor' ? ' selected' : ''}`}>
          <input type="radio" name="role" value="visitor" checked={role === 'visitor'} onChange={() => setRole('visitor')} />
          <span><strong>Visitante</strong><br /><small>Explorar y guardar favoritos</small></span>
        </label>
        <label className={`role-option${role === 'entrepreneur' ? ' selected' : ''}`}>
          <input type="radio" name="role" value="entrepreneur" checked={role === 'entrepreneur'} onChange={() => setRole('entrepreneur')} />
          <span><strong>Emprendedor</strong><br /><small>Mostrar mi emprendimiento</small></span>
        </label>
      </fieldset>
      <p className="muted small">Podrás activar el otro rol más tarde con la misma cuenta.</p>
      <OAuthButtons role={role} />
      <form onSubmit={submit} className="stack">
        <label className="field"><span>Nombre</span>
          <input autoComplete="name" required maxLength={100} value={form.name} onChange={set('name')} />
        </label>
        <label className="field"><span>Correo</span>
          <input type="email" autoComplete="email" required value={form.email} onChange={set('email')} />
        </label>
        <label className="field"><span>Contraseña</span>
          <input type="password" autoComplete="new-password" required minLength={8} value={form.password} onChange={set('password')} />
          <small className="muted">Mínimo 8 caracteres, con letras y números.</small>
        </label>
        {error && <div className="alert error" role="alert">{error}</div>}
        <button className="btn primary" disabled={busy}>{busy ? 'Creando…' : 'Crear cuenta'}</button>
      </form>
      <p className="small">¿Ya tienes cuenta? <Link to={`/ingresar?rol=${role}${next ? `&next=${encodeURIComponent(next)}` : ''}`}>Ingresa</Link></p>
    </section>
  );
}
