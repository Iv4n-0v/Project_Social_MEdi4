import { publicRequest, request } from './http';

export const authApi = {
  register: (body) => publicRequest('POST', '/auth/register', { body }),
  login: (body) => publicRequest('POST', '/auth/login', { body }),
  logout: () => publicRequest('POST', '/auth/logout'),
  me: () => request('GET', '/auth/me'),
  addRole: (role) => request('POST', '/auth/roles', { body: { role } }),
  providers: () => publicRequest('GET', '/auth/oauth/providers'),
  oauthStart: (provider, role) => publicRequest('GET', `/auth/oauth/${provider}/login`, { query: { role } }),
  forgot: (email) => publicRequest('POST', '/auth/password/forgot', { body: { email } }),
  reset: (token, new_password) => publicRequest('POST', '/auth/password/reset', { body: { token, new_password } }),
};
