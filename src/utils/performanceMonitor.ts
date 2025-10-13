/**
 * Performance Monitoring Utility
 * 
 * Tracks and reports:
 * - Component render times
 * - API call durations
 * - User interactions
 * - Core Web Vitals
 */

interface PerformanceEntry {
  name: string;
  duration: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

class PerformanceMonitor {
  private entries: PerformanceEntry[] = [];
  private maxEntries = 1000;

  /**
   * Mark performance measurement start
   */
  startMeasure(name: string): number {
    const startTime = performance.now();
    performance.mark(`${name}-start`);
    return startTime;
  }

  /**
   * Mark performance measurement end
   */
  endMeasure(name: string, metadata?: Record<string, any>): number {
    performance.mark(`${name}-end`);
    
    try {
      performance.measure(name, `${name}-start`, `${name}-end`);
      const measure = performance.getEntriesByName(name)[0];
      
      this.recordEntry({
        name,
        duration: measure.duration,
        timestamp: Date.now(),
        metadata
      });
      
      // Cleanup marks
      performance.clearMarks(`${name}-start`);
      performance.clearMarks(`${name}-end`);
      performance.clearMeasures(name);
      
      return measure.duration;
    } catch (error) {
      console.error('Performance measure failed:', error);
      return 0;
    }
  }

  /**
   * Record performance entry
   */
  private recordEntry(entry: PerformanceEntry): void {
    this.entries.push(entry);
    
    // Keep only last N entries
    if (this.entries.length > this.maxEntries) {
      this.entries = this.entries.slice(-this.maxEntries);
    }
  }

  /**
   * Get performance statistics
   */
  getStats(name?: string): {
    count: number;
    avg: number;
    min: number;
    max: number;
    p95: number;
  } {
    const filtered = name 
      ? this.entries.filter(e => e.name === name)
      : this.entries;
    
    if (filtered.length === 0) {
      return { count: 0, avg: 0, min: 0, max: 0, p95: 0 };
    }
    
    const durations = filtered.map(e => e.duration).sort((a, b) => a - b);
    const sum = durations.reduce((acc, val) => acc + val, 0);
    const p95Index = Math.floor(durations.length * 0.95);
    
    return {
      count: filtered.length,
      avg: sum / filtered.length,
      min: durations[0],
      max: durations[durations.length - 1],
      p95: durations[p95Index]
    };
  }

  /**
   * Monitor Core Web Vitals
   */
  monitorCoreWebVitals(): void {
    // Largest Contentful Paint
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      
      console.log('LCP:', lastEntry);
      this.recordEntry({
        name: 'LCP',
        duration: lastEntry.startTime,
        timestamp: Date.now()
      });
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // First Input Delay
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry: any) => {
        console.log('FID:', entry.processingStart - entry.startTime);
        this.recordEntry({
          name: 'FID',
          duration: entry.processingStart - entry.startTime,
          timestamp: Date.now()
        });
      });
    }).observe({ entryTypes: ['first-input'] });

    // Cumulative Layout Shift
    let clsValue = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as any[]) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      }
      
      console.log('CLS:', clsValue);
      this.recordEntry({
        name: 'CLS',
        duration: clsValue,
        timestamp: Date.now()
      });
    }).observe({ entryTypes: ['layout-shift'] });
  }

  /**
   * Export performance report
   */
  exportReport(): any {
    return {
      timestamp: Date.now(),
      entries: this.entries,
      stats: {
        overall: this.getStats(),
        byName: this.getUniqueNames().reduce((acc, name) => {
          acc[name] = this.getStats(name);
          return acc;
        }, {} as Record<string, any>)
      }
    };
  }

  private getUniqueNames(): string[] {
    return [...new Set(this.entries.map(e => e.name))];
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Initialize Core Web Vitals monitoring
if (typeof window !== 'undefined') {
  performanceMonitor.monitorCoreWebVitals();
}

