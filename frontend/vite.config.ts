import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	base: '/static/',
	plugins: [svelte()],
	build: {
		outDir: 'dist',
		rollupOptions: {
			output: {
				manualChunks: undefined,
				entryFileNames: 'app.js',
				chunkFileNames: 'app.js',
				assetFileNames: 'app.[ext]'
			}
		}
	}
});
