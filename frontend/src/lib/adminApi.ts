import api from '@/lib/api';

export interface User {
  _id: string;
  name: string;
  email: string;
  phone?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Category {
  _id: string;
  name: string;
  description?: string;
  image?: string;
  parentCategory?: string;
  videoCount?: number;
  createdAt: string;
}

export interface Video {
  _id: string;
  title: string;
  description?: string;
  url: string;
  categoryId: string;
  categoryName?: string;
  views?: number;
  ratingCount?: number;
  avgRating?: number;
  createdAt: string;
}

export interface DashboardStats {
  totalUsers: number;
  totalCategories: number;
  totalVideos: number;
  totalRatings: number;
  avgRating: number;
  recentUsers: number;
  recentVideos: number;
  totalViews: number;
}

export interface Pagination {
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// User Management
export const getAllUsers = async (page = 1, limit = 10, search = '') => {
  const response = await api.get('/admin/users', {
    params: { page, limit, search },
  });
  return response.data;
};

export const createUser = async (data: Partial<User> & { password: string }) => {
  const response = await api.post('/admin/users', data);
  return response.data;
};

export const updateUser = async (id: string, data: Partial<User>) => {
  const response = await api.put(`/admin/users/${id}`, data);
  return response.data;
};

export const deleteUser = async (id: string) => {
  const response = await api.delete(`/admin/users/${id}`);
  return response.data;
};

// Analytics
export const getDashboardAnalytics = async () => {
  const response = await api.get('/admin/analytics/dashboard');
  return response.data;
};

export const getVideoAnalytics = async () => {
  const response = await api.get('/admin/analytics/videos');
  return response.data;
};

export const getUserEngagement = async () => {
  const response = await api.get('/admin/analytics/engagement');
  return response.data;
};

// Category Management
export const getCategoriesWithStats = async () => {
  const response = await api.get('/admin/categories/stats');
  return response.data;
};

export const getCategories = async () => {
  const response = await api.get('/category');
  return response.data;
};

export const deleteCategory = async (id: string) => {
  const response = await api.delete(`/admin/categories/${id}`);
  return response.data;
};

export const createCategory = async (data: FormData) => {
  const response = await api.post('/category', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const updateCategory = async (id: string, data: FormData) => {
  const response = await api.put(`/category/${id}`, data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// Video Management
export const getVideosWithStats = async (
  page = 1,
  limit = 10,
  categoryId = '',
  search = ''
) => {
  const response = await api.get('/admin/videos/stats', {
    params: { page, limit, categoryId, search },
  });
  return response.data;
};

export const deleteVideo = async (id: string) => {
  const response = await api.delete(`/admin/videos/${id}`);
  return response.data;
};

export const createVideo = async (data: FormData | any) => {
  const response = await api.post('/videos', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const updateVideo = async (id: string, data: FormData | any) => {
  const response = await api.put(`/videos/${id}`, data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// Feedback
export const getAllFeedback = async (page = 1, limit = 10) => {
  const response = await api.get('/admin/feedback', {
    params: { page, limit },
  });
  return response.data;
};

// Auth
export const login = async (email: string, password: string) => {
  const response = await api.post('/auth/login', { email, password });
  return response.data;
};

export const getProfile = async () => {
  const response = await api.get('/auth/profile');
  return response.data;
};

export const updateProfile = async (data: Partial<User>) => {
  const response = await api.put('/auth/profile', data);
  return response.data;
};
