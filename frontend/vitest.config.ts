import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      exclude: [
        // Build & Config
        'node_modules/',
        '.next/',
        'vitest.config.ts',
        'vitest.setup.ts',
        'next.config.ts',
        '**/*.d.ts',
        '**/*.config.*',
        '**/types/**',

        // Next.js App Router (routing, not business logic)
        'app/layout.tsx',              // Just providers wrapper
        'app/**/layout.tsx',           // All nested layouts
        'app/**/page.tsx',             // Page route files (test with E2E instead)
        'app/**/loading.tsx',          // Loading states
        'app/**/error.tsx',            // Error boundaries
        'app/**/not-found.tsx',        // 404 pages

        // Provider Wrappers (minimal logic)
        'lib/providers.tsx',           // Simple QueryClient + Auth wrapper

        // Test Utilities
        '__tests__/utils/**',          // Test helpers themselves

        // Backup Files
        '**/*-backup.tsx',             // Old backup files
        '**/*-backup.ts',
      ],
      // Optional: Set realistic thresholds (commented out for now)
      // statements: 40,
      // branches: 35,
      // functions: 40,
      // lines: 40,
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
})
