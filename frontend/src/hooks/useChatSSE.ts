import { useState, useCallback } from 'react';
import { useAuthStore } from '../store/useAuthStore';

export interface Source {
  text: string;
  page?: number;
  timestamp?: number;
  score?: number;
}

interface MessageMetadata {
  sources?: Source[];
}

export interface StreamMessage {
  role: 'user' | 'assistant';
  content: string;
  metadata?: MessageMetadata;
  isStreaming?: boolean;
}

export const useChatSSE = (fileId: string) => {
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const accessToken = useAuthStore((state) => state.accessToken);

  const sendMessage = useCallback(async (question: string, history: { role: string, content: string }[]) => {
    if (!question.trim()) return;

    // Add user message immediately
    const userMessage: StreamMessage = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMessage]);
    
    // Add empty assistant message that will be filled by stream
    const assistantMessage: StreamMessage = { 
      role: 'assistant', 
      content: '', 
      isStreaming: true 
    };
    setMessages((prev) => [...prev, assistantMessage]);
    
    setIsStreaming(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          file_id: fileId,
          question,
          history
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to connect to chat stream');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader available');

      let accumulatedContent = '';
      let finalMetadata: MessageMetadata | undefined;

      let isDone = false;
      while (!isDone) {
        const { done, value } = await reader.read();
        if (done) {
          isDone = true;
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === 'token' && data.content) {
                accumulatedContent += data.content;
              } else if (data.type === 'metadata' && data.sources) {
                finalMetadata = { sources: data.sources };
              }

              // Update the last message in state
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastIdx = newMessages.length - 1;
                newMessages[lastIdx] = {
                  ...newMessages[lastIdx],
                  content: accumulatedContent,
                  metadata: finalMetadata,
                };
                return newMessages;
              });
            } catch (e) {
              console.error('Error parsing SSE chunk', e, line);
            }
          }
        }
      }

      // Mark streaming as finished
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastIdx = newMessages.length - 1;
        newMessages[lastIdx] = {
          ...newMessages[lastIdx],
          isStreaming: false,
        };
        return newMessages;
      });

    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An error occurred during chat';
      setError(message);
      // Remove the failed assistant message
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsStreaming(false);
    }
  }, [fileId, accessToken]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    sendMessage,
    isStreaming,
    error,
    clearMessages
  };
};
