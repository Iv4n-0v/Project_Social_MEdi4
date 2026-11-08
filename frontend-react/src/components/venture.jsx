import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { friendlyMessage } from '../api/errors';
import { useAuth } from '../auth/AuthContext';
import { useFavorites } from '../auth/FavoritesContext';

export const PLATFORM_LABELS = {
  instagram: 'Instagram',
  facebook: 'Facebook',
  tiktok: 'TikTok',
  whatsapp: 'WhatsApp',
  youtube: 'YouTube',
};

export const SOURCE_LABELS = { manual: 'declarado por el emprendedor', api: 'verificado con la red' };

export function formatFollowers(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

export function Avatar({ venture, size = 56 }) {
  const initial = (venture.name || '?').trim().charAt(0).toUpperCase();
  if (venture.profile_image_url) {
    return <img className="v-avatar" style={{ width: size, height: size }} src={venture.profile_image_url} alt="" />;
  }
  return (
    <div className="v-avatar v-initial" style={{ width: size, height: size, fontSize: size * 0.45 }} aria-hidden="true">
      {initial}
    </div>
  );
}

export function SocialList({ social }) {
  if (!social || social.length === 0) return <p className="muted small">Aún no ha publicado sus redes.</p>;
  return (
    <ul className="social-list">
      {social.map((s) => (
        <li key={s.platform}>
          <a href={s.url} target="_blank" rel="noopener noreferrer nofollow">{PLATFORM_LABELS[s.platform] || s.platform}</a>
          {s.followers != null && (
            <span className="muted small">
              {' '}· {formatFollowers(s.followers)} seguidores
              {s.followers_source ? ` (${SOURCE_LABELS[s.followers_source] || s.followers_source})` : ''}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

export async function shareVenture(venture) {
  const url = `${window.location.origin}/emprendimiento/${venture.id}`;
  if (navigator.share) {
    try {
      await navigator.share({ title: venture.name, text: venture.description || venture.name, url });
      return 'Compartido';
    } catch (e) {
      if (e && e.name === 'AbortError') return '';
    }
  }
  try {
    await navigator.clipboard.writeText(url);
    return 'Enlace copiado';
  } catch {
    window.prompt('Copia este enlace', url);
    return '';
  }
}

export function FavoriteButton({ venture }) {
  const { isLoggedIn } = useAuth();
  const { isFavorite, toggle } = useFavorites();
  const navigate = useNavigate();
  const loc = useLocation();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const on = isFavorite(venture.id);

  async function click() {
    if (!isLoggedIn) {
      navigate(`/ingresar?next=${encodeURIComponent(loc.pathname + loc.search)}`);
      return;
    }
    setBusy(true);
    setError('');
    try {
      await toggle(venture.id);
    } catch (e) {
      setError(friendlyMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button
        type="button"
        className={`btn small${on ? ' on' : ''}`}
        onClick={click}
        disabled={busy}
        aria-pressed={on}
      >
        {on ? '★ En favoritos' : '☆ Guardar'}
      </button>
      {error && <span className="alert error small" role="alert">{error}</span>}
    </>
  );
}

export function ShareButton({ venture }) {
  const [msg, setMsg] = useState('');
  return (
    <>
      <button
        type="button"
        className="btn small"
        onClick={async () => {
          setMsg(await shareVenture(venture));
          setTimeout(() => setMsg(''), 2500);
        }}
      >
        Compartir
      </button>
      {msg && <span className="muted small" role="status">{msg}</span>}
    </>
  );
}

export function VentureCard({ venture }) {
  return (
    <article className="card v-card">
      <div className="row">
        <Avatar venture={venture} />
        <div>
          <h3 className="v-name"><Link to={`/emprendimiento/${venture.id}`}>{venture.name}</Link></h3>
          {venture.category && <span className="badge off">{venture.category.name}</span>}
        </div>
      </div>
      {venture.entrepreneur_name && <p className="muted small">Por {venture.entrepreneur_name}</p>}
      {venture.description && <p className="v-desc">{venture.description}</p>}
      <SocialList social={venture.social} />
      <div className="row v-actions">
        <Link className="btn small primary" to={`/emprendimiento/${venture.id}`}>Ver perfil</Link>
        <FavoriteButton venture={venture} />
        <ShareButton venture={venture} />
      </div>
    </article>
  );
}
