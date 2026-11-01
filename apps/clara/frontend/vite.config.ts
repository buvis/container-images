import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [
    tailwindcss(),
    // SvelteKit 3 reads its config here; svelte.config.js is no longer supported.
    sveltekit({
      preprocess: vitePreprocess(),
      adapter: adapter({ fallback: '200.html' }),
      alias: {
        $api: 'src/lib/api',
        $state: 'src/lib/state',
        $components: 'src/lib/components',
        $tests: 'src/tests'
      }
    })
  ],
  test: {
    environment: 'jsdom',
    setupFiles: ['src/tests/setup.ts'],
    include: ['src/**/*.test.ts', 'src/**/*.svelte.test.ts'],
    globals: true
  },
  resolve: process.env.VITEST
    ? { conditions: ['browser'] }
    : undefined,
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
