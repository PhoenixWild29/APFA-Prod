import * as React from 'react';

interface LoadingIndicatorProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  fullScreen?: boolean;
  variant?: 'spinner' | 'dots' | 'bar';
}

export default function LoadingIndicator({
  message = 'Loading...',
  size = 'medium',
  fullScreen = false,
  variant = 'spinner',
}: LoadingIndicatorProps) {
  const LoadingVariant = {
    spinner: SpinnerLoader,
    dots: DotsLoader,
    bar: BarLoader,
  }[variant];

  const containerClass = fullScreen
    ? 'fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm'
    : 'flex flex-col items-center justify-center p-5';

  return (
    <div className={containerClass}>
      <LoadingVariant size={size} />
      {message && <p className="mt-4 text-sm text-muted-foreground">{message}</p>}
    </div>
  );
}

function SpinnerLoader({ size }: { size: string }) {
  const sizeMap = {
    small: 'h-5 w-5 border-2',
    medium: 'h-10 w-10 border-4',
    large: 'h-15 w-15 border-[6px]',
  };

  return (
    <div
      className={`animate-spin rounded-full border-gray-200 border-t-primary ${sizeMap[size as keyof typeof sizeMap]}`}
    />
  );
}

function DotsLoader({ size }: { size: string }) {
  const dotSize = {
    small: 'h-2 w-2',
    medium: 'h-3 w-3',
    large: 'h-4 w-4',
  };

  return (
    <div className="flex gap-2">
      <div
        className={`animate-bounce rounded-full bg-primary ${dotSize[size as keyof typeof dotSize]}`}
        style={{ animationDelay: '0ms' }}
      />
      <div
        className={`animate-bounce rounded-full bg-primary ${dotSize[size as keyof typeof dotSize]}`}
        style={{ animationDelay: '200ms' }}
      />
      <div
        className={`animate-bounce rounded-full bg-primary ${dotSize[size as keyof typeof dotSize]}`}
        style={{ animationDelay: '400ms' }}
      />
    </div>
  );
}

function BarLoader({ size }: { size: string }) {
  const height = {
    small: 'h-0.5',
    medium: 'h-1',
    large: 'h-1.5',
  };

  return (
    <div className={`w-48 overflow-hidden rounded-full bg-gray-200 ${height[size as keyof typeof height]}`}>
      <div className="h-full w-full origin-left animate-[slide_1.5s_ease-in-out_infinite] bg-primary" />
    </div>
  );
}

export function InlineLoading({ text = 'Loading' }: { text?: string }) {
  return (
    <span className="inline-block text-muted-foreground">
      {text}
      <span className="inline-block">
        <span className="animate-[fade_1.4s_infinite]">.</span>
        <span className="animate-[fade_1.4s_infinite_200ms]">.</span>
        <span className="animate-[fade_1.4s_infinite_400ms]">.</span>
      </span>
    </span>
  );
}

export function SkeletonLoader({
  width = '100%',
  height = '20px',
  count = 1,
}: {
  width?: string;
  height?: string;
  count?: number;
}) {
  return (
    <div style={{ width }}>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="animate-pulse rounded bg-gray-200"
          style={{
            height,
            marginBottom: count > 1 && index < count - 1 ? '12px' : '0',
          }}
        />
      ))}
    </div>
  );
}

