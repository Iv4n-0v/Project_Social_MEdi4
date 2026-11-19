import { useEffect, useId, useRef, useState } from 'react';

const PHOTON = 'https://photon.komoot.io/api/';

function toLabel(p) {
  const parts = [p.name, p.city || p.county, p.state, p.country].filter(Boolean);
  return parts.filter((x, i) => parts.indexOf(x) === i).join(', ');
}

export default function LocationInput({ id, value, onChange, maxLength = 120 }) {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const [active, setActive] = useState(-1);
  const picked = useRef(false);
  const box = useRef(null);
  const listId = useId();

  useEffect(() => {
    if (picked.current) {
      picked.current = false;
      return undefined;
    }
    const q = value.trim();
    if (q.length < 3) {
      setItems([]);
      setOpen(false);
      setFailed(false);
      setLoading(false);
      return undefined;
    }
    const ctl = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setFailed(false);
      try {
        const url = `${PHOTON}?q=${encodeURIComponent(q)}&limit=5&lat=4.6&lon=-74.1`;
        const res = await fetch(url, { signal: ctl.signal });
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        const seen = new Set();
        const list = (data.features || [])
          .map((f) => toLabel(f.properties || {}))
          .filter((l) => l && !seen.has(l) && seen.add(l));
        setItems(list);
        setActive(-1);
        setOpen(list.length > 0);
      } catch (e) {
        if (e.name !== 'AbortError') {
          setItems([]);
          setOpen(false);
          setFailed(true);
        }
      } finally {
        if (!ctl.signal.aborted) setLoading(false);
      }
    }, 450);
    return () => {
      clearTimeout(timer);
      ctl.abort();
    };
  }, [value]);

  useEffect(() => {
    function outside(e) {
      if (box.current && !box.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', outside);
    return () => document.removeEventListener('mousedown', outside);
  }, []);

  function pick(label) {
    picked.current = true;
    onChange(label.slice(0, maxLength));
    setOpen(false);
    setItems([]);
  }

  function onKeyDown(e) {
    if (!open || items.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((a) => (a + 1) % items.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => (a <= 0 ? items.length - 1 : a - 1));
    } else if (e.key === 'Enter' && active >= 0) {
      e.preventDefault();
      pick(items[active]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  return (
    <div className="loc-box" ref={box}>
      <input
        id={id}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        autoComplete="off"
        maxLength={maxLength}
        value={value}
        placeholder="Ej.: Bogotá, Colombia"
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => items.length > 0 && setOpen(true)}
        onKeyDown={onKeyDown}
      />
      {loading && <small className="muted">Buscando sugerencias…</small>}
      {failed && (
        <small className="muted">
          No pudimos consultar las sugerencias. Puedes escribir la ubicación a mano.
        </small>
      )}
      {open && items.length > 0 && (
        <ul className="loc-list" id={listId} role="listbox">
          {items.map((label, i) => (
            <li
              key={label}
              role="option"
              aria-selected={i === active}
              className={i === active ? 'on' : ''}
              onMouseDown={(e) => {
                e.preventDefault();
                pick(label);
              }}
            >
              {label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}