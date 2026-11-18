import { Link, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function Loading() {
  return <p className="muted" role="status">Cargando…</p>;
}

// Exige sesion; si no hay, lleva a /ingresar y vuelve aqui al terminar.
export function RequireAuth({ children }) {
  const { isLoggedIn, ready } = useAuth();
  const loc = useLocation();
  if (!ready) return <Loading />;
  if (!isLoggedIn) {
    return <Navigate to={`/ingresar?next=${encodeURIComponent(loc.pathname)}`} replace />;
  }
  return children;
}

// Exige un rol. Es una ayuda de interfaz: la proteccion real la hace el gateway con el token.
export function RequireRole({ role, children }) {
  const { isLoggedIn, hasRole, ready, addRole } = useAuth();
  const loc = useLocation();
  if (!ready) return <Loading />;
  if (!isLoggedIn) {
    return <Navigate to={`/ingresar?rol=${role}&next=${encodeURIComponent(loc.pathname)}`} replace />;
  }
  if (!hasRole(role)) {
    return (
      <section className="card narrow">
        <h2>Esta sección es para emprendedores</h2>
        <p>Tu cuenta aún no tiene el rol de emprendedor. Puedes activarlo ahora; seguirás teniendo tu rol de visitante.</p>
        <div className="row">
          <button className="btn primary" onClick={() => addRole(role)}>Activar rol de emprendedor</button>
          <Link className="btn" to="/explorar">Volver al catálogo</Link>
        </div>
      </section>
    );
  }
  return children;
}
