import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export default defineConfig({
	base: '/static/',
	plugins: [svelte()],
	resolve: {
		alias: {
			'$lib': path.resolve(__dirname, './src/lib'),
			'$mdr': path.resolve(__dirname, './src/lib/mdr')
		}
	},
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
