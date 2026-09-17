import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Send, ChevronLeft, Loader2, Info } from 'lucide-react';
import { ChatLayout } from '../components/chat/ChatLayout';
import { ChatMessage } from '../components/chat/ChatMessage';
import { MediaPlayer, MediaPlayerHandle } from '../components/chat/MediaPlayer';
import { SummaryPanel } from '../components/chat/SummaryPanel';
import { useChatSSE } from '../hooks/useChatSSE';
import { useFile } from '../hooks/useFiles';
import { api } from '../api/axios';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const ChatView = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const { data: file, isLoading: isLoadingFile } = useFile(fileId ?? '');
  const { messages, sendMessage, isStreaming, error } = useChatSSE(fileId ?? '');
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<MediaPlayerHandle>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    
    const history = messages.map(m => ({ role: m.role, content: m.content }));
    sendMessage(input, history);
    setInput('');
  };

  const [mediaUrl, setMediaUrl] = useState<string>('');
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [mediaLoading, setMediaLoading] = useState<boolean>(false);

  useEffect(() => {
    let currentUrl = '';
    let cancelled = false;
    const fetchMedia = async () => {
      if (!file) return;
      setMediaLoading(true);
      setMediaError(null);
      try {
        const response = await api.get(`/files/${file.id}/content`, {
          responseType: 'blob'
        });
        if (cancelled) return;
        // Backend may return JSON error with blob type on failure; check
        const contentType = response.headers['content-type'] || '';
        if (contentType.includes('application/json')) {
          const text = await (response.data as Blob).text();
          try {
            const json = JSON.parse(text);
            throw { response: { status: response.status, data: json } };
          } catch {
            // ignore
          }
        }
        currentUrl = URL.createObjectURL(response.data);
        setMediaUrl(currentUrl);
      } catch (err: any) {
        if (cancelled) return;
        const status = err?.response?.status;
        const detail = err?.response?.data
          ? (err.response.data instanceof Blob
              ? await err.response.data.text().then((t: string) => {
                  try {
                    return JSON.parse(t).detail || t;
                  } catch {
                    return t;
                  }
                }).catch(() => '')
              : err.response.data.detail || err.response.data.message || '')
          : err.message || '';
        console.error('Failed to fetch media content', err);
        if (status === 410) {
          setMediaError(
            detail || 'File expired from serverless ephemeral storage. Please re-upload the file.'
          );
        } else if (status === 404) {
          setMediaError(
            detail || 'Media not found. It may have expired on the serverless filesystem. Re-upload or enable Vercel Blob (BLOB_READ_WRITE_TOKEN).'
          );
        } else {
          setMediaError(detail || 'Failed to load media content.');
        }
      } finally {
        if (!cancelled) setMediaLoading(false);
      }
    };

    fetchMedia();

    return () => {
      cancelled = true;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [file]);

  if (isLoadingFile) {
    return (
      <div className="h-full flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    );
  }

  if (!file) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-background p-6 text-center">
        <h2 className="text-xl font-bold text-textPrimary mb-2">File not found</h2>
        <p className="text-textSecondary mb-6">The file you are looking for does not exist or has been deleted.</p>
        <Link to="/">
          <Button variant="outline">Back to Library</Button>
        </Link>
      </div>
    );
  }


  const fileType = (file?.file_type || '').toLowerCase();
  const isPDF = fileType === 'pdf';
  const isVideo = ['mp4', 'webm', 'mov'].includes(fileType);
  // isAudio not used for now as it maps to 'audio' by default in ternary below



  return (
    <div className="h-full flex flex-col overflow-hidden bg-background">
      {/* Sub-header */}
      <div className="h-12 border-b border-border bg-panel flex items-center px-4 justify-between shrink-0">
        <div className="flex items-center gap-3 overflow-hidden">
          <Link to="/" className="text-textSecondary hover:text-textPrimary">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <h2 className="text-sm font-medium text-textPrimary truncate" title={file.original_filename}>
            {file.original_filename}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase font-bold text-accent bg-accent/10 px-2 py-0.5 rounded border border-accent/20">
            {file.file_type}
          </span>
        </div>
      </div>

      <ChatLayout
        leftContent={
          <div className="h-full flex flex-col p-4 lg:p-6">
            {mediaError ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 bg-panel rounded-lg border border-border">
                <div className="p-3 bg-red-400/10 rounded-full mb-3">
                  <Info className="w-6 h-6 text-red-400" />
                </div>
                <h3 className="text-textPrimary font-medium mb-1">Media unavailable</h3>
                <p className="text-textSecondary text-xs max-w-sm mb-4">{mediaError}</p>
                <Link to="/">
                  <Button variant="outline" size="sm">Back to Library & re-upload</Button>
                </Link>
                {mediaError.includes('BLOB_READ_WRITE_TOKEN') && (
                  <p className="text-[10px] text-textSecondary mt-3 max-w-sm">
                    Add a Vercel Blob store: Vercel Dashboard → Storage → Create Blob Store → Connect to project → redeploy.
                  </p>
                )}
              </div>
            ) : mediaUrl ? (
              <MediaPlayer 
                ref={playerRef}
                src={mediaUrl} 
                type={isPDF ? 'pdf' : (isVideo ? 'video' : 'audio')} 
                className="flex-1"
              />
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-accent" />
              </div>
            )}
          </div>
        }
        rightContent={
          <div className="flex flex-col h-full overflow-hidden">
            {/* Summary Area */}
            <SummaryPanel fileId={file.id} />
            
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 lg:p-6 custom-scrollbar">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                  <div className="p-4 bg-accent/5 rounded-full mb-4">
                    <Info className="w-8 h-8 text-accent/50" />
                  </div>
                  <h3 className="text-textPrimary font-medium mb-1">Ask anything about this {file.file_type}</h3>
                  <p className="text-textSecondary text-xs">
                    I can help you summarize, find specific information, or explain concepts.
                  </p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <ChatMessage key={idx} message={msg} />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-panel border-t border-border">
              {error && (
                <div className="mb-3 p-2 text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded">
                  {error}
                </div>
              )}
              <form onSubmit={handleSend} className="relative flex items-center gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question..."
                  className="pr-12 bg-background"
                  disabled={isStreaming}
                />
                <Button 
                  type="submit" 
                  size="sm" 
                  className="absolute right-1 h-8 w-8 p-0"
                  disabled={!input.trim() || isStreaming}
                >
                  {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
              </form>
              <p className="text-[10px] text-textSecondary mt-2 text-center">
                AI may generate inaccurate information. Check important facts.
              </p>
            </div>
          </div>
        }
      />
    </div>
  );
};
