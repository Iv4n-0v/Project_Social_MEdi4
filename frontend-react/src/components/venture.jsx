import { useEffect, useState } from 'react';
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

export function BrokenImage({ size = 56, className = 'v-avatar' }) {
  return (
    <div
      className={`${className} v-broken`}
      style={{ width: size, height: size }}
      role="img"
      aria-label="Imagen dañada o no disponible"
      title="La imagen está dañada o no está disponible"
    >
      <svg viewBox="0 0 24 24" width={size * 0.5} height={size * 0.5} aria-hidden="true" focusable="false">
        <rect x="3" y="4" width="18" height="16" rx="2" fill="none" stroke="currentColor" strokeWidth="2" />
        <circle cx="9" cy="10" r="1.6" fill="currentColor" />
        <path d="M3 17l5-5 4 4 3-3 6 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
        <path d="M4 3l16 18" stroke="var(--color-danger)" strokeWidth="2.2" strokeLinecap="round" />
      </svg>
    </div>
  );
}

export function Avatar({ venture, size = 56 }) {
  const [failed, setFailed] = useState(false);
  const url = venture.profile_image_url;
  const initial = (venture.name || '?').trim().charAt(0).toUpperCase();

  // Si cambia la URL (foto nueva), se vuelve a intentar cargar
  useEffect(() => setFailed(false), [url]);

  if (url && failed) return <BrokenImage size={size} />;
  if (url) {
    return (
      <img
        className="v-avatar"
        style={{ width: size, height: size }}
        src={url}
        alt=""
        onError={() => setFailed(true)}
      />
    );
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
        className={`btn small heart${on ? ' on' : ''}`}
        onClick={click}
        disabled={busy}
        aria-pressed={on}
        aria-label={on ? 'Quitar de favoritos' : 'Añadir a favoritos'}
        title={on ? 'Quitar de favoritos' : 'Añadir a favoritos'}
      >
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">
          <path
            d="M12 21s-7.5-4.6-9.6-9.1C.9 8.6 2.6 5 6.1 5c2 0 3.4 1.1 4.2 2.3h3.4C14.5 6.1 15.9 5 17.9 5c3.5 0 5.2 3.6 3.7 6.9C19.5 16.4 12 21 12 21z"
            fill={on ? 'currentColor' : 'none'}
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        </svg>
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
      {venture.location && (
        <p className="v-location muted small">
          <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" focusable="false">
            <path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
            <circle cx="12" cy="10" r="2.5" fill="none" stroke="currentColor" strokeWidth="2" />
          </svg>
          <span className="sr-only">Ubicación: </span>{venture.location}
        </p>
      )}
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
