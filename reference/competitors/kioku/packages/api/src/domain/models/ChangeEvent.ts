/**
 * ChangeEvent - File system change detected by file watcher
 *
 * Purpose: Track file changes for real-time context updates.
 * Used by: File Watching feature (User Story 3)
 *
 * @module domain/models
 */

export enum FileEventType {
  ADD = 'add',
  CHANGE = 'change',
  UNLINK = 'unlink',
  RENAME = 'rename',
}

export interface ChangeEvent {
  id: string;                      // UUID v4
  eventType: FileEventType;
  filePath: string;                // Absolute path
  oldPath?: string;                // For renames
  timestamp: Date;
  processed: boolean;              // Has this been handled?
  error?: string;                  // Error message if processing failed
}
