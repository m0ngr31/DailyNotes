import {Requests} from './requests';

const AUTH_TOKEN = 'dn-token';

export function getToken() {
  if (typeof(Storage)) {
    return localStorage.getItem(AUTH_TOKEN);
  }

  return null;
}

export async function setToken(token: string) {
  if (typeof(Storage)) {
    localStorage.setItem(AUTH_TOKEN, token);
  }
}

export function clearToken() {
  if (typeof(Storage)) {
    localStorage.removeItem(AUTH_TOKEN)
  }
}

export async function updateJWT() {
  try {
    const res = await Requests.get('/refresh_jwt');

    if (!res || !res.data || !res.data.token) {
      throw new Error('no token');
    }

    setToken(res.data.token);
  } catch (e) {}
}