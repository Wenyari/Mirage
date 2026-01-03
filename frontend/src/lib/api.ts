import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加 JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器：处理 401 和统一错误处理
api.interceptors.response.use(
  (response) => {
    // 直接返回 data 字段，简化调用
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 401 未授权，清除 token 并跳转登录
      localStorage.removeItem('auth_token');
      
      // 根据当前路径判断跳转到哪个登录页
      if (window.location.pathname.startsWith('/wadminw')) {
        window.location.href = '/wadminw/login';
      } else {
        window.location.href = '/login';
      }
    }

    // 统一错误格式
    const errorMessage = error.response?.data?.message || error.message || 'Network Error';

    return Promise.reject({
      message: errorMessage,
      status: error.response?.status,
      data: error.response?.data,
    });
  }
);

export default api;
