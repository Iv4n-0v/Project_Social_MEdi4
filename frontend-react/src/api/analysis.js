import { makeResource } from './resource';
import { request } from './http';

export const analysis = {
  ...makeResource('/analysis'),
  byUser: (userId) => request('GET', '/analysis', { query: { user_id: userId } }),
};
