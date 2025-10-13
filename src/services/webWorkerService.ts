/**
 * Web Worker Service
 * 
 * Manages Web Worker communication for:
 * - Heavy computation offloading
 * - Non-blocking data processing
 */

class WebWorkerService {
  private worker: Worker | null = null;
  private messageId = 0;
  private pendingMessages: Map<number, {
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = new Map();

  constructor() {
    this.initializeWorker();
  }

  private initializeWorker() {
    try {
      this.worker = new Worker(
        new URL('../workers/heavyComputation.worker.ts', import.meta.url),
        { type: 'module' }
      );

      this.worker.addEventListener('message', (event) => {
        const { type, result, error, duration } = event.data;
        
        if (error) {
          console.error('Worker error:', error);
          this.pendingMessages.forEach(({ reject }) => reject(error));
          this.pendingMessages.clear();
        } else {
          console.log(`Worker completed ${type} in ${duration.toFixed(2)}ms`);
          this.pendingMessages.forEach(({ resolve }) => resolve(result));
          this.pendingMessages.clear();
        }
      });

      this.worker.addEventListener('error', (error) => {
        console.error('Worker error:', error);
        this.pendingMessages.forEach(({ reject }) => reject(error));
        this.pendingMessages.clear();
      });
    } catch (error) {
      console.error('Failed to initialize Web Worker:', error);
    }
  }

  /**
   * Execute computation in Web Worker
   */
  async executeComputation<T>(
    type: 'process_data' | 'calculate_embeddings' | 'transform',
    payload: any
  ): Promise<T> {
    if (!this.worker) {
      throw new Error('Web Worker not initialized');
    }

    return new Promise((resolve, reject) => {
      const id = this.messageId++;
      this.pendingMessages.set(id, { resolve, reject });

      this.worker!.postMessage({ type, payload });

      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.pendingMessages.has(id)) {
          this.pendingMessages.delete(id);
          reject(new Error('Worker timeout'));
        }
      }, 30000);
    });
  }

  /**
   * Terminate worker
   */
  terminate() {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
      this.pendingMessages.clear();
    }
  }
}

// Singleton instance
export const webWorkerService = new WebWorkerService();

