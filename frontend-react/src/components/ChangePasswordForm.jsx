import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../api/auth';
import { friendlyMessage } from '../api/errors';
import { useAuth } from '../auth/AuthContext';

const EMPTY = { current: '', next: '', repeat: '' };

// Formulario "Cambiar contraseña". Se usa en Mi cuenta y en Configuración del panel.
export default function ChangePasswordForm() {
  const { account } = useAuth();
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  // Cuentas creadas con Google o Facebook no tienen contraseña que cambiar
  if (!account.has_password) {
    return (
      <p className="muted small">
        Tu cuenta entra con Google o Facebook y no tiene contraseña. Si quieres crear una,{' '}
        <Link to="/recuperar">solicítala por correo</Link>.
      </p>
    );
  }

  function problem() {
    if (form.next.length < 8) return 'La nueva contraseña debe tener al menos 8 caracteres.';
    if (form.next.length > 128) return 'La nueva contraseña no puede superar los 128 caracteres.';
    if (form.next === form.current) return 'La nueva contraseña debe ser distinta de la actual.';
    if (form.next !== form.repeat) return 'La confirmación no coincide con la nueva contraseña.';
    return '';
  }

  async function submit(e) {
    e.preventDefault();
    setNotice('');
    const msg = problem();
    if (msg) {
      setError(msg);
      return;
    }
    setBusy(true);
    setError('');
    try {
      await authApi.changePassword(form.current, form.next);
      setForm(EMPTY);
      setNotice('Contraseña actualizada. Se cerraron tus otras sesiones.');
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <details className="pwd-box">
      <summary>Cambiar contraseña</summary>
      <form className="stack" onSubmit={submit}>
        <label className="field"><span>Contraseña actual</span>
          <input type="password" autoComplete="current-password" required maxLength={200} value={form.current} onChange={set('current')} />
        </label>
        <label className="field"><span>Nueva contraseña</span>
          <input type="password" autoComplete="new-password" required minLength={8} maxLength={128} value={form.next} onChange={set('next')} />
          <small className="muted">Mínimo 8 caracteres.</small>
        </label>
        <label className="field"><span>Repite la nueva contraseña</span>
          <input type="password" autoComplete="new-password" required maxLength={128} value={form.repeat} onChange={set('repeat')} />
        </label>
        {error && <div className="alert error" role="alert">{error}</div>}
        {notice && <div className="alert success" role="status">{notice}</div>}
        <button className="btn primary" disabled={busy}>{busy ? 'Guardando…' : 'Guardar contraseña'}</button>
      </form>
    </details>
  );
}
