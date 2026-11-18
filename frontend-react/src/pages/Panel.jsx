import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { venturesApi } from '../api/ventures';
import { useAuth } from '../auth/AuthContext';
import { Loading } from '../components/Guards';
import PanelNav from '../components/PanelNav';

const TOOLS = [
  ['/usuarios', 'Usuarios', 'Registra usuarios y las metodologías que aplican.'],
  ['/metodologias', 'Metodologías', 'Administra metodologías y sus beneficios.'],
  ['/beneficios', 'Beneficios', 'Catálogo de beneficios.'],
  ['/analisis', 'Análisis', 'Sector, alcance y tiempo en redes por usuario.'],
];

function statusOf(v) {
  if (!v) return ['Sin crear', 'off'];
  if (!v.is_active) return ['Eliminado', 'off'];
  return v.is_published ? ['Publicado', 'ok'] : ['Borrador (no visible)', 'off'];
}

export default function Panel() {
  const { account } = useAuth();
  const [venture, setVenture] = useState(undefined); // undefined = cargando, null = no existe
  useEffect(() => {
    venturesApi
      .mine()
      .then(setVenture)
      .catch(() => setVenture(null)); // 404 = aun no lo crea
  }, []);
  const [label, tone] = statusOf(venture);
  return (
    <section>
      <h2>Hola, {account.name}</h2>
      <PanelNav />
      <div className="grid two">
        <article className="card">
          <h3>Mi emprendimiento</h3>
          {venture === undefined ? <Loading /> : (
            <>
              <p>{venture ? venture.name : 'Aún no has creado tu emprendimiento.'}</p>
              <p><span className={`badge ${tone}`}>{label}</span></p>
              <div className="row">
                <Link className="btn primary" to="/panel/emprendimiento">{venture ? 'Editar' : 'Crear mi emprendimiento'}</Link>
                {venture && venture.is_published && <Link className="btn" to={`/emprendimiento/${venture.id}`}>Ver como visitante</Link>}
              </div>
            </>
          )}
        </article>
        <article className="card">
          <h3>Mis redes sociales</h3>
          <p>Vincula Instagram, Facebook, TikTok, WhatsApp o YouTube para que los visitantes te encuentren.</p>
          <div className="row">
            <Link className="btn" to="/panel/redes">Administrar redes</Link>
            <Link className="btn" to="/panel/estadisticas">Ver estadísticas</Link>
          </div>
        </article>
      </div>
      <h3>Herramientas</h3>
      <div className="grid">
        {TOOLS.map(([to, title, text]) => (
          <Link key={to} to={to} className="card link-card">
            <h3>{title}</h3>
            <p>{text}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
