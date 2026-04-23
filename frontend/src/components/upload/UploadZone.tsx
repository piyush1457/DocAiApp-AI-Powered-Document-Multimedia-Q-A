import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';
import { api } from '../../api/axios';

interface UploadZoneProps {
  onUploadSuccess: () => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (selectedFile: File) => {
    setError(null);
    const validTypes = ['application/pdf', 'audio/mpeg', 'video/mp4', 'audio/wav', 'audio/x-m4a', 'video/webm'];
    
    if (!validTypes.includes(selectedFile.type)) {
      setError('Invalid file type. Supported formats: PDF, MP3, MP4, WAV, M4A, WEBM');
      setFile(null);
      return;
    }

    if (selectedFile.size > 500 * 1024 * 1024) { // 500MB
      setError('File size exceeds 500MB limit');
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setFile(null);
      onUploadSuccess();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to upload file');
      } else {
        setError('An unexpected error occurred during upload.');
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="w-full">
      <div
        className={cn(
          "relative border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-200 ease-in-out",
          isDragging ? "border-accent bg-accent/5" : "border-border bg-panel hover:border-textSecondary",
          isUploading ? "opacity-50 pointer-events-none" : ""
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileChange}
          accept=".pdf,.mp3,.mp4,.wav,.m4a,.webm"
        />

        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="p-3 bg-background rounded-full border border-border">
            <UploadCloud className="w-8 h-8 text-textSecondary" />
          </div>
          
          <div>
            <p className="text-textPrimary font-medium text-lg">
              Drag and drop your file here
            </p>
            <p className="text-textSecondary text-sm mt-1">
              or click to browse from your computer
            </p>
            <p className="text-xs text-textSecondary mt-4">
              Supported formats: PDF, MP3, MP4, WAV, M4A, WEBM (Max 500MB)
            </p>
          </div>

          <Button 
            variant="secondary" 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="mt-2"
          >
            Select File
          </Button>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 flex items-center gap-2 text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-md">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {file && !error && (
        <div className="mt-4 p-4 flex items-center justify-between bg-panel border border-border rounded-lg">
          <div className="flex items-center gap-3 overflow-hidden">
            <File className="w-5 h-5 text-accent shrink-0" />
            <div className="truncate">
              <p className="text-sm font-medium text-textPrimary truncate">{file.name}</p>
              <p className="text-xs text-textSecondary">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button variant="ghost" size="sm" onClick={() => setFile(null)} disabled={isUploading}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleUpload} isLoading={isUploading}>
              Upload
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
