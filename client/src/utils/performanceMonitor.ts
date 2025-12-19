/**
 * Moniteur de performance pour identifier les goulots d'étranglement
 */

export class PerformanceMonitor {
  private static timers: Map<string, number> = new Map();
  private static logs: Array<{operation: string, duration: number, timestamp: number}> = [];

  static start(operation: string): void {
    this.timers.set(operation, performance.now());
    console.log(`⏱️ [PERF] START: ${operation}`);
  }

  static end(operation: string): number {
    const startTime = this.timers.get(operation);
    if (!startTime) {
      console.warn(`⚠️ [PERF] No start time for: ${operation}`);
      return 0;
    }

    const duration = performance.now() - startTime;
    const log = {
      operation,
      duration,
      timestamp: Date.now()
    };
    
    this.logs.push(log);
    this.timers.delete(operation);

    // Colorier selon la durée
    const color = duration < 100 ? '🟢' : duration < 500 ? '🟡' : '🔴';
    console.log(`${color} [PERF] END: ${operation} - ${duration.toFixed(2)}ms`);
    
    return duration;
  }

  static getReport(): string {
    const sorted = [...this.logs].sort((a, b) => b.duration - a.duration);
    const total = sorted.reduce((sum, log) => sum + log.duration, 0);
    
    let report = '\n📊 RAPPORT DE PERFORMANCE\n';
    report += '='.repeat(60) + '\n';
    sorted.slice(0, 10).forEach(log => {
      const percent = ((log.duration / total) * 100).toFixed(1);
      report += `${log.operation.padEnd(40)} ${log.duration.toFixed(2)}ms (${percent}%)\n`;
    });
    report += '='.repeat(60) + '\n';
    report += `TOTAL: ${total.toFixed(2)}ms\n`;
    
    return report;
  }

  static clear(): void {
    this.timers.clear();
    this.logs = [];
  }
}

// Export pour utilisation dans la console
(window as any).perfReport = () => console.log(PerformanceMonitor.getReport());
