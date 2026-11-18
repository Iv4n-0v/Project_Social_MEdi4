import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { friendlyMessage } from '../api/errors';
import { useAuth } from '../auth/AuthContext';

const ROLE_LABEL = { visitor: 'Visitante', entrepreneur: 'Emprendedor' };

export default function Account() {
  const { account, addRole, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function enable(role) {
    setBusy(true);
    setError('');
    try {
      await addRole(role);
    } catch (e) {
      setError(friendlyMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function out() {
    await logout();
    navigate('/', { replace: true });
  }
  return (
    <section className="card narrow">
      <h2>Mi cuenta</h2>
      <dl className="data">
        <dt>Nombre</dt><dd>{account.name}</dd>
        <dt>Correo</dt><dd>{account.email}</dd>
        <dt>Roles</dt>
        <dd>{account.roles.map((r) => <span key={r} className="badge ok role-badge">{ROLE_LABEL[r] || r}</span>)}</dd>
      </dl>
      {error && <div className="alert error" role="alert">{error}</div>}
      <div className="stack">
        {!hasRole('entrepreneur') && (
          <button className="btn" disabled={busy} onClick={() => enable('entrepreneur')}>Activar rol de emprendedor</button>
        )}
        {!hasRole('visitor') && (
          <button className="btn" disabled={busy} onClick={() => enable('visitor')}>Activar rol de visitante</button>
        )}
        {hasRole('entrepreneur') && <Link className="btn" to="/panel">Ir a mi panel</Link>}
        <button className="btn danger" onClick={out}>Cerrar sesión</button>
      </div>
    </section>
  );
}
