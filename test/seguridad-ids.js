// Casos 1 y 5: acceso a datos de otros usuarios / sin sesion o con token invalido.
// Los resultados esperados son rechazos (401/403/404), por eso se declaran como estados esperados.
//
// Uso minimo (sin tokens):
//   k6 run -e BASE_URL=... seguridad-ids.js
// Completo (tokens obtenidos con POST /auth/login de dos cuentas de prueba):
//   Automatico: el script inicia sesion solo con las credenciales de las cuentas de prueba.
//   k6 run -e BASE_URL=... -e EMAIL_A=prueba.a@... -e PASS_A=... -e EMAIL_V=prueba.v@... -e PASS_V=... -e ID_B=<id de un registro de usuarios de la cuenta B> seguridad-ids.js
//   (EMAIL_V/PASS_V es una cuenta con rol visitante; ambas son opcionales.)
//   Tambien acepta TOKEN_A / TOKEN_VISITOR ya obtenidos.
// No pegues contrasenas ni tokens reales en chats ni los subas a Git.
import http from 'k6/http';
import { check, group } from 'k6';

const BASE = __ENV.BASE_URL || 'http://localhost:8080/api/v1';
function login(email, pass) {
  if (!email || !pass) return '';
  const r = http.post(`${BASE}/auth/login`, JSON.stringify({ email, password: pass }),
    { headers: { 'Content-Type': 'application/json' } });
  try { return r.json('access_token') || ''; } catch (e) { return ''; }
}
const ID_B = __ENV.ID_B || '102';
const FAKE = 'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIn0.firma-alterada';

http.setResponseCallback(http.expectedStatuses(200, 401, 403, 404));
export const options = { vus: 1, iterations: 1, thresholds: { checks: ['rate==1'] } };

const auth = (t) => ({ headers: { Authorization: `Bearer ${t}` } });

export function setup() {
  return {
    tokenA: __ENV.TOKEN_A || login(__ENV.EMAIL_A, __ENV.PASS_A),
    tokenV: __ENV.TOKEN_VISITOR || login(__ENV.EMAIL_V, __ENV.PASS_V),
  };
}

export default function (data) {
  const TOKEN_A = data.tokenA;
  const TOKEN_VISITOR = data.tokenV;
  group('Caso 5: sin sesion o con token invalido', () => {
    check(http.get(`${BASE}/users/${ID_B}`), { 'GET /users/{id} sin token -> 401': (r) => r.status === 401 });
    check(http.get(`${BASE}/users`), { 'GET /users sin token -> 401': (r) => r.status === 401 });
    check(http.get(`${BASE}/auth/me`), { 'GET /auth/me sin token -> 401': (r) => r.status === 401 });
    check(http.get(`${BASE}/me/venture`), { 'GET /me/venture sin token -> 401': (r) => r.status === 401 });
    check(http.get(`${BASE}/users/${ID_B}`, auth(FAKE)), { 'token alterado -> 401': (r) => r.status === 401 });
  });

  if (TOKEN_VISITOR) {
    group('Caso 1: visitante no accede a rutas de emprendedor', () => {
      check(http.get(`${BASE}/users/${ID_B}`, auth(TOKEN_VISITOR)), { 'visitante en /users/{id} -> 403': (r) => r.status === 403 });
      check(http.get(`${BASE}/me/venture`, auth(TOKEN_VISITOR)), { 'visitante en /me/venture -> 403': (r) => r.status === 403 });
    });
  }

  if (TOKEN_A) {
    group('Caso 1: usuario A pide el id de B', () => {
      const r = http.get(`${BASE}/users/${ID_B}`, auth(TOKEN_A));
      check(r, {
        'recurso ajeno -> 403 o 404': (x) => x.status === 403 || x.status === 404,
        'no devuelve datos del usuario B': (x) => !String(x.body).includes('"email"'),
      });
    });
  }
}
