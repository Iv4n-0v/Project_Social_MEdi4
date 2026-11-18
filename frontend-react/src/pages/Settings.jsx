import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { useAuth } from '../auth/AuthContext';
import PanelNav from '../components/PanelNav';
import { useMyVenture } from '../components/useMyVenture';

const ACTIONS = {
  CREATE: 'Creado', UPDATE: 'Editado', PUBLISH: 'Publicado', UNPUBLISH: 'Ocultado',
  DELETE: 'Eliminado', RESTORE: 'Restaurado',
};
const labelAction = (a) =>
  a.startsWith('SOCIAL_SET:') ? `Red vinculada: ${a.split(':')[1]}`
  : a.startsWith('SOCIAL_REMOVE:') ? `Red desvinculada: ${a.split(':')[1]}`
  : ACTIONS[a] || a;

export default function Settings() {
  const { account, logout } = useAuth();
  const navigate = useNavigate();
  const { venture, setVenture, error: loadError } = useMyVenture();
  const [audits, setAudits] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (venture) venturesApi.audits().then(setAudits).catch(() => {});
  }, [venture]);

  async function run(action, msg) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      setVenture(await action());
      setNotice(msg);
    } catch (e) {
      setError(friendlyMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Configuración</h2>
      <PanelNav />
      {(error || loadError) && <div className="alert error" role="alert">{error || loadError}</div>}
      {notice && <div className="alert success" role="status">{notice}</div>}

      <div className="card">
        <h3>Mi cuenta</h3>
        <dl className="data">
          <dt>Nombre</dt><dd>{account.name}</dd>
          <dt>Correo</dt><dd>{account.email}</dd>
        </dl>
        <div className="row">
          <Link className="btn" to="/cuenta">Roles y datos de la cuenta</Link>
          <button className="btn danger" onClick={async () => { await logout(); navigate('/', { replace: true }); }}>Cerrar sesión</button>
        </div>
      </div>

      {venture && (
        <>
          <div className="card">
            <h3>Visibilidad de mi emprendimiento</h3>
            {venture.is_active ? (
              <>
                <p>Estado: <span className={`badge ${venture.is_published ? 'ok' : 'off'}`}>{venture.is_published ? 'Publicado' : 'Borrador (no visible)'}</span></p>
                <div className="row">
                  {venture.is_published
                    ? <button className="btn" disabled={busy} onClick={() => run(venturesApi.unpublish, 'Ahora está oculto')}>Ocultar del catálogo</button>
                    : <button className="btn primary" disabled={busy} onClick={() => run(venturesApi.publish, 'Tu emprendimiento ya es visible')}>Publicar</button>}
                  <button className="btn danger" disabled={busy} onClick={() => run(venturesApi.remove, 'Emprendimiento eliminado')}>Eliminar</button>
                </div>
              </>
            ) : (
              <>
                <p>Eliminado: no se ve en el catálogo. Puedes restaurarlo (vuelve como borrador).</p>
                <button className="btn primary" disabled={busy} onClick={() => run(venturesApi.restore, 'Emprendimiento restaurado')}>Restaurar</button>
              </>
            )}
          </div>

          <div className="card">
            <h3>Historial de cambios</h3>
            {audits.length === 0 ? <p className="muted">Sin movimientos.</p> : (
              <ul className="history">
                {[...audits].reverse().map((a) => (
                  <li key={a.id} className="small">{new Date(a.timestamp).toLocaleString('es-CO')} — {labelAction(a.action)}</li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </section>
  );
}
