import { NavLink, Route, Routes } from 'react-router-dom';
import CrudPage from './components/CrudPage';
import Home from './pages/Home';
import Login from './pages/Login';

const links = [
  ['/usuarios', 'Usuarios'],
  ['/metodologias', 'Metodologías'],
  ['/beneficios', 'Beneficios'],
  ['/analisis', 'Análisis'],
];

export default function App() {
  return (
    <>
      <header className="nav">
        <NavLink to="/" className="brand">Project Social Media</NavLink>
        <nav>
          {links.map(([to, label]) => <NavLink key={to} to={to}>{label}</NavLink>)}
          <NavLink to="/login">Ingresar</NavLink>
        </nav>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/usuarios" element={<CrudPage resourceKey="users" />} />
          <Route path="/metodologias" element={<CrudPage resourceKey="methodologies" />} />
          <Route path="/beneficios" element={<CrudPage resourceKey="benefits" />} />
          <Route path="/analisis" element={<CrudPage resourceKey="analysis" />} />
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<p>Página no encontrada.</p>} />
        </Routes>
      </main>
    </>
  );
}
