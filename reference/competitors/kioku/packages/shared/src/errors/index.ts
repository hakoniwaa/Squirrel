export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigError";
  }
}

export class StorageError extends Error {
  constructor(
    message: string,
    public override cause?: Error,
  ) {
    super(message);
    this.name = "StorageError";
  }
}

export class MCPError extends Error {
  constructor(
    message: string,
    public code?: number,
  ) {
    super(message);
    this.name = "MCPError";
  }
}

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}
