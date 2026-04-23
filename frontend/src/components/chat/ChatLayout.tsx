import React from 'react';

interface ChatLayoutProps {
  leftContent: React.ReactNode;
  rightContent: React.ReactNode;
}

export const ChatLayout: React.FC<ChatLayoutProps> = ({ leftContent, rightContent }) => {
  return (
    <div className="flex flex-col lg:flex-row h-full overflow-hidden bg-background">
      {/* Left Column: Media Viewer */}
      <div className="flex-1 min-h-[40vh] lg:min-h-0 border-b lg:border-b-0 lg:border-r border-border flex flex-col">
        <div className="flex-1 w-full relative min-h-0">
          {leftContent}
        </div>
      </div>

      {/* Right Column: Chat Interface */}
      <div className="w-full lg:w-[450px] xl:w-[500px] h-[60vh] lg:h-full bg-panel flex flex-col shrink-0">
        {rightContent}
      </div>
    </div>
  );
};
