import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { friendlyMessage } from '../api/errors';
import { venturesApi } from '../api/ventures';
import { Loading } from '../components/Guards';
import { VentureCard } from '../components/venture';

export default function Favorites() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    venturesApi.favorites().then(setItems).catch((e) => setError(friendlyMessage(e)));
  }, []);

  // Quitar un favorito desde la tarjeta cambia el boton; la lista se actualiza al volver a entrar
  const visible = items;
  return (
    <section>
      <h2>Mis favoritos</h2>
      {error && <div className="alert error" role="alert">{error}</div>}
      {!items && !error && <Loading />}
      {visible && visible.length === 0 && (
        <div className="card">
          <p>Aún no has guardado emprendimientos.</p>
          <Link className="btn primary" to="/explorar">Explorar el catálogo</Link>
        </div>
      )}
      <div className="grid cards">
        {visible && visible.map((v) => <VentureCard key={v.id} venture={v} />)}
      </div>
    </section>
  );
}
