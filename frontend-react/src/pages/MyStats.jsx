import { useEffect, useState } from 'react';
import { friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { Loading } from '../components/Guards';
import PanelNav, { NoVenture } from '../components/PanelNav';
import { useMyVenture } from '../components/useMyVenture';
import { PLATFORM_LABELS, SOURCE_LABELS, formatFollowers } from '../components/venture';

const fmtDate = (d) => new Date(d).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

function StatCard({ stat, onUpdated, onError }) {
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const canTrack = stat.platform !== 'whatsapp'; // WhatsApp no tiene seguidores

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
      {venture === undefined && <Loading />}
      {venture === null && <NoVenture />}
      {venture && (
        <>
          <div className="card info">
            <p className="small">
              <strong>Automático</strong> = la cifra se obtuvo de la red con su API oficial. <strong>Manual</strong> =
              la declaraste tú, con su fecha. Por ahora todas las cifras son manuales: la conexión automática con
              cada red se activa más adelante y solo donde la red lo permita.
            </p>
          </div>
          {stats === undefined && <Loading />}
          {stats && stats.length === 0 && !error && <div className="card"><p>Aún no has vinculado redes. Hazlo en «Mis redes».</p></div>}
          <div className="grid cards">
            {(stats || []).map((s) => <StatCard key={s.platform} stat={s} onUpdated={load} onError={setError} />)}
          </div>
        </>
      )}
    </section>
  );
}
