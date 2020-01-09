import axios, {AxiosPromise} from 'axios';

import {getToken, clearToken} from './user';
import router from '../router/index';
import {Notifications} from './notifications';

axios.defaults.baseURL = '/api';

axios.interceptors.request.use(config => {
  // Get token
  const token = getToken();

  if (token) {
    config.headers.common['Authorization'] = `Bearer ${token}`;
  }

  return config;
}, (error) => {
  return Promise.reject(error);
});

axios.interceptors.response.use(res => res, async err => {
  if (err.response && (err.response.status === 403 || err.response.status === 401 || err.response.status === 422)) {
    // Logout
    clearToken();

    try {
      (Notifications.service as any).open({
        duration: 5000,
        message: 'Session expired. Logging out.',
        position: 'is-top',
        type: 'is-warning'
      });
    } catch (e) {}

    router.push({ name: 'Login' });
  }
  return Promise.reject(err);
});

export const Requests = {
  post: (url: string, data: any): AxiosPromise => {
    return axios.post(url, data);
  },

  get: (url: string, data?: any): AxiosPromise => {
    return axios.get(url, { params: data || {} });
  },

  put: (url: string, data: any): AxiosPromise => {
    return axios.put(url, data);
  }
};
