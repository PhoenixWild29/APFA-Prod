/**
 * Reusable loading indicator component
 * Provides visual feedback during async operations
 */
import React from 'react';

/**
 * Loading indicator component
 * @param {object} props - Component props
 * @param {string} props.message - Loading message to display
 * @param {string} props.size - Size: 'small', 'medium', or 'large'
 * @param {boolean} props.fullScreen - Whether to display full screen
 * @param {string} props.variant - Variant: 'spinner', 'dots', or 'bar'
 */
export default function LoadingIndicator({
  message = 'Loading...',
  size = 'medium',
  fullScreen = false,
  variant = 'spinner',
}) {
  const LoadingVariant = {
    spinner: SpinnerLoader,
    dots: DotsLoader,
    bar: BarLoader,
  }[variant] || SpinnerLoader;
  
  const container = fullScreen ? styles.fullScreenContainer : styles.container;
  
  return (
    <div style={container}>
      <LoadingVariant size={size} />
      {message && <p style={styles.message}>{message}</p>}
    </div>
  );
}

/**
 * Spinner loading animation
 */
function SpinnerLoader({ size }) {
  const sizeStyles = {
    small: { width: '20px', height: '20px', borderWidth: '2px' },
    medium: { width: '40px', height: '40px', borderWidth: '4px' },
    large: { width: '60px', height: '60px', borderWidth: '6px' },
  };
  
  return <div style={{ ...styles.spinner, ...sizeStyles[size] }} />;
}

/**
 * Dots loading animation
 */
function DotsLoader({ size }) {
  const dotSize = {
    small: '8px',
    medium: '12px',
    large: '16px',
  }[size];
  
  return (
    <div style={styles.dotsContainer}>
      <div style={{ ...styles.dot, width: dotSize, height: dotSize }} />
      <div style={{ ...styles.dot, width: dotSize, height: dotSize, animationDelay: '0.2s' }} />
      <div style={{ ...styles.dot, width: dotSize, height: dotSize, animationDelay: '0.4s' }} />
    </div>
  );
}

/**
 * Bar loading animation
 */
function BarLoader({ size }) {
  const height = {
    small: '2px',
    medium: '4px',
    large: '6px',
  }[size];
  
  return (
    <div style={{ ...styles.barContainer, height }}>
      <div style={styles.bar} />
    </div>
  );
}

/**
 * Inline loading text
 * Minimal loading indicator for inline use
 */
export function InlineLoading({ text = 'Loading' }) {
  return (
    <span style={styles.inlineLoading}>
      {text}
      <span style={styles.inlineDots}>
        <span style={styles.inlineDot}>.</span>
        <span style={{ ...styles.inlineDot, animationDelay: '0.2s' }}>.</span>
        <span style={{ ...styles.inlineDot, animationDelay: '0.4s' }}>.</span>
      </span>
    </span>
  );
}

/**
 * Skeleton loader for content placeholders
 */
export function SkeletonLoader({ width = '100%', height = '20px', count = 1 }) {
  return (
    <div style={{ width }}>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          style={{
            ...styles.skeleton,
            height,
            marginBottom: count > 1 && index < count - 1 ? '12px' : '0',
          }}
        />
      ))}
    </div>
  );
}

/**
 * Styles
 */
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
  },
  fullScreenContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    zIndex: 9999,
  },
  message: {
    marginTop: '16px',
    fontSize: '14px',
    color: '#666',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  
  // Spinner styles
  spinner: {
    border: 'solid #f3f3f3',
    borderTop: 'solid #1976d2',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  
  // Dots styles
  dotsContainer: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  dot: {
    backgroundColor: '#1976d2',
    borderRadius: '50%',
    animation: 'bounce 1.4s infinite ease-in-out both',
  },
  
  // Bar styles
  barContainer: {
    width: '200px',
    backgroundColor: '#f3f3f3',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  bar: {
    width: '100%',
    height: '100%',
    backgroundColor: '#1976d2',
    animation: 'slide 1.5s infinite ease-in-out',
  },
  
  // Inline loading styles
  inlineLoading: {
    display: 'inline-block',
    color: '#666',
  },
  inlineDots: {
    display: 'inline-block',
  },
  inlineDot: {
    animation: 'fade 1.4s infinite',
    opacity: 0,
  },
  
  // Skeleton styles
  skeleton: {
    backgroundColor: '#e0e0e0',
    borderRadius: '4px',
    animation: 'pulse 1.5s ease-in-out infinite',
  },
};

// Inject CSS animations
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    
    @keyframes bounce {
      0%, 80%, 100% { 
        transform: scale(0);
      }
      40% { 
        transform: scale(1);
      }
    }
    
    @keyframes slide {
      0% {
        transform: translateX(-100%);
      }
      100% {
        transform: translateX(100%);
      }
    }
    
    @keyframes fade {
      0%, 80%, 100% {
        opacity: 0;
      }
      40% {
        opacity: 1;
      }
    }
    
    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.5;
      }
    }
  `;
  document.head.appendChild(styleSheet);
}

