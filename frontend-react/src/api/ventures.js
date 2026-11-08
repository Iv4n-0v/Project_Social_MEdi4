import { publicRequest, request } from './http';

export const venturesApi = {
  categories: () => publicRequest('GET', '/categories'),
  search: (query) => publicRequest('GET', '/ventures', { query }),
  get: (id) => publicRequest('GET', `/ventures/${id}`),
  // del emprendedor
  mine: () => request('GET', '/me/venture'),
  save: (body) => request('PUT', '/me/venture', { body }),
  remove: () => request('DELETE', '/me/venture'),
  restore: () => request('POST', '/me/venture/restore'),
  publish: () => request('POST', '/me/venture/publish'),
  unpublish: () => request('POST', '/me/venture/unpublish'),
  audits: () => request('GET', '/me/venture/audits'),
  setSocial: (platform, body) => request('PUT', `/me/venture/social/${platform}`, { body }),
  removeSocial: (platform) => request('DELETE', `/me/venture/social/${platform}`),
  // favoritos
  favorites: () => request('GET', '/me/favorites'),
  favoriteIds: () => request('GET', '/me/favorite-ids'),
  addFavorite: (id) => request('PUT', `/me/favorites/${id}`),
  removeFavorite: (id) => request('DELETE', `/me/favorites/${id}`),
};
