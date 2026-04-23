import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/axios';

export interface FileData {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  original_filename: string;
  status: 'uploading' | 'processing' | 'ready' | 'failed';
  error_message?: string;
  created_at: string;
}

const fetchFiles = async (): Promise<FileData[]> => {
  const { data } = await api.get('/files/');
  return data;
};

export const useFiles = () => {
  return useQuery({
    queryKey: ['files'],
    queryFn: fetchFiles,
    refetchInterval: (query) => {
      const data = query.state.data as FileData[] | undefined;
      const isProcessing = data?.some(file => file.status === 'processing' || file.status === 'uploading');
      return isProcessing ? 3000 : false;
    },
  });
};

export const useDeleteFile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/files/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
    },
  });
};

const fetchFile = async (id: string): Promise<FileData> => {
  const { data } = await api.get(`/files/${id}`);
  return data;
};

export const useFile = (id: string) => {
  return useQuery({
    queryKey: ['file', id],
    queryFn: () => fetchFile(id),
    enabled: !!id,
  });
};
