import { useState } from 'react';
import { labelOf } from '../utils';

function initial(field, item) {
  if (field.type === 'file') return null;
  if (field.type === 'multi') return item?.[field.name] ?? [];
  return item?.[field.name] ?? '';
}

export default function ResourceForm({ cfg, item, lookups, onSubmit, onCancel }) {
  const isNew = !item;
  const fields = cfg.fields.filter((f) => isNew || !f.createOnly);
  const [values, setValues] = useState(() =>
    Object.fromEntries(fields.map((f) => [f.name, initial(f, item)]))
  );
  const [saving, setSaving] = useState(false);

  const set = (name, value) => setValues((prev) => ({ ...prev, [name]: value }));
  const options = (f) => (lookups[f.source] || []).filter((o) => o.is_active);

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await onSubmit(values, fields);
    } finally {
      setSaving(false);
    }
  }

  function toggle(name, id) {
    const current = values[name];
    set(name, current.includes(id) ? current.filter((x) => x !== id) : [...current, id]);
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h3>{isNew ? `Nuevo registro` : `Editar registro #${item.id}`}</h3>
      {fields.map((f) => (
        <label key={f.name} className="field">
          <span>{f.label}{f.required ? ' *' : ''}</span>
          {f.type === 'textarea' && (
            <textarea value={values[f.name]} maxLength={f.max} rows={3}
              onChange={(e) => set(f.name, e.target.value)} />
          )}
          {(f.type === 'text' || f.type === 'number') && (
            <input type={f.type} value={values[f.name]} required={f.required}
              maxLength={f.max} min={f.min} step={f.step}
              onChange={(e) => set(f.name, e.target.value)} />
          )}
          {f.type === 'file' && (
            <input type="file" accept="image/*" onChange={(e) => set(f.name, e.target.files[0] || null)} />
          )}
          {f.type === 'select' && (
            <select value={values[f.name]} required={f.required}
              onChange={(e) => set(f.name, e.target.value)}>
              <option value="">Selecciona…</option>
              {options(f).map((o) => <option key={o.id} value={o.id}>{labelOf(o)}</option>)}
            </select>
          )}
          {f.type === 'multi' && (
            <div className="checks">
              {options(f).length === 0 && <em>No hay registros activos para elegir.</em>}
              {options(f).map((o) => (
                <label key={o.id} className="check">
                  <input type="checkbox" checked={values[f.name].includes(o.id)}
                    onChange={() => toggle(f.name, o.id)} />
                  {labelOf(o)}
                </label>
              ))}
            </div>
          )}
        </label>
      ))}
      <div className="row">
        <button type="submit" className="btn primary" disabled={saving}>
          {saving ? 'Guardando…' : 'Guardar'}
        </button>
        <button type="button" className="btn" onClick={onCancel}>Cancelar</button>
      </div>
    </form>
  );
}
