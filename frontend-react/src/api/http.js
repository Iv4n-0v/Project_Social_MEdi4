import { ApiError, NetworkError } from './errors';

const BASE = '/api/v1';

// ---- sesion: el access token vive SOLO en memoria (no en localStorage) ----
let accessToken = null;
let onSessionLost = () => {};

export function setAccessToken(token) {
  accessToken = token || null;
}
export function getAccessToken() {
  return accessToken;
}
export function setSessionLostHandler(fn) {
  onSessionLost = fn || (() => {});
}

function parseDetail(body) {
  const d = body && body.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((e) => e.msg).join('; ');
  return '';
}

async function send(method, path, { body, query, auth = true } = {}) {
  const url = new URL(BASE + path, window.location.origin);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
    });
  }
  const init = { method, headers: { Accept: 'application/json' }, credentials: 'same-origin' };
  if (auth && accessToken) init.headers.Authorization = `Bearer ${accessToken}`;
  if (body instanceof FormData) {
    init.body = body;
  } else if (body !== undefined) {
    init.headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(url, init);
  } catch {
    throw new NetworkError();
  }
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  if (!res.ok) throw new ApiError(res.status, parseDetail(data), data);
  return data;
}

// ---- renovacion del access token ----
// Una sola renovacion a la vez: si varias peticiones reciben 401 juntas, comparten
// la misma promesa (evita rotar el refresh token varias veces en paralelo).
let refreshing = null;

export function refreshSession() {
  if (!refreshing) {
    refreshing = send('POST', '/auth/refresh', { auth: false })
      .then((s) => {
        setAccessToken(s.access_token);
        return s;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

export async function request(method, path, opts = {}) {
  try {
    return await send(method, path, opts);
  } catch (err) {
    const canRetry = err instanceof ApiError && err.status === 401 && opts.auth !== false && accessToken;
    if (!canRetry) throw err;
    try {
      await refreshSession();
    } catch (refreshErr) {
      if (refreshErr instanceof ApiError && refreshErr.status === 401) {
        // Puede ser una carrera con otra pestaña (que ya renovo la cookie): un reintento corto.
        await wait(300);
        try {
          await refreshSession();
        } catch {
          setAccessToken(null);
          onSessionLost();
          throw err;
        }
      } else {
        throw refreshErr;
      }
    }
    return send(method, path, opts);
  }
}

// Las llamadas de /auth/login, /register, etc. no deben intentar renovar nada
export const publicRequest = (method, path, opts = {}) => send(method, path, { ...opts, auth: false });
