import { useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { homeFor } from '../utils';

export default function Home() {
  const { account, ready } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();

  // Regreso de Google/Facebook: la sesion ya quedo creada, se entra directo
  useEffect(() => {
    if (params.get('oauth') === 'ok' && ready && account) navigate(homeFor(account), { replace: true });
  }, [params, ready, account, navigate]);

  return (
    <section className="landing">
      <div className="hero">
        <h1>Descubre y da a conocer emprendimientos</h1>
        <p>
          Una plataforma que conecta a quienes emprenden con las personas que quieren conocerlos:
          perfiles claros, sus redes sociales en un solo lugar y cifras que tú puedes verificar.
        </p>
      </div>
      <div className="grid two">
        <article className="card choice">
          <h2>Quiero explorar</h2>
          <p>Navega el catálogo, busca por nombre o categoría y guarda tus favoritos.</p>
          <div className="row">
            <Link className="btn primary" to="/explorar">Ver emprendimientos</Link>
          </div>
        </article>
        <article className="card choice">
          <h2>Tengo un emprendimiento</h2>
          <p>Crea tu perfil, vincula tus redes y decide cuándo publicarlo.</p>
          <div className="row">
            <Link className="btn primary" to={account ? '/panel' : '/registro?rol=entrepreneur'}>
              {account ? 'Ir a mi panel' : 'Crear mi cuenta de emprendedor'}
            </Link>
            {!account && <Link className="btn" to="/ingresar?rol=entrepreneur">Ya tengo cuenta</Link>}
          </div>
        </article>
      </div>
      <p className="muted small">
        Los datos que ves son los que cada emprendedor publica. Si una cifra de seguidores es declarada
        a mano, se indica así.
      </p>
    </section>
  );
}
