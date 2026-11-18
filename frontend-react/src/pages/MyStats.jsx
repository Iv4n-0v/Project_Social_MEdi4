import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { Loading } from '../components/Guards';
import PanelNav, { NoVenture } from '../components/PanelNav';
import { useMyVenture } from '../components/useMyVenture';
import { PLATFORM_LABELS, SOURCE_LABELS, formatFollowers } from '../components/venture';

const YOUTUBE_MESSAGES = {
  ok: ['success', 'Listo: obtuvimos tus suscriptores de YouTube con la API oficial.'],
  denied: ['info', 'No diste el permiso en Google, así que no se conectó nada.'],
  invalid: ['error', 'El enlace de conexión venció o no es válido. Inténtalo de nuevo.'],
  nochannel: ['error', 'Esa cuenta de Google no tiene un canal de YouTube. Elige la cuenta que sea dueña de tu canal.'],
  hidden: ['info', 'Tu canal oculta su número de suscriptores, así que YouTube no lo entrega. Puedes registrarlo manualmente.'],
  novenue: ['error', 'Primero crea tu emprendimiento y vuelve a conectar.'],
  notconfigured: ['error', 'La conexión con YouTube no está configurada en este entorno.'],
  failed: ['error', 'No pudimos leer tu canal en este momento. Inténtalo de nuevo más tarde.'],
};

const fmtDate = (d) => new Date(d).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

function StatCard({ stat, onUpdated, onError, youtubeEnabled }) {
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const canTrack = stat.platform !== 'whatsapp'; // WhatsApp no tiene seguidores

  async function connectYoutube() {
    setBusy(true);
    onError('');
    try {
      const { url } = await venturesApi.youtubeStart();
      window.location.assign(url); // Google pide el permiso y nos devuelve a esta pagina
    } catch (err) {
      onError(friendlyMessage(err));
      setBusy(false);
    }
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    onError('');
    try {
      await venturesApi.setSocial(stat.platform, { url: stat.url, followers: Number(value) });
      setValue('');
      await onUpdated();
    } catch (err) {
      onError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="card stat">
      <h3>{PLATFORM_LABELS[stat.platform] || stat.platform}</h3>
      {!canTrack ? (
        <p className="muted">WhatsApp no tiene seguidores: no hay cifra que mostrar.</p>
      ) : stat.latest ? (
        <>
          <p className="stat-number">{formatFollowers(stat.latest.followers)} <span className="muted small">seguidores</span></p>
          <p className="small">
            <span className={`badge ${stat.latest.source === 'api' ? 'ok' : 'off'}`}>
              {stat.latest.source === 'api' ? 'Automático' : 'Manual'}
            </span>{' '}
            {SOURCE_LABELS[stat.latest.source] || stat.latest.source} · {fmtDate(stat.latest.updated_at)}
          </p>
        </>
      ) : (
        <p className="muted">Sin datos todavía. No mostramos cifras que no tengamos.</p>
      )}
      {stat.platform === 'youtube' && youtubeEnabled && (
        <div className="row">
          <button type="button" className="btn small" disabled={busy} onClick={connectYoutube}>
            {stat.latest && stat.latest.source === 'api' ? 'Actualizar desde YouTube' : 'Conectar con YouTube'}
          </button>
          <small className="muted">Permiso de solo lectura. No guardamos tu acceso a Google.</small>
        </div>
      )}
      {canTrack && (
        <form className="row" onSubmit={submit}>
          <input
            type="number"
            min="0"
            required
            aria-label={`Actualizar seguidores de ${PLATFORM_LABELS[stat.platform]}`}
            placeholder="Nueva cifra"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
          <button className="btn small primary" disabled={busy}>Registrar manualmente</button>
        </form>
      )}
      {stat.history.length > 1 && (
        <details>
          <summary className="small">Historial ({stat.history.length})</summary>
          <ul className="history">
            {stat.history.map((p, i) => (
              <li key={i} className="small">
                {fmtDate(p.updated_at)} — {formatFollowers(p.followers)} ({p.source === 'api' ? 'automático' : 'manual'})
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}

export default function MyStats() {
  const { venture } = useMyVenture();
  const [stats, setStats] = useState(undefined);
  const [error, setError] = useState('');
  const [youtubeEnabled, setYoutubeEnabled] = useState(false);
  const [params, setParams] = useSearchParams();
  const yt = params.get('youtube');
  const ytMessage = yt && YOUTUBE_MESSAGES[yt] ? YOUTUBE_MESSAGES[yt] : null;

  useEffect(() => {
    venturesApi.integrations().then((i) => setYoutubeEnabled(!!i.youtube)).catch(() => {});
  }, []);

  async function load() {
    try {
      setStats(await venturesApi.stats());
    } catch (e) {
      setStats([]);
      setError(friendlyMessage(e));
    }
  }
  useEffect(() => {
    if (venture) load();
  }, [venture]);

  return (
    <section>
      <h2>Estadísticas</h2>
      <PanelNav />
      {error && <div className="alert error" role="alert">{error}</div>}
      {ytMessage && (
        <div className={`alert ${ytMessage[0]}`} role={ytMessage[0] === 'error' ? 'alert' : 'status'}>
          {ytMessage[1]}{' '}
          <button type="button" className="linklike" onClick={() => setParams({}, { replace: true })}>Cerrar</button>
        </div>
      )}
      {venture === undefined && <Loading />}
      {venture === null && <NoVenture />}
      {venture && (
        <>
          <div className="card info">
            <p className="small">
              <strong>Automático</strong> = la cifra se obtuvo de la red con su API oficial. <strong>Manual</strong> =
              la declaraste tú, con su fecha. Hoy solo YouTube se puede conectar de forma automática (con su API
              oficial y permiso de solo lectura). Instagram, Facebook y TikTok exigen aprobación de cada plataforma
              para leer seguidores, así que por ahora se registran a mano y se rotulan como «Manual».
            </p>
          </div>
          {stats === undefined && <Loading />}
          {stats && stats.length === 0 && !error && <div className="card"><p>Aún no has vinculado redes. Hazlo en «Mis redes».</p></div>}
          <div className="grid cards">
            {(stats || []).map((s) => <StatCard key={s.platform} stat={s} onUpdated={load} onError={setError} youtubeEnabled={youtubeEnabled} />)}
          </div>
        </>
      )}
    </section>
  );
}
