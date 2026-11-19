import { request } from './http';

// Adapter: cada recurso del gateway se usa con los mismos metodos
export function makeResource(path) {
  return {
    list: (query) => request('GET', path, { query }),
    get: (id) => request('GET', `${path}/${id}`),
    create: (body) => request('POST', path, { body }),
    update: (id, body) => request('PUT', `${path}/${id}`, { body }),
    remove: (id) => request('DELETE', `${path}/${id}`),
    restore: (id) => request('POST', `${path}/${id}/restore`),
    audits: (id) => request('GET', `${path}/${id}/audits`),
  };
}
