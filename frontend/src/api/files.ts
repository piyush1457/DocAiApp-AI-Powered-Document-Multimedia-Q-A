/**
 * API client for file-related operations.
 */

import apiClient from './client';
import { File, ChatMessage, ChatResponse, SummaryResponse } from '../types';

export const filesApi = {
  list: async (): Promise<File[]> => {
    const { data } = await apiClient.get('/files/');
    return data;
  },

  get: async (id: string): Promise<File> => {
    const { data } = await apiClient.get(`/files/${id}`);
    return data;
  },

  upload: async (file: File | any): Promise<File> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await apiClient.post('/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/files/${id}`);
  },

  chat: async (fileId: string, messages: ChatMessage[]): Promise<ChatResponse> => {
    const { data } = await apiClient.post('/chat/', {
      file_id: fileId,
      messages,
    });
    return data;
  },

  getSummary: async (fileId: string): Promise<SummaryResponse> => {
    const { data } = await apiClient.get(`/summary/${fileId}`);
    return data;
  },
};
