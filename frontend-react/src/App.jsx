import { Link, NavLink, Route, Routes, useNavigate } from 'react-router-dom';
import CrudPage from './components/CrudPage';
import { RequireAuth, RequireRole } from './components/Guards';
import { useAuth } from './auth/AuthContext';
import Account from './pages/Account';
import Explore from './pages/Explore';
import Favorites from './pages/Favorites';
import Home from './pages/Home';
import Login from './pages/Login';
import MyVenture from './pages/MyVenture';
import Panel from './pages/Panel';
import { Forgot, Reset } from './pages/PasswordReset';
import Register from './pages/Register';
import VentureDetail from './pages/VentureDetail';

function Nav() {
  const { account, isLoggedIn, hasRole, logout, ready } = useAuth();
  const navigate = useNavigate();
  return (
    <header className="nav">
      <NavLink to="/" end className="brand">Project Social Media</NavLink>
      <nav aria-label="Principal">
        <NavLink to="/explorar">Explorar</NavLink>
        {isLoggedIn && <NavLink to="/favoritos">Favoritos</NavLink>}
        {hasRole('entrepreneur') && <NavLink to="/panel">Mi panel</NavLink>}
        {ready && isLoggedIn && (
          <>
            <NavLink to="/cuenta">{account.name.split(' ')[0]}</NavLink>
            <button
              type="button"
              className="linklike"
              onClick={async () => {
                await logout();
                navigate('/', { replace: true });
              }}
            >
              Salir
            </button>
          </>
        )}
        {ready && !isLoggedIn && (
          <>
            <NavLink to="/ingresar">Ingresar</NavLink>
            <Link className="nav-cta" to="/registro">Registrarme</Link>
          </>
        )}
      </nav>
    </header>
  );
}

const tool = (key) => (
  <RequireRole role="entrepreneur"><CrudPage resourceKey={key} /></RequireRole>
);

export default function App() {
  return (
    <>
      <Nav />
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/explorar" element={<Explore />} />
          <Route path="/emprendimiento/:id" element={<VentureDetail />} />
          <Route path="/ingresar" element={<Login />} />
          <Route path="/registro" element={<Register />} />
          <Route path="/recuperar" element={<Forgot />} />
          <Route path="/restablecer" element={<Reset />} />
          <Route path="/favoritos" element={<RequireAuth><Favorites /></RequireAuth>} />
          <Route path="/cuenta" element={<RequireAuth><Account /></RequireAuth>} />
          <Route path="/panel" element={<RequireRole role="entrepreneur"><Panel /></RequireRole>} />
          <Route path="/panel/emprendimiento" element={<RequireRole role="entrepreneur"><MyVenture /></RequireRole>} />
          <Route path="/usuarios" element={tool('users')} />
          <Route path="/metodologias" element={tool('methodologies')} />
          <Route path="/beneficios" element={tool('benefits')} />
          <Route path="/analisis" element={tool('analysis')} />
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<p>Página no encontrada. <Link to="/">Ir al inicio</Link></p>} />
        </Routes>
      </main>
    </>
  );
}
