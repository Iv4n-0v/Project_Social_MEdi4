import { useCallback, useEffect, useMemo, useState } from 'react';
import { friendlyMessage } from '../api/errors';
import { RESOURCES } from '../config/resources';
import { labelOf } from '../utils';
import ResourceForm from './ResourceForm';

export default function CrudPage({ resourceKey }) {
  const cfg = RESOURCES[resourceKey];
  const [items, setItems] = useState([]);
  const [lookups, setLookups] = useState({});
  const [filter, setFilter] = useState('true');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [editing, setEditing] = useState(null);
  const [audits, setAudits] = useState(null);

  const sources = useMemo(
    () => [...new Set(cfg.fields.filter((f) => f.source).map((f) => f.source))],
    [cfg]
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const query = filter === 'all' ? {} : { is_active: filter };
      const [list, ...related] = await Promise.all([
        cfg.api.list(query),
        ...sources.map((s) => RESOURCES[s].api.list()),
      ]);
      setItems(list);
      setLookups(Object.fromEntries(sources.map((s, i) => [s, related[i]])));
    } catch (e) {
      setError(friendlyMessage(e));
    } finally {
      setLoading(false);
    }
  }, [cfg, filter, sources]);

  useEffect(() => {
    setEditing(null);
    setAudits(null);
    setNotice('');
    load();
  }, [load]);

  const nameOf = (source, id) => {
    const found = (lookups[source] || []).find((x) => x.id === id);
    return found ? labelOf(found) : `#${id} (no encontrado)`;
  };

  function cell(item, col) {
    const v = item[col.key];
    if (col.type === 'bool') return <span className={`badge ${v ? 'ok' : 'off'}`}>{v ? 'Activo' : 'Inactivo'}</span>;
    if (col.type === 'multi') return v && v.length ? v.map((id) => nameOf(col.source, id)).join(', ') : '—';
    if (col.type === 'ref') return nameOf(col.source, v);
    if (col.type === 'date') return v ? new Date(v).toLocaleString() : '';
    if (col.type === 'image') return v ? <img className="avatar" src={v} alt={item.name} /> : 'Sin imagen';
    return v ?? '—';
  }

  async function run(action, okMessage) {
    setError('');
    setNotice('');
    try {
      await action();
      setNotice(okMessage);
      await load();
    } catch (e) {
      setError(friendlyMessage(e));
    }
  }

  async function showAudits(item) {
    setError('');
    try {
      setAudits({ item, rows: await cfg.api.audits(item.id) });
    } catch (e) {
      setError(friendlyMessage(e));
    }
  }

  async function save(values, fields) {
    setError('');
    setNotice('');
    try {
      const isNew = editing === 'new';
      const data = {};
      let file = null;
      for (const f of fields) {
        const v = values[f.name];
        if (f.type === 'file') file = v;
        else if (f.type === 'number' || f.type === 'select') {
          if (v !== '') data[f.name] = Number(v);
        } else if (f.type === 'multi') data[f.name] = v;
        else if (v !== '' || !isNew) data[f.name] = v;
      }
      if (isNew) {
        let body = data;
        if (cfg.createAsForm) {
          body = new FormData();
          Object.entries(data).forEach(([k, v]) =>
            Array.isArray(v) ? v.forEach((x) => body.append(k, x)) : body.append(k, v)
          );
          body.append('is_active', 'true');
          if (file) body.append('img', file);
        }
        await cfg.api.create(body);
      } else {
        await cfg.api.update(editing.id, data);
        if (file) await cfg.api.setImage(editing.id, file);
      }
      setEditing(null);
      setNotice(isNew ? 'Registro creado.' : 'Cambios guardados.');
      await load();
    } catch (e) {
      setError(friendlyMessage(e));
    }
  }

  return (
    <section>
      <div className="row between">
        <h2>{cfg.title}</h2>
        <div className="row">
          <select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filtro de estado">
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
            <option value="all">Todos</option>
          </select>
          <button className="btn primary" onClick={() => setEditing('new')}>Nuevo</button>
        </div>
      </div>

      {error && <p className="alert error" role="alert">{error}</p>}
      {notice && <p className="alert success">{notice}</p>}

      {editing && (
        <ResourceForm
          key={editing === 'new' ? 'new' : editing.id}
          cfg={cfg}
          item={editing === 'new' ? null : editing}
          lookups={lookups}
          onSubmit={save}
          onCancel={() => setEditing(null)}
        />
      )}

      {loading ? <p>Cargando…</p> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                {cfg.columns.map((c) => <th key={c.key}>{c.label}</th>)}
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && <tr><td colSpan={cfg.columns.length + 2}>Sin registros.</td></tr>}
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  {cfg.columns.map((c) => <td key={c.key}>{cell(item, c)}</td>)}
                  <td className="actions">
                    {item.is_active && <button className="btn small" onClick={() => setEditing(item)}>Editar</button>}
                    <button className="btn small" onClick={() => showAudits(item)}>Historial</button>
                    {item.is_active
                      ? <button className="btn small danger" onClick={() => run(() => cfg.api.remove(item.id), 'Registro desactivado.')}>Desactivar</button>
                      : <button className="btn small" onClick={() => run(() => cfg.api.restore(item.id), 'Registro restaurado.')}>Restaurar</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {audits && (
        <div className="card">
          <div className="row between">
            <h3>Historial del registro #{audits.item.id}</h3>
            <button className="btn small" onClick={() => setAudits(null)}>Cerrar</button>
          </div>
          <ul>
            {audits.rows.length === 0 && <li>Sin movimientos.</li>}
            {audits.rows.map((a) => (
              <li key={a.id}><strong>{a.action}</strong> · {new Date(a.timestamp).toLocaleString()}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
