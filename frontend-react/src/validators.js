// Reglas de nombre compartidas por el registro y el emprendimiento.
// Devuelven '' si el nombre es válido, o el mensaje de error en español.

export function normalizeName(raw) {
  return (raw || '').replace(/\s+/g, ' ').trim();
}

const PERSON = /^\p{L}[\p{L}\p{M}' .-]*$/u;
const VENTURE = /^[\p{L}\p{N}][\p{L}\p{M}\p{N}' .,&!+()\-_/]*$/u;

export function validateName(raw, kind = 'person') {
  const v = normalizeName(raw);
  if (!v) return 'El nombre es obligatorio.';
  if (v.length < 2) return 'El nombre debe tener al menos 2 caracteres.';
  if (v.length > 100) return 'El nombre no puede superar los 100 caracteres.';
  if (kind === 'person') {
    if (!PERSON.test(v)) return 'Usa solo letras, espacios, punto, apóstrofo o guion, y empieza con una letra.';
    return '';
  }
  if (!VENTURE.test(v)) return 'El nombre contiene símbolos no permitidos. Empieza con letra o número.';
  if (!/\p{L}/u.test(v)) return 'El nombre debe incluir al menos una letra.';
  return '';
}