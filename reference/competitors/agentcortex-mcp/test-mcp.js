#!/usr/bin/env node
import { spawn } from 'child_process';

// Test script to verify MCP server is working
console.log('Testing TaskMem MCP Server...');

const child = spawn('node', ['dist/src/index.js'], {
  stdio: ['pipe', 'pipe', 'pipe']
});

// Test tools/list request
const testRequest = {
  jsonrpc: "2.0",
  id: 1,
  method: "tools/list"
};

let output = '';
let errorOutput = '';

child.stdout.on('data', (data) => {
  output += data.toString();
});

child.stderr.on('data', (data) => {
  errorOutput += data.toString();
});

child.on('close', (code) => {
  console.log(`MCP server exited with code ${code}`);
  if (errorOutput) {
    console.error('Error output:', errorOutput);
  }
  if (output) {
    console.log('Server response:', output);
  }
});

// Send test request
child.stdin.write(JSON.stringify(testRequest) + '\n');

// Kill after 3 seconds
setTimeout(() => {
  child.kill();
  console.log('✅ MCP server test completed');
}, 3000);