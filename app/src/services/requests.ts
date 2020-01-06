import axios, {AxiosPromise} from 'axios';

axios.defaults.baseURL = '/api';

axios.interceptors.request.use(config => {
  // Get token

  const token = null;

  if (token) {
    config.headers.common['Authorization'] = `Bearer ${token}`;
  }

  return config;
}, (error) => {
  return Promise.reject(error);
});

axios.interceptors.response.use(res => res, async err => {
  if (err.response && err.response.status === 403) {
    // Logout
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
