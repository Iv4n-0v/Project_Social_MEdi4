import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError, friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { Loading } from '../components/Guards';
import { PLATFORM_LABELS, SOURCE_LABELS, formatFollowers } from '../components/venture';

const PLACEHOLDERS = {
  instagram: 'https://instagram.com/tu_usuario',
  facebook: 'https://facebook.com/tu_pagina',
  tiktok: 'https://tiktok.com/@tu_usuario',
  whatsapp: 'https://wa.me/573001234567',
  youtube: 'https://youtube.com/@tu_canal',
};

const EMPTY = { name: '', entrepreneur_name: '', show_entrepreneur_name: false, description: '', location: '', category_id: '' };

function SocialRow({ platform, current, onSaved, onError }) {
  const [url, setUrl] = useState(current ? current.url : '');
  const [followers, setFollowers] = useState('');
  const [busy, setBusy] = useState(false);

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    onError('');
    try {
      const body = { url: url.trim() };
      if (followers !== '') body.followers = Number(followers);
      onSaved(await venturesApi.setSocial(platform, body), `${PLATFORM_LABELS[platform]} guardado`);
      setFollowers('');
    } catch (err) {
      onError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }
  async function unlink() {
    setBusy(true);
    onError('');
    try {
      const v = await venturesApi.removeSocial(platform);
      setUrl('');
      onSaved(v, `${PLATFORM_LABELS[platform]} desvinculado`);
    } catch (err) {
      onError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="social-row" onSubmit={save}>
      <strong>{PLATFORM_LABELS[platform]}</strong>
      <input
        type="url"
        aria-label={`Enlace de ${PLATFORM_LABELS[platform]}`}
        placeholder={PLACEHOLDERS[platform]}
        required
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      {platform !== 'whatsapp' && (
        <input
          type="number"
          min="0"
          aria-label={`Seguidores de ${PLATFORM_LABELS[platform]} (opcional)`}
          placeholder="Seguidores (opcional)"
          value={followers}
          onChange={(e) => setFollowers(e.target.value)}
        />
      )}
      <div className="row">
        <button className="btn small primary" disabled={busy}>{current ? 'Actualizar' : 'Vincular'}</button>
        {current && <button type="button" className="btn small danger" disabled={busy} onClick={unlink}>Desvincular</button>}
      </div>
      {current && current.followers != null && (
        <small className="muted">
          Último dato: {formatFollowers(current.followers)} seguidores ({SOURCE_LABELS[current.followers_source] || current.followers_source}
          {current.followers_updated_at ? `, ${new Date(current.followers_updated_at).toLocaleDateString('es-CO')}` : ''})
        </small>
      )}
    </form>
  );
}

export default function MyVenture() {
  const [venture, setVenture] = useState(undefined);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  const adopt = useCallback((v) => {
    setVenture(v);
    setForm({
      name: v.name || '',
      entrepreneur_name: v.entrepreneur_name || '',
      show_entrepreneur_name: !!v.show_entrepreneur_name,
      description: v.description || '',
      location: v.location || '',
      category_id: v.category_id ?? '',
    });
  }, []);

  useEffect(() => {
    venturesApi.categories().then(setCategories).catch(() => {});
    venturesApi
      .mine()
      .then(adopt)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) setVenture(null);
        else {
          setVenture(null);
          setError(friendlyMessage(e));
        }
      });
  }, [adopt]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  async function run(action, okMessage) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      adopt(await action());
      setNotice(okMessage);
    } catch (e) {
      setError(friendlyMessage(e));
    } finally {
      setBusy(false);
    }
  }

  const save = (e) => {
    e.preventDefault();
    const body = {
      ...form,
      name: form.name.trim(),
      category_id: form.category_id === '' ? null : Number(form.category_id),
    };
    return run(() => venturesApi.save(body), 'Cambios guardados');
  };

  if (venture === undefined) return <Loading />;

  const deleted = venture && !venture.is_active;
  const socialByPlatform = Object.fromEntries((venture ? venture.social : []).map((s) => [s.platform, s]));

  return (
    <section>
      <p className="small"><Link to="/panel">← Mi panel</Link></p>
      <h2>Mi emprendimiento</h2>
      {error && <div className="alert error" role="alert">{error}</div>}
      {notice && <div className="alert success" role="status">{notice}</div>}

      {deleted && (
        <div className="card">
          <p>Tu emprendimiento está eliminado y no se ve en el catálogo. Puedes restaurarlo (volverá como borrador).</p>
          <button className="btn primary" disabled={busy} onClick={() => run(venturesApi.restore, 'Emprendimiento restaurado')}>Restaurar</button>
        </div>
      )}

      {!deleted && (
        <form className="card" onSubmit={save}>
          <label className="field"><span>Nombre del emprendimiento *</span>
            <input required maxLength={100} value={form.name} onChange={set('name')} />
          </label>
          <label className="field"><span>Categoría</span>
            <select value={form.category_id} onChange={set('category_id')}>
              <option value="">Sin categoría</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
          <label className="field"><span>Descripción corta *</span>
            <textarea rows={4} maxLength={1000} value={form.description} onChange={set('description')} />
            <small className="muted">{form.description.length}/1000 · Es obligatoria para publicar.</small>
          </label>
          <label className="field"><span>Ubicación</span>
            <input maxLength={120} value={form.location} onChange={set('location')} />
          </label>
          <label className="field"><span>Tu nombre como emprendedor</span>
            <input maxLength={100} value={form.entrepreneur_name} onChange={set('entrepreneur_name')} />
          </label>
          <label className="check">
            <input type="checkbox" checked={form.show_entrepreneur_name} onChange={set('show_entrepreneur_name')} />
            Mostrar mi nombre en el perfil público
          </label>
          <div className="row">
            <button className="btn primary" disabled={busy || !form.name.trim()}>{venture ? 'Guardar cambios' : 'Crear emprendimiento'}</button>
          </div>
        </form>
      )}

      {venture && !deleted && (
        <>
          <div className="card">
            <h3>Visibilidad</h3>
            <p>
              Estado: <span className={`badge ${venture.is_published ? 'ok' : 'off'}`}>{venture.is_published ? 'Publicado' : 'Borrador (no visible)'}</span>
            </p>
            <div className="row">
              {venture.is_published ? (
                <>
                  <button className="btn" disabled={busy} onClick={() => run(venturesApi.unpublish, 'Ahora está oculto')}>Ocultar del catálogo</button>
                  <Link className="btn" to={`/emprendimiento/${venture.id}`}>Ver perfil público</Link>
                </>
              ) : (
                <button className="btn primary" disabled={busy} onClick={() => run(venturesApi.publish, 'Tu emprendimiento ya es visible')}>Publicar</button>
              )}
            </div>
          </div>

          <div className="card" id="redes">
            <h3>Mis redes sociales</h3>
            <p className="muted small">
              Pega el enlace de cada red. Los seguidores son opcionales y se mostrarán como “declarados por el emprendedor”.
            </p>
            <div className="stack">
              {Object.keys(PLATFORM_LABELS).map((p) => (
                <SocialRow
                  key={`${p}-${socialByPlatform[p] ? socialByPlatform[p].url : ''}`}
                  platform={p}
                  current={socialByPlatform[p]}
                  onError={setError}
                  onSaved={(v, msg) => { setVenture(v); setNotice(msg); }}
                />
              ))}
            </div>
          </div>

          <div className="card">
            <h3>Eliminar</h3>
            <p className="muted small">Se oculta del catálogo y queda en auditoría; podrás restaurarlo.</p>
            <button className="btn danger" disabled={busy} onClick={() => run(venturesApi.remove, 'Emprendimiento eliminado')}>Eliminar emprendimiento</button>
          </div>
        </>
      )}
    </section>
  );
}
