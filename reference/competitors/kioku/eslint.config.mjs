import { defineConfig } from "eslint/config";
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import boundaries from "eslint-plugin-boundaries";

export default defineConfig(
  // Ignore patterns
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      "coverage/**",
      "*.config.js",
      "*.config.ts",
      "*.config.mjs",
      "**/*.config.js",
      "**/*.config.ts",
      "**/*.config.mjs",
      "bun.lockb",
      "index.ts",
      "test-yaml-debug.ts",
      "types/**/*.d.ts",
      "packages-backup/**",
      "**/dist/**",
      "packages/*/dist/**",
      "packages/ui/src/eslint.config.mjs",
    ],
  },

  // Base ESLint recommended rules
  eslint.configs.recommended,

  // TypeScript recommended + strict + stylistic
  ...tseslint.configs.recommended,
  ...tseslint.configs.strict,
  ...tseslint.configs.stylistic,

  // Global settings for all files
  {
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: ["./tsconfig.json", "./packages/*/tsconfig.json"],
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },

  // Architecture boundaries plugin
  {
    plugins: {
      boundaries,
    },
    settings: {
      "import/resolver": {
        typescript: {
          alwaysTryTypes: true,
          project: "./tsconfig.json",
        },
      },
      "boundaries/elements": [
        {
          type: "domain",
          pattern: "src/domain/**/*",
          mode: "folder",
        },
        {
          type: "application",
          pattern: "src/application/**/*",
          mode: "folder",
        },
        {
          type: "infrastructure",
          pattern: "src/infrastructure/**/*",
          mode: "folder",
        },
        {
          type: "shared",
          pattern: "src/shared/**/*",
          mode: "folder",
        },
      ],
    },
    rules: {
      // Architecture boundary enforcement
      "boundaries/element-types": [
        "error",
        {
          default: "disallow",
          message:
            "❌ Architecture violation: ${file.type} cannot import ${dependency.type}",
          rules: [
            // Domain (🟢) - Pure business logic, can import from itself but NO dependencies on other layers
            {
              from: ["domain"],
              allow: ["domain"],
              disallow: ["application", "infrastructure", "shared"],
              message:
                "❌ DOMAIN LAYER VIOLATION: Domain (🟢) must be pure with ZERO dependencies. Found import from ${dependency.type}. Move shared code to domain if needed.",
            },

            // Application (🟡) - Can depend on itself and Domain
            {
              from: ["application"],
              allow: ["application", "domain"],
              disallow: ["infrastructure", "shared"],
              message:
                "❌ APPLICATION LAYER VIOLATION: Application (🟡) can only import from Domain (🟢). Found import from ${dependency.type}. Move shared code to domain or use dependency injection.",
            },

            // Infrastructure (🔴) - Can depend on Application + Domain + itself
            {
              from: ["infrastructure"],
              allow: ["domain", "application", "shared", "infrastructure"],
              message:
                "✅ Infrastructure (🔴) can import from Domain, Application, Shared, and other Infrastructure",
            },

            // Shared - Can be imported by all layers
            {
              from: ["shared"],
              allow: ["domain"],
              disallow: ["application", "infrastructure"],
              message:
                "❌ SHARED LAYER VIOLATION: Shared utilities should only import from Domain (🟢) or be pure. Found import from ${dependency.type}.",
            },
          ],
        },
      ],

      // Package-level boundary enforcement
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@kioku/ui"],
              message:
                "❌ PACKAGE BOUNDARY VIOLATION: API package cannot import from UI package. Keep API independent of presentation layer.",
            },
            {
              group: ["@kioku/cli"],
              message:
                "❌ PACKAGE BOUNDARY VIOLATION: API package cannot import from CLI package. CLI depends on API, not vice versa.",
            },
          ],
        },
      ],

      // TypeScript strict rules
      "@typescript-eslint/explicit-function-return-type": [
        "error",
        {
          allowExpressions: true,
          allowTypedFunctionExpressions: true,
        },
      ],
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
        },
      ],
      "@typescript-eslint/consistent-type-imports": [
        "error",
        {
          prefer: "type-imports",
        },
      ],

      // Code quality rules
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "prefer-const": "error",
      "no-var": "error",
    },
  },

  // Test files - enforced quality gates with test-specific allowances
  {
    files: ["tests/**/*.ts", "**/*.test.ts", "**/*.spec.ts"],
    ignores: ["packages/*/tests/**/*"], // Ignore package test files for now
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: "./tsconfig.tests.json", // Enable TypeScript project for test files
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // ✅ Enforce type safety - same as src
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
        },
      ],
      "@typescript-eslint/consistent-type-imports": [
        "error",
        {
          prefer: "type-imports",
        },
      ],

      // ❌ Disable architecture boundaries - tests can import from any layer
      "boundaries/element-types": "off",

      // ✅ Allow console in tests - useful for debugging
      "no-console": "off",

      // ✅ Explicit return types on helper functions, but allow test functions
      "@typescript-eslint/explicit-function-return-type": [
        "error",
        {
          allowExpressions: true,
          allowTypedFunctionExpressions: true,
          allowHigherOrderFunctions: true,
          allowIIFEs: true,
        },
      ],

      // ✅ Allow floating promises in test setup/teardown
      "@typescript-eslint/no-floating-promises": "off",

      // ✅ Code quality rules - same as src
      "prefer-const": "error",
      "no-var": "error",
    },
  },

  // CLI command files - allow console output (it's the primary purpose)
  {
    files: ["src/infrastructure/cli/commands/*.ts", "packages/cli/src/**/*.ts"],
    rules: {
      "no-console": "off", // CLI commands output to console by design
    },
  },

  // CLI package - cannot import from UI
  {
    files: ["packages/cli/**/*.ts"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@kioku/ui", "@kioku/ui/*"],
              message:
                "❌ PACKAGE BOUNDARY VIOLATION: CLI package cannot import from UI package. Keep CLI and UI separate.",
            },
          ],
        },
      ],
    },
  },

  // UI package - cannot import from CLI
  {
    files: ["packages/ui/**/*.ts", "packages/ui/**/*.tsx"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@kioku/cli", "@kioku/cli/*"],
              message:
                "❌ PACKAGE BOUNDARY VIOLATION: UI package cannot import from CLI package. Keep CLI and UI separate.",
            },
          ],
        },
      ],
    },
  },

  // API package - cannot import from CLI or UI (most restrictive)
  {
    files: ["packages/api/**/*.ts"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@kioku/ui", "@kioku/ui/*"],
              message:
                "❌ PACKAGE BOUNDARY VIOLATION: API package cannot import from UI package. Keep API independent of presentation layer.",
            },
            {
              group: ["@kioku/cli", "@kioku/cli/*"],
              message:
                "❌ PACKAGE BOUNDARY VIOLATION: API package cannot import from CLI package. CLI depends on API, not vice versa.",
            },
          ],
        },
      ],
    },
  },
);
