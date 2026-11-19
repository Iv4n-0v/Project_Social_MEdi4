import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApiError, friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { Loading } from '../components/Guards';
import { Avatar, FavoriteButton, ShareButton, SocialList } from '../components/venture';

export default function VentureDetail() {
  const { id } = useParams();
  const [venture, setVenture] = useState(null);
  const [error, setError] = useState('');
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    let alive = true;
    setVenture(null);
    setMissing(false);
    setError('');
    venturesApi
      .get(id)
      .then((v) => alive && setVenture(v))
      .catch((e) => {
        if (!alive) return;
        if (e instanceof ApiError && (e.status === 404 || e.status === 422)) setMissing(true);
        else setError(friendlyMessage(e));
      });
    return () => {
      alive = false;
    };
  }, [id]);

  if (missing) {
    return (
      <section className="card narrow">
        <h2>Emprendimiento no disponible</h2>
        <p>Puede que haya dejado de estar publicado.</p>
        <Link className="btn" to="/explorar">Volver al catálogo</Link>
      </section>
    );
  }
  if (error) return <div className="alert error" role="alert">{error}</div>;
  if (!venture) return <Loading />;
  return (
    <section>
      <p className="small"><Link to="/explorar">← Volver al catálogo</Link></p>
      <article className="card profile">
        <div className="row">
          <Avatar venture={venture} size={88} />
          <div>
            <h2>{venture.name}</h2>
            {venture.category && <span className="badge off">{venture.category.name}</span>}
            {venture.entrepreneur_name && <p className="muted">Por {venture.entrepreneur_name}</p>}
            {venture.location && <p className="muted small">📍 {venture.location}</p>}
          </div>
        </div>
        {venture.description && <p className="v-desc full">{venture.description}</p>}
        <h3>Redes sociales</h3>
        <SocialList social={venture.social} />
        <div className="row v-actions">
          <FavoriteButton venture={venture} />
          <ShareButton venture={venture} />
        </div>
      </article>
    </section>
  );
}
