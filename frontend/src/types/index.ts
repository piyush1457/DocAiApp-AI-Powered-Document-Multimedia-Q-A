/**
 * TypeScript interfaces mirroring backend schemas.
 */

export type FileType = 'PDF' | 'MP3' | 'MP4' | 'WAV' | 'M4A' | 'WEBM';
export type FileStatus = 'uploading' | 'processing' | 'ready' | 'failed';

export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface File {
  id: string;
  filename: string;
  file_type: FileType;
  status: FileStatus;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  answer: string;
  context_used: string[];
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface SummaryResponse {
  summary: string;
}
