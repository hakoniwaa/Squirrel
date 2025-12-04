import winston from "winston";

export const logger = winston.createLogger({
  level: process.env.KIOKU_LOG_LEVEL || "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json(),
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
  ],
});

// Add file transport if .context directory exists
if (process.env.CONTEXT_DIR) {
  logger.add(
    new winston.transports.File({
      filename: `${process.env.CONTEXT_DIR}/kioku.log`,
    }),
  );
}
