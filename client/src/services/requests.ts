import axios, {AxiosPromise} from 'axios';

import {getToken, clearToken, setToken} from './user';
import router from '../router/index';
import {SharedBuefy} from './sharedBuefy';

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

axios.interceptors.response.use(res => {
  if (res && res.data && res.data.token) {
    setToken(res.data.token);
  }
  return res;
}, async err => {
  if (err.response && (err.response.status === 403 || err.response.status === 401 || err.response.status === 422)) {
    // Logout
    clearToken();

    try {
      (SharedBuefy.notifications as any).open({
        duration: 5000,
        message: 'Session expired. Logging out.',
        position: 'is-top',
        type: 'is-warning'
      });
      
      (SharedBuefy.activeDialog as any).close();
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
