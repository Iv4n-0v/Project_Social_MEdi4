import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError, friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { Loading } from '../components/Guards';
import PanelNav from '../components/PanelNav';
import { Avatar } from '../components/venture';

const MAX_MB = 5;

const EMPTY = { name: '', entrepreneur_name: '', show_entrepreneur_name: false, description: '', location: '', category_id: '' };

export default function MyVenture() {
  const [venture, setVenture] = useState(undefined);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [canUpload, setCanUpload] = useState(false);

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
    venturesApi.integrations().then((i) => setCanUpload(!!i.photo_upload)).catch(() => {});
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

  function pickPhoto(e) {
    const file = e.target.files && e.target.files[0];
    e.target.value = ''; // permite elegir de nuevo el mismo archivo
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setError('Usa una imagen JPG, PNG o WEBP.');
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`La imagen supera los ${MAX_MB} MB.`);
      return;
    }
    return run(() => venturesApi.setImage(file), 'Foto actualizada');
  }

  if (venture === undefined) return <Loading />;

  const deleted = venture && !venture.is_active;

  return (
    <section>
      <h2>Mi emprendimiento</h2>
      <PanelNav />
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
            <h3>Foto del emprendimiento</h3>
            <div className="row photo-row">
              <Avatar venture={venture} size={96} />
              <div>
                {canUpload ? (
                  <>
                    <label className="btn" aria-disabled={busy}>
                      {venture.profile_image_url ? 'Cambiar foto' : 'Subir foto'}
                      <input type="file" accept="image/jpeg,image/png,image/webp" hidden disabled={busy} onChange={pickPhoto} />
                    </label>{' '}
                    {venture.profile_image_url && (
                      <button className="btn" disabled={busy} onClick={() => run(venturesApi.removeImage, 'Foto eliminada')}>Quitar foto</button>
                    )}
                    <p className="muted small">JPG, PNG o WEBP, hasta {MAX_MB} MB.</p>
                  </>
                ) : (
                  <p className="muted small">La subida de fotos aún no está configurada en este entorno.</p>
                )}
              </div>
            </div>
          </div>

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
