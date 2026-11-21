// Caso 4 (parte A): comprueba el limite de /register del gateway (10 solicitudes por minuto).
// Envia cuerpos INVALIDOS a proposito: pasan por el limitador pero no crean cuentas.
//   Esperado: las primeras 10 -> 422 (validacion) y el resto -> 503 (limitador de KrakenD).
// ATENCION: el limite es global por endpoint; durante ~1 minuto nadie podra registrarse de verdad.
//
// Uso:  k6 run -e BASE_URL=https://project-social-media.tail41abfa.ts.net/api/v1 registro-limite.js
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const BASE = __ENV.BASE_URL || 'http://localhost:8080/api/v1';
const r422 = new Counter('resp_422_validacion');
const r503 = new Counter('resp_503_limitador');
const r429 = new Counter('resp_429');
const otros = new Counter('resp_otros');

export const options = {
  vus: 1,
  iterations: 30,
  thresholds: {
    resp_503_limitador: ['count>0'],   // el limitador debe haber actuado
    resp_otros: ['count==0'],          // nada inesperado (500, 200, etc.)
  },
};

export default function () {
  const res = http.post(`${BASE}/auth/register`, '{}', {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'POST /auth/register' },
  });
  if (res.status === 422) r422.add(1);
  else if (res.status === 503) r503.add(1);
  else if (res.status === 429) r429.add(1);
  else otros.add(1);
  check(res, { 'respuesta 422, 429 o 503': (r) => [422, 429, 503].includes(r.status) });
}

http.setResponseCallback(http.expectedStatuses(422, 429, 503));
