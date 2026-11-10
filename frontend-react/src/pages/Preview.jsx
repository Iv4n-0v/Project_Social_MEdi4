import { Link } from 'react-router-dom';
import { Loading } from '../components/Guards';
import PanelNav, { NoVenture } from '../components/PanelNav';
import { useMyVenture } from '../components/useMyVenture';
import { Avatar, SocialList } from '../components/venture';

export default function Preview() {
  const { venture } = useMyVenture();
  // Lo que ve un visitante: el nombre del emprendedor solo si autorizo mostrarlo
  const pub = venture
    ? { ...venture, entrepreneur_name: venture.show_entrepreneur_name ? venture.entrepreneur_name : null }
    : null;
  return (
    <section>
      <h2>Vista previa</h2>
      <PanelNav />
      {venture === undefined && <Loading />}
      {venture === null && <NoVenture />}
      {venture && (
        <>
          {!venture.is_active ? (
            <div className="alert error">Tu emprendimiento está eliminado: nadie lo ve. Restáuralo en Configuración.</div>
          ) : venture.is_published ? (
            <div className="alert success">Publicado: así lo ven los visitantes. <Link to={`/emprendimiento/${venture.id}`}>Abrir perfil público</Link></div>
          ) : (
            <div className="alert info">Borrador: los visitantes todavía no lo ven. Publícalo desde «Mi emprendimiento».</div>
          )}
          <h3>Tarjeta en el catálogo</h3>
          <div className="grid cards">
            <article className="card v-card">
              <div className="row">
                <Avatar venture={pub} />
                <div>
                  <h3 className="v-name">{pub.name}</h3>
                  {pub.category && <span className="badge off">{pub.category.name}</span>}
                </div>
              </div>
              {pub.entrepreneur_name && <p className="muted small">Por {pub.entrepreneur_name}</p>}
              {pub.description && <p className="v-desc">{pub.description}</p>}
              <SocialList social={pub.social} />
            </article>
          </div>
          <h3>Perfil completo</h3>
          <article className="card profile">
            <div className="row">
              <Avatar venture={pub} size={88} />
              <div>
                <h2>{pub.name}</h2>
                {pub.category && <span className="badge off">{pub.category.name}</span>}
                {pub.entrepreneur_name && <p className="muted">Por {pub.entrepreneur_name}</p>}
                {pub.location && <p className="muted small">📍 {pub.location}</p>}
              </div>
            </div>
            {pub.description ? <p className="v-desc full">{pub.description}</p> : <p className="muted">Aún sin descripción.</p>}
            <h3>Redes sociales</h3>
            <SocialList social={pub.social} />
          </article>
        </>
      )}
    </section>
  );
}
