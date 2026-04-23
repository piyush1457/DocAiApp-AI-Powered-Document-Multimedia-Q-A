import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/axios';
import { ChevronDown, ChevronUp, FileText, Loader2, List, Clock } from 'lucide-react';
import { cn } from '../ui/Button';
import { usePlayerStore } from '../../store/playerStore';

interface ChapterMarker {
  title: string;
  start_time: number;
  end_time: number;
}

interface SummaryData {
  summary: string;
  key_topics: string[];
  word_count: number;
  chapter_markers?: ChapterMarker[];
}

interface SummaryPanelProps {
  fileId: string;
}

export const SummaryPanel = ({ fileId }: SummaryPanelProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const setSeekToTime = usePlayerStore((state) => state.setSeekToTime);

  const { data, isLoading, isError } = useQuery<SummaryData>({
    queryKey: ['summary', fileId],
    queryFn: async () => {
      const response = await api.get(`/summary/${fileId}`);
      return response.data;
    },
    enabled: isOpen,
    staleTime: Infinity,
  });

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-panel border-b border-border">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-background transition-colors focus:outline-none"
      >
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-accent" />
          <span className="font-medium text-textPrimary">Document Summary</span>
        </div>
        {isOpen ? <ChevronUp className="w-5 h-5 text-textSecondary" /> : <ChevronDown className="w-5 h-5 text-textSecondary" />}
      </button>

      {isOpen && (
        <div className="p-4 pt-0 border-t border-border bg-background/50">
          {isLoading ? (
            <div className="flex items-center justify-center p-6">
              <Loader2 className="w-6 h-6 animate-spin text-accent" />
            </div>
          ) : isError ? (
            <div className="text-red-400 p-4 text-sm bg-red-400/10 rounded-md">
              Failed to load summary.
            </div>
          ) : data ? (
            <div className="space-y-4 pt-4 animate-in fade-in slide-in-from-top-2 duration-200">
              <div>
                <p className="text-sm text-textPrimary leading-relaxed">
                  {data.summary}
                </p>
                <p className="text-xs text-textSecondary mt-2">
                  Word count: {data.word_count}
                </p>
              </div>

              {data.key_topics?.length > 0 && (
                <div>
                  <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase text-textSecondary mb-2">
                    <List className="w-3.5 h-3.5" /> Key Topics
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {data.key_topics.map((topic, idx) => (
                      <span key={idx} className="px-2 py-1 bg-accent/10 text-accent text-xs rounded-md border border-accent/20">
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {data.chapter_markers && data.chapter_markers.length > 0 && (
                <div>
                  <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase text-textSecondary mb-2">
                    <Clock className="w-3.5 h-3.5" /> Chapters
                  </h4>
                  <div className="space-y-2">
                    {data.chapter_markers.map((chapter, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSeekToTime(chapter.start_time)}
                        className="w-full flex items-center justify-between p-2 text-sm bg-panel hover:bg-accent/10 border border-border hover:border-accent/30 rounded-md transition-colors text-left"
                      >
                        <span className="text-textPrimary truncate mr-2">{chapter.title}</span>
                        <span className="text-xs font-mono text-accent shrink-0">
                          {formatTime(chapter.start_time)}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
