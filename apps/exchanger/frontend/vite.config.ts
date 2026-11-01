import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		// SvelteKit 3 reads its config here; svelte.config.js is no longer supported.
		sveltekit({
			adapter: adapter({
				pages: '../app/static',
				assets: '../app/static',
				fallback: 'index.html'
			})
		})
	],
	server: {
		proxy: {
			'/api': {
				target: 'http://127.0.0.1:8000',
				changeOrigin: true,
				ws: true
			}
		}
	}
});
