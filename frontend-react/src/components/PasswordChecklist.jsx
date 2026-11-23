// Lista en vivo de requisitos de la contraseña (solo guía en pantalla; la regla
// que valida el servidor es la longitud mínima, ver backend/auth/security.py).
export const PASSWORD_RULES = [
  { id: 'len', label: 'Al menos 8 caracteres', test: (p) => p.length >= 8 },
  { id: 'letter', label: 'Al menos una letra', test: (p) => /\p{L}/u.test(p) },
  { id: 'digit', label: 'Al menos un número (0-9)', test: (p) => /\d/.test(p) },
];

export const passwordOk = (p) => PASSWORD_RULES.every((r) => r.test(p));

export default function PasswordChecklist({ password }) {
  return (
    <div className="pw-rules-box">
      <small className="muted">La contraseña debe contener:</small>
      <ul className="pw-rules" aria-live="polite">
        {PASSWORD_RULES.map((r) => (
          <li key={r.id} className={r.test(password) ? 'ok' : ''}>
            {r.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
