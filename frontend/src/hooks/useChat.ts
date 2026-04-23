/**
 * Hook for managing chat state and interactions.
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { filesApi } from '../api/files';
import { ChatMessage } from '../types';

export const useChat = (fileId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const chatMutation = useMutation({
    mutationFn: (newMessages: ChatMessage[]) => filesApi.chat(fileId, newMessages),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.answer },
      ]);
    },
  });

  const sendMessage = async (content: string) => {
    const newMessages: ChatMessage[] = [...messages, { role: 'user', content }];
    setMessages(newMessages);
    chatMutation.mutate(newMessages);
  };

  return {
    messages,
    sendMessage,
    isLoading: chatMutation.isPending,
    error: chatMutation.error,
  };
};
