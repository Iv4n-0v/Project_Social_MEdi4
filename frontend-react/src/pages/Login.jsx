const providers = ['Google', 'Instagram', 'Facebook', 'X'];

export default function Login() {
  return (
    <section className="card narrow">
      <h2>Iniciar sesión</h2>
      <p>La autenticación aún no está implementada. Estos botones son un marcador para el trabajo futuro.</p>
      <div className="stack">
        {providers.map((p) => (
          <button key={p} className="btn" disabled>Continuar con {p} (próximamente)</button>
        ))}
      </div>
    </section>
  );
}
