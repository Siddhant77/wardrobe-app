/**
 * Configurable logging utility for the frontend.
 *
 * Supports different log levels:
 * - CRITICAL: Only failures (critical errors)
 * - ERROR: Errors and above
 * - WARNING: Warnings, errors, and above
 * - INFO: Informational messages and above (default)
 * - DEBUG: All messages including debug info
 *
 * Configuration:
 * - Set via localStorage: localStorage.setItem('logLevel', 'DEBUG')
 * - Syncs with backend log level (optional)
 * - Can be changed at runtime
 */

export enum LogLevel {
  CRITICAL = 'CRITICAL',
  ERROR = 'ERROR',
  WARNING = 'WARNING',
  INFO = 'INFO',
  DEBUG = 'DEBUG',
}

// Log level hierarchy for filtering
const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  [LogLevel.CRITICAL]: 0,
  [LogLevel.ERROR]: 1,
  [LogLevel.WARNING]: 2,
  [LogLevel.INFO]: 3,
  [LogLevel.DEBUG]: 4,
};

class FrontendLogger {
  private currentLevel: LogLevel;

  constructor() {
    // Initialize log level from localStorage or default to INFO
    const stored = this.getStoredLevel();
    this.currentLevel = stored || LogLevel.INFO;
  }

  /**
   * Get the stored log level from localStorage
   */
  private getStoredLevel(): LogLevel | null {
    if (typeof window === 'undefined') return null;
    const stored = localStorage.getItem('logLevel');
    if (stored && Object.values(LogLevel).includes(stored as LogLevel)) {
      return stored as LogLevel;
    }
    return null;
  }

  /**
   * Check if a message should be logged based on current level
   */
  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVEL_PRIORITY[level] <= LOG_LEVEL_PRIORITY[this.currentLevel];
  }

  /**
   * Format log message with timestamp and level
   */
  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level}] ${message}`;
  }

  /**
   * Get the console method for the log level
   */
  private getConsoleMethod(level: LogLevel): (...args: any[]) => void {
    switch (level) {
      case LogLevel.CRITICAL:
      case LogLevel.ERROR:
        return console.error;
      case LogLevel.WARNING:
        return console.warn;
      case LogLevel.INFO:
        return console.info;
      case LogLevel.DEBUG:
        return console.log;
      default:
        return console.log;
    }
  }

  /**
   * Internal log method
   */
  private log(level: LogLevel, message: string, data?: any): void {
    if (!this.shouldLog(level)) {
      return;
    }

    const formatted = this.formatMessage(level, message);
    const method = this.getConsoleMethod(level);

    if (data) {
      method(formatted, data);
    } else {
      method(formatted);
    }
  }

  /**
   * Log a debug message (most verbose)
   */
  debug(message: string, data?: any): void {
    this.log(LogLevel.DEBUG, message, data);
  }

  /**
   * Log an info message (default level)
   */
  info(message: string, data?: any): void {
    this.log(LogLevel.INFO, message, data);
  }

  /**
   * Log a warning message
   */
  warning(message: string, data?: any): void {
    this.log(LogLevel.WARNING, message, data);
  }

  /**
   * Log an error message
   */
  error(message: string, error?: Error | string | any): void {
    let errorStr = '';
    if (error instanceof Error) {
      errorStr = error.message;
    } else if (typeof error === 'string') {
      errorStr = error;
    } else if (error) {
      errorStr = JSON.stringify(error);
    }
    this.log(LogLevel.ERROR, message, errorStr ? { error: errorStr } : undefined);
  }

  /**
   * Log a critical/failure message (least verbose)
   */
  critical(message: string, error?: Error | string | any): void {
    let errorStr = '';
    if (error instanceof Error) {
      errorStr = error.message;
    } else if (typeof error === 'string') {
      errorStr = error;
    } else if (error) {
      errorStr = JSON.stringify(error);
    }
    this.log(LogLevel.CRITICAL, message, errorStr ? { error: errorStr } : undefined);
  }

  /**
   * Get the current log level
   */
  getLevel(): LogLevel {
    return this.currentLevel;
  }

  /**
   * Set the log level at runtime
   */
  setLevel(level: LogLevel): void {
    if (!Object.values(LogLevel).includes(level)) {
      console.warn(`Invalid log level: ${level}`);
      return;
    }
    this.currentLevel = level;
    if (typeof window !== 'undefined') {
      localStorage.setItem('logLevel', level);
    }
    this.info(`Log level changed to ${level}`);
  }

  /**
   * Sync frontend log level with backend
   */
  async syncWithBackend(backendUrl: string = 'http://localhost:8000'): Promise<void> {
    try {
      const response = await fetch(`${backendUrl}/config/log-level`);
      if (!response.ok) throw new Error(`Failed to fetch backend log level: ${response.statusText}`);
      const data = await response.json();
      const backendLevel = data.current_level as LogLevel;
      if (Object.values(LogLevel).includes(backendLevel)) {
        this.setLevel(backendLevel);
        this.info(`Synced log level with backend: ${backendLevel}`);
      }
    } catch (err) {
      this.warning('Failed to sync log level with backend', err);
    }
  }

  /**
   * Set backend log level via API
   */
  async setBackendLevel(level: LogLevel, backendUrl: string = 'http://localhost:8000'): Promise<boolean> {
    try {
      const response = await fetch(`${backendUrl}/config/log-level`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level }),
      });
      if (!response.ok) throw new Error(`Failed to set backend log level: ${response.statusText}`);
      this.info(`Backend log level set to ${level}`);
      return true;
    } catch (err) {
      this.error('Failed to set backend log level', err);
      return false;
    }
  }
}

// Export singleton instance
export const logger = new FrontendLogger();

// Export convenience functions
export const logDebug = (message: string, data?: any) => logger.debug(message, data);
export const logInfo = (message: string, data?: any) => logger.info(message, data);
export const logWarning = (message: string, data?: any) => logger.warning(message, data);
export const logError = (message: string, error?: Error | string | any) => logger.error(message, error);
export const logCritical = (message: string, error?: Error | string | any) => logger.critical(message, error);
