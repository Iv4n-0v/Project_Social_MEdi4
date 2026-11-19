import { useState } from 'react';
import { Loading } from '../components/Guards';
import PanelNav, { NoVenture } from '../components/PanelNav';
import SocialRow from '../components/SocialRow';
import { useMyVenture } from '../components/useMyVenture';
import { PLATFORM_LABELS } from '../components/venture';

export default function MySocials() {
  const { venture, setVenture, error: loadError } = useMyVenture();
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const active = venture && venture.is_active;
  const byPlatform = Object.fromEntries((venture ? venture.social : []).map((s) => [s.platform, s]));
  return (
    <section>
      <h2>Mis redes sociales</h2>
      <PanelNav />
      {(error || loadError) && <div className="alert error" role="alert">{error || loadError}</div>}
      {notice && <div className="alert success" role="status">{notice}</div>}
      {venture === undefined && <Loading />}
      {venture === null && <NoVenture />}
      {venture && !active && <div className="card"><p>Tu emprendimiento está eliminado. Restáuralo desde Configuración.</p></div>}
      {active && (
        <div className="card">
          <p className="muted small">
            Pega el enlace de cada red; se valida que sea de esa red. Los seguidores son opcionales y se
            mostrarán como «declarados por el emprendedor».
          </p>
          <div className="stack">
            {Object.keys(PLATFORM_LABELS).map((p) => (
              <SocialRow
                key={`${p}-${byPlatform[p] ? byPlatform[p].url : ''}`}
                platform={p}
                current={byPlatform[p]}
                onError={setError}
                onSaved={(v, msg) => { setVenture(v); setNotice(msg); }}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
