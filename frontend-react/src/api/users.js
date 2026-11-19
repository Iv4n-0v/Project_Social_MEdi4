import { makeResource } from './resource';
import { request } from './http';

export const users = {
  ...makeResource('/users'),
  setImage: (id, file) => {
    const form = new FormData();
    form.append('img', file);
    return request('PUT', `/users/${id}/image`, { body: form });
  },
};
