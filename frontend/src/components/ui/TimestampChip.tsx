import React from 'react';
import { cn } from './Button';
import { usePlayerStore } from '../../store/playerStore';

interface TimestampChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  timeInSeconds: number;
  formattedTime: string;
}

export const TimestampChip: React.FC<TimestampChipProps> = ({ 
  timeInSeconds, 
  formattedTime, 
  className,
  ...props 
}) => {
  const setSeekToTime = usePlayerStore((state) => state.setSeekToTime);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    setSeekToTime(timeInSeconds);
    if (props.onClick) {
      props.onClick(e);
    }
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium",
        "bg-accent/20 text-accent hover:bg-accent hover:text-white transition-colors cursor-pointer",
        className
      )}
      title={`Seek to ${formattedTime}`}
      {...props}
    >
      ▶ {formattedTime}
    </button>
  );
};
