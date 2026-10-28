import { Link } from 'react-router-dom';

const cards = [
  ['/usuarios', 'Usuarios', 'Registra usuarios y las metodologías que aplican.'],
  ['/metodologias', 'Metodologías', 'Administra metodologías y sus beneficios.'],
  ['/beneficios', 'Beneficios', 'Catálogo de beneficios.'],
  ['/analisis', 'Análisis', 'Sector, alcance y tiempo en redes por usuario.'],
];

export default function Home() {
  return (
    <section>
      <h2>Project Social Media</h2>
      <p>Registra y controla las metodologías y redes sociales que usas con fines lucrativos.</p>
      <div className="grid">
        {cards.map(([to, title, text]) => (
          <Link key={to} to={to} className="card link-card">
            <h3>{title}</h3>
            <p>{text}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
