import { NavLink } from 'react-router-dom';

const SECTIONS = [
  ['/panel', 'Panel', true],
  ['/panel/emprendimiento', 'Mi emprendimiento'],
  ['/panel/redes', 'Mis redes'],
  ['/panel/estadisticas', 'Estadísticas'],
  ['/panel/vista-previa', 'Vista previa'],
  ['/panel/configuracion', 'Configuración'],
];

export default function PanelNav() {
  return (
    <nav className="panel-nav" aria-label="Secciones del panel">
      {SECTIONS.map(([to, label, end]) => (
        <NavLink key={to} to={to} end={end}>{label}</NavLink>
      ))}
    </nav>
  );
}

export function NoVenture() {
  return (
    <div className="card">
      <p>Primero crea tu emprendimiento para usar esta sección.</p>
      <NavLink className="btn primary" to="/panel/emprendimiento">Crear mi emprendimiento</NavLink>
    </div>
  );
}
