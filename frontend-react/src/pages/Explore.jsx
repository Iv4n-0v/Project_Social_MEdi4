import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { Loading } from '../components/Guards';
import { VentureCard } from '../components/venture';

const PAGE = 12;

export default function Explore() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') || '';
  const category = params.get('categoria') || '';
  const [text, setText] = useState(q);
  const [categories, setCategories] = useState([]);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    venturesApi.categories().then(setCategories).catch(() => setCategories([]));
  }, []);

  const load = useCallback(
    async (offset) => {
      setLoading(true);
      setError('');
      try {
        const r = await venturesApi.search({ q, category_id: category, limit: PAGE, offset });
        setData((cur) => (offset > 0 && cur ? { ...r, items: [...cur.items, ...r.items] } : r));
      } catch (e) {
        setError(friendlyMessage(e));
      } finally {
        setLoading(false);
      }
    },
    [q, category]
  );

  useEffect(() => {
    load(0);
  }, [load]);

  function update(next) {
    const p = new URLSearchParams(params);
    Object.entries(next).forEach(([k, v]) => (v ? p.set(k, v) : p.delete(k)));
    setParams(p, { replace: true });
  }

  const items = data ? data.items : [];
  return (
    <section>
      <h2>Explora emprendimientos</h2>
      <form
        className="row filters"
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          update({ q: text.trim() });
        }}
      >
        <input
          type="search"
          aria-label="Buscar por nombre"
          placeholder="Buscar por nombre o descripción"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <select aria-label="Categoría" value={category} onChange={(e) => update({ categoria: e.target.value })}>
          <option value="">Todas las categorías</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button className="btn primary">Buscar</button>
        {(q || category) && (
          <button type="button" className="btn" onClick={() => { setText(''); setParams({}, { replace: true }); }}>
            Limpiar
          </button>
        )}
      </form>
      {error && <div className="alert error" role="alert">{error}</div>}
      {loading && !data && <Loading />}
      {data && items.length === 0 && !loading && (
        <div className="card">
          <p>
            {q || category
              ? 'No encontramos emprendimientos con esos filtros.'
              : 'Aún no hay emprendimientos publicados. ¡Vuelve pronto!'}
          </p>
        </div>
      )}
      <div className="grid cards">
        {items.map((v) => <VentureCard key={v.id} venture={v} />)}
      </div>
      {data && items.length < data.total && (
        <div className="row center">
          <button className="btn" disabled={loading} onClick={() => load(items.length)}>
            {loading ? 'Cargando…' : `Ver más (${data.total - items.length})`}
          </button>
        </div>
      )}
    </section>
  );
}
