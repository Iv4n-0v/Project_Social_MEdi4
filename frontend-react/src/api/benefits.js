import { makeResource } from './resource';
import { request } from './http';

export const benefits = {
  ...makeResource('/benefits'),
  // Una sola llamada con ?ids=1,2,3
  findByIds: (ids) => request('GET', '/benefits', { query: { ids: ids.join(',') } }),
};
