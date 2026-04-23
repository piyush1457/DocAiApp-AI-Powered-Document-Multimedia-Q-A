import React, { useRef, useEffect, useState, useImperativeHandle, forwardRef, useMemo } from 'react';
import { Play, Pause, Volume2, VolumeX, RotateCcw, RotateCw, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import { Button } from '../ui/Button';
import { cn } from '../ui/Button';
import { usePlayerStore } from '../../store/playerStore';

// Initialize PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

interface MediaPlayerProps {
  src: string;
  type: 'pdf' | 'audio' | 'video';
  className?: string;
}

export interface MediaPlayerHandle {
  seekTo: (time: number) => void;
}

export const MediaPlayer = forwardRef<MediaPlayerHandle, MediaPlayerProps>(({ src, type, className }, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);

  // PDF specific state
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [pdfScale, setPdfScale] = useState<number>(1.2);

  const seekToTime = usePlayerStore((state) => state.seekToTime);
  const clearSeekToTime = usePlayerStore((state) => state.clearSeekToTime);

  const activeRef = type === 'video' ? videoRef : audioRef;

  useImperativeHandle(ref, () => ({
    seekTo: (time: number) => {
      if (type === 'pdf') {
        setPageNumber(Math.max(1, Math.min(time, numPages || Infinity)));
      } else if (activeRef.current) {
        activeRef.current.currentTime = time;
      }
    }
  }));

  useEffect(() => {
    if (seekToTime !== null) {
      if (type === 'pdf') {
        // Assume seekToTime is page number for PDFs
        setPageNumber(Math.max(1, Math.min(seekToTime, numPages || Infinity)));
      } else if (activeRef.current) {
        activeRef.current.currentTime = seekToTime;
        activeRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
      clearSeekToTime();
    }
  }, [seekToTime, activeRef, clearSeekToTime, type, numPages]);

  // Sync volume and mute state
  useEffect(() => {
    if (activeRef.current) {
      activeRef.current.volume = isMuted ? 0 : volume;
      activeRef.current.muted = isMuted;
    }
  }, [volume, isMuted, activeRef]);

  const togglePlay = () => {
    if (activeRef.current) {
      if (isPlaying) {
        activeRef.current.pause();
      } else {
        activeRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (activeRef.current) {
      setCurrentTime(activeRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (activeRef.current) {
      setDuration(activeRef.current.duration);
    }
  };

  const formatTime = (time: number) => {
    if (isNaN(time)) return '0:00';
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (activeRef.current) {
      activeRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const skip = (seconds: number) => {
    if (activeRef.current) {
      activeRef.current.currentTime += seconds;
    }
  };

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    setPageNumber(1);
  }

  const changePage = (offset: number) => {
    setPageNumber(prevPageNumber => 
      Math.max(1, Math.min(prevPageNumber + offset, numPages || 1))
    );
  };

  // PDF.js worker options configuration ensures it uses a web worker for parsing.
  // Memoize options if needed, but defaults are usually fine.

  if (type === 'pdf') {
    return (
      <div className={cn("w-full h-full bg-panel rounded-lg border border-border flex flex-col overflow-hidden", className)}>
        {/* PDF Controls */}
        <div className="h-12 border-b border-border bg-background flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-2">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => changePage(-1)} 
              disabled={pageNumber <= 1}
              className="h-8 w-8 p-0"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm font-medium text-textPrimary min-w-[80px] text-center">
              Page {pageNumber} of {numPages || '-'}
            </span>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => changePage(1)} 
              disabled={pageNumber >= numPages}
              className="h-8 w-8 p-0"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setPdfScale(s => Math.max(0.5, s - 0.2))} className="text-xs px-2 h-8">-</Button>
            <span className="text-xs text-textSecondary">{Math.round(pdfScale * 100)}%</span>
            <Button variant="ghost" size="sm" onClick={() => setPdfScale(s => Math.min(3, s + 0.2))} className="text-xs px-2 h-8">+</Button>
          </div>
        </div>

        {/* PDF Viewer */}
        <div className="flex-1 overflow-y-auto bg-black/5 flex justify-center custom-scrollbar relative min-h-0 h-full">
          <Document
            file={src}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="flex flex-col items-center justify-center h-full text-textSecondary pt-20">
                <Loader2 className="w-8 h-8 animate-spin mb-4 text-accent" />
                <p>Loading PDF...</p>
              </div>
            }
            className="flex flex-col items-center py-6"
            error={
              <div className="text-red-400 p-4 pt-20 text-center">Failed to load PDF.</div>
            }
          >
            <Page 
              pageNumber={pageNumber} 
              scale={pdfScale}
              className="shadow-2xl bg-white"
              renderTextLayer={false}
              renderAnnotationLayer={false}
              loading={<div className="animate-pulse w-[600px] h-[800px] bg-white shadow-xl" />}
            />
          </Document>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("w-full h-full bg-panel rounded-xl border border-border overflow-hidden flex flex-col min-h-0", className)}>
      {/* Media Display Area */}
      <div className="relative flex-1 bg-black flex items-center justify-center min-h-0 overflow-hidden">
        {type === 'video' ? (
          <video
            ref={videoRef}
            src={src}
            className="max-h-full max-w-full object-contain"
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onClick={togglePlay}
          />
        ) : (
          <audio
            ref={audioRef}
            src={src}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
          />
        )}
        
        {type === 'audio' && (
          <div className="flex flex-col items-center gap-4 py-20">
            <div className="w-20 h-20 bg-accent/10 rounded-full flex items-center justify-center border border-accent/20">
               <Volume2 className="w-8 h-8 text-accent" />
            </div>
            <span className="text-textSecondary text-sm font-medium">Audio Playback</span>
          </div>
        )}
      </div>

      {/* Controls Area - Fixed Height to ensure visibility */}
      <div className="bg-panel border-t border-border p-4 sm:p-5 space-y-4 shrink-0 z-10 shadow-2xl">
        {/* Progress Bar */}
        <div className="flex items-center gap-4">
          <span className="text-[10px] font-mono text-textSecondary w-10 text-right">{formatTime(currentTime)}</span>
          <div className="flex-1 relative group h-6 flex items-center">
            <input
              type="range"
              min="0"
              max={duration || 0}
              step="0.1"
              value={currentTime}
              onChange={handleSeek}
              className="absolute w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-accent z-20"
            />
            <div 
              className="absolute h-1.5 bg-accent rounded-lg pointer-events-none z-10" 
              style={{ width: `${(currentTime / (duration || 1)) * 100}%` }}
            />
          </div>
          <span className="text-[10px] font-mono text-textSecondary w-10">{formatTime(duration)}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => skip(-5)} title="Rewind 5s" className="h-9 w-9 p-0 hover:bg-white/10">
              <RotateCcw className="w-5 h-5 text-textPrimary" />
            </Button>
            <Button 
              variant="secondary" 
              size="md" 
              onClick={togglePlay} 
              className="h-12 w-12 p-0 rounded-full bg-accent text-background hover:bg-accent/90 shadow-lg"
            >
              {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-0.5" />}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => skip(5)} title="Forward 5s" className="h-9 w-9 p-0 hover:bg-white/10">
              <RotateCw className="w-5 h-5 text-textPrimary" />
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => {
                if (activeRef.current) {
                  activeRef.current.pause();
                  activeRef.current.currentTime = 0;
                  setIsPlaying(false);
                }
              }} 
              title="Stop"
              className="h-9 w-9 p-0 hover:bg-white/10"
            >
              <div className="w-4 h-4 bg-textPrimary rounded-sm" />
            </Button>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => setIsMuted(!isMuted)} className="h-9 w-9 p-0 hover:bg-white/10">
              {isMuted || volume === 0 ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </Button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={isMuted ? 0 : volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="w-24 h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-accent"
            />
          </div>
        </div>
      </div>
    </div>
  );
});

MediaPlayer.displayName = 'MediaPlayer';
