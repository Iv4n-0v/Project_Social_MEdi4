// Caso 4 (parte B): carga de lectura sobre el catalogo publico, escalada al entorno gratuito.
// Umbrales del plan: p95 < 3 s y tasa de error < 1 %.
//
// Uso (prueba corta):   k6 run -e BASE_URL=... carga-lectura.js
// Mas fuerte:           k6 run -e BASE_URL=... -e VUS=100 -e HOLD=3m carga-lectura.js
// Mientras corre: en la VM `watch -n 2 kubectl top pods -n social-media`, en el portatil `docker stats`.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://localhost:8080/api/v1';
const VUS = parseInt(__ENV.VUS || '50');
const RAMP = __ENV.RAMP || '1m';
const HOLD = __ENV.HOLD || '2m';

export const options = {
  stages: [
    { duration: RAMP, target: VUS },   // rampa
    { duration: HOLD, target: VUS },   // sostenido
    { duration: '20s', target: 0 },    // bajada
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'],
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.99'],
  },
};

export function setup() {
  // toma un id real del catalogo para probar el detalle
  const res = http.get(`${BASE}/ventures?limit=5`);
  let id = null;
  try {
    const body = res.json();
    const list = Array.isArray(body) ? body : (body.items || body.data || body.ventures || []);
    if (list.length) id = list[0].id;
  } catch (e) { /* sin id: se omite el detalle */ }
  return { id };
}

export default function (data) {
  const calls = [
    ['GET /categories', `${BASE}/categories`],
    ['GET /ventures', `${BASE}/ventures?limit=12`],
    ['GET /ventures?q', `${BASE}/ventures?q=a&limit=12`],
  ];
  if (data.id) calls.push(['GET /ventures/{id}', `${BASE}/ventures/${data.id}`]);

  for (const [name, url] of calls) {
    const res = http.get(url, { tags: { name } });
    check(res, { [`${name} responde 200`]: (r) => r.status === 200 });
    sleep(Math.random() * 1.5 + 0.5);  // pausa de usuario real
  }
}
