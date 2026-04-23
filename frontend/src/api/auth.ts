/**
 * API client for authentication operations.
 */

import apiClient from './client';
import { User, Token } from '../types';

export const authApi = {
  login: async (formData: FormData): Promise<Token> => {
    const { data } = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return data;
  },

  register: async (userData: any): Promise<User> => {
    const { data } = await apiClient.post('/auth/register', userData);
    return data;
  },

  refresh: async (token: string): Promise<Token> => {
    const { data } = await apiClient.post('/auth/refresh', { token });
    return data;
  },
};
