import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { FileText, FileAudio, FileVideo, AlertCircle, MessageSquare, Trash2 } from 'lucide-react';
import { UploadZone } from '../components/upload/UploadZone';
import { useFiles, useDeleteFile, FileData } from '../hooks/useFiles';
import { Button } from '../components/ui/Button';
import { cn } from '../components/ui/Button';

const FileIcon = ({ type, className }: { type: string, className?: string }) => {
  const t = type?.toLowerCase();
  if (t === 'pdf') return <FileText className={className} />;
  if (['mp3', 'wav', 'm4a'].includes(t)) return <FileAudio className={className} />;
  if (['mp4', 'webm', 'mov'].includes(t)) return <FileVideo className={className} />;
  return <FileText className={className} />;
};

export const FileLibrary = () => {
  const { data: files, isLoading, isError } = useFiles();
  const deleteFile = useDeleteFile();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [showUpload, setShowUpload] = useState(false);

  const handleUploadSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['files'] });
    setShowUpload(false);
  };

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this file?')) {
      deleteFile.mutate(id);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto w-full">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-textPrimary">Your Files</h1>
          <p className="text-textSecondary mt-1">Upload and analyze your documents and multimedia</p>
        </div>
        <Button onClick={() => setShowUpload(!showUpload)}>
          {showUpload ? 'Cancel Upload' : 'Upload New File'}
        </Button>
      </div>

      {showUpload && (
        <div className="mb-10">
          <UploadZone onUploadSuccess={handleUploadSuccess} />
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center items-center h-40">
          <div className="animate-spin w-8 h-8 border-4 border-accent border-t-transparent rounded-full" />
        </div>
      ) : isError ? (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          Failed to load files. Please try refreshing the page.
        </div>
      ) : files?.length === 0 ? (
        <div className="text-center py-20 border border-border rounded-lg bg-panel">
          <FileText className="w-12 h-12 text-textSecondary mx-auto mb-4" />
          <h3 className="text-lg font-medium text-textPrimary">No files yet</h3>
          <p className="text-textSecondary mt-1 mb-6">Upload a document or media file to get started.</p>
          {!showUpload && (
            <Button onClick={() => setShowUpload(true)}>Upload File</Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {files?.map((file) => (
            <div 
              key={file.id} 
              className={cn(
                "flex flex-col bg-panel border border-border rounded-lg overflow-hidden transition-colors relative",
                file.status === 'ready' ? "hover:border-accent group cursor-pointer" : "opacity-80 hover:border-red-500/50 group"
              )}
              onClick={() => file.status === 'ready' && navigate(`/chat/${file.id}`)}
              role={file.status === 'ready' ? 'button' : 'article'}
              tabIndex={file.status === 'ready' ? 0 : -1}
            >
              <button 
                onClick={(e) => handleDelete(e, file.id)}
                className="absolute top-4 right-4 p-2 bg-red-500/10 text-red-400 rounded-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/20 z-10"
                title="Delete file"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              
              <div className="p-5 flex-1 pt-4 pr-14">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2 bg-background rounded border border-border">
                    <FileIcon type={file.file_type} className="w-6 h-6 text-accent" />
                  </div>
                  <div className="mt-1">
                    <StatusBadge status={file.status} />
                  </div>
                </div>
                
                <h3 className="font-medium text-textPrimary line-clamp-2" title={file.original_filename}>
                  {file.original_filename}
                </h3>
                <p className="text-xs text-textSecondary mt-2 uppercase">
                  {file.file_type} • {(file.file_size / 1024 / 1024).toFixed(2)} MB
                </p>
                <p className="text-xs text-textSecondary mt-1">
                  {new Date(file.created_at).toLocaleDateString()}
                </p>
              </div>
              
              {file.status === 'ready' && (
                <div className="bg-background px-5 py-3 border-t border-border flex items-center text-sm font-medium text-textSecondary group-hover:text-accent transition-colors">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Chat with file
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const StatusBadge = ({ status }: { status: FileData['status'] }) => {
  if (status === 'uploading') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
        Uploading
      </span>
    );
  }
  
  if (status === 'processing') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
        Processing
      </span>
    );
  }
  
  if (status === 'failed') {
    return (
      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20" title="Processing failed. Check backend logs for details.">
        Failed
      </span>
    );
  }
  
  return (
    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
      Ready
    </span>
  );
};
