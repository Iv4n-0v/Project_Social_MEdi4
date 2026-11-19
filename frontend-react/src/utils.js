export const labelOf = (item) => item.name ?? item.sector ?? `#${item.id}`;

// Solo rutas internas: evita que ?next=https://sitio-malo.com sirva para redirigir fuera
export function safeNext(next) {
  return typeof next === 'string' && next.startsWith('/') && !next.startsWith('//') ? next : '';
}

export function homeFor(account) {
  return account && account.roles.includes('entrepreneur') ? '/panel' : '/explorar';
}
