import React from 'react';
import { StreamMessage, Source } from '../../hooks/useChatSSE';
import { TimestampChip } from '../ui/TimestampChip';
import { cn } from '../../utils/cn';
import { usePlayerStore } from '../../store/playerStore';

interface ChatMessageProps {
  message: StreamMessage;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const setSeekToTime = usePlayerStore((state) => state.setSeekToTime);

  // Function to parse content and inject TimestampChips
  const renderContent = (content: string) => {
    // Matches patterns like [0:42], [1:23:45], 0:42, 1:23:45
    const timestampRegex = /(\[?\d{1,2}:\d{2}(?::\d{2})?\]?)/g;
    const parts = content.split(timestampRegex);

    return parts.map((part, i) => {
      const match = part.match(/\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?/);
      if (match) {
        const timeStr = match[1];
        const timeParts = timeStr.split(':').map(Number);
        let seconds = 0;
        if (timeParts.length === 3) {
          seconds = timeParts[0] * 3600 + timeParts[1] * 60 + timeParts[2];
        } else {
          seconds = timeParts[0] * 60 + timeParts[1];
        }
        
        return (
          <TimestampChip 
            key={i} 
            timeInSeconds={seconds} 
            formattedTime={timeStr} 
            className="mx-1"
          />
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  const handleSourceClick = (source: Source) => {
    if (source.page) {
      setSeekToTime(source.page);
    } else if (source.timestamp !== undefined) {
      setSeekToTime(source.timestamp);
    }
  };

  return (
    <div className={cn(
      "flex flex-col mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300",
      isUser ? "items-end" : "items-start"
    )}>
      <div className={cn(
        "max-w-[90%] px-4 py-3 rounded-lg text-sm leading-relaxed",
        isUser 
          ? "bg-accent text-white rounded-tr-none" 
          : "bg-background border border-border text-textPrimary rounded-tl-none"
      )}>
        <div className="whitespace-pre-wrap">
          {renderContent(message.content)}
          {message.isStreaming && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-accent/50 animate-pulse align-middle" />
          )}
        </div>
      </div>

      {!isUser && message.metadata?.sources && message.metadata.sources.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          <span className="text-[10px] text-textSecondary uppercase font-bold mr-1 flex items-center">Sources:</span>
          {message.metadata.sources.slice(0, 3).map((source, idx) => (
            <button 
              key={idx} 
              onClick={() => handleSourceClick(source)}
              className="px-2 py-1 bg-panel border border-border hover:border-accent/50 hover:bg-accent/10 rounded text-[10px] text-textSecondary hover:text-accent truncate max-w-[150px] transition-colors cursor-pointer"
              title={source.text}
            >
              {source.page ? `[Page ${source.page}]` : source.timestamp !== undefined ? `[▶ ${Math.floor(source.timestamp / 60)}:${(source.timestamp % 60).toString().padStart(2, '0')}]` : 'Segment'}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
