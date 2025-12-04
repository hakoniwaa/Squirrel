import { beforeAll, afterEach, afterAll } from 'vitest';

// Global test setup
beforeAll(() => {
  // Set test environment
  process.env.NODE_ENV = 'test';
});

afterEach(() => {
  // Clean up after each test
  // Reset any global state if needed
});

afterAll(() => {
  // Final cleanup
});