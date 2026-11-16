import { svelte } from '@sveltejs/vite-plugin-svelte';
import type { Plugin } from 'vite';
import { defineConfig } from 'vitest/config';
import { META_CONTENT_SECURITY_POLICY, buildHeadersFile } from './config/security-headers';

// Build-only: the dev server needs inline styles and a websocket for hot reload.
function securityHeadersPlugin(): Plugin {
  return {
    name: 'alphabet-game:security-headers',
    apply: 'build',
    transformIndexHtml: () => [
      {
        tag: 'meta',
        attrs: { 'http-equiv': 'Content-Security-Policy', content: META_CONTENT_SECURITY_POLICY },
        injectTo: 'head-prepend',
      },
    ],
    generateBundle() {
      this.emitFile({ type: 'asset', fileName: '_headers', source: buildHeadersFile() });
    },
  };
}

export default defineConfig({
  plugins: [svelte(), securityHeadersPlugin()],
  build: {
    // data: URIs would violate img-src/font-src 'self'
    assetsInlineLimit: 0,
    sourcemap: false,
  },
  test: {
    include: ['tests/unit/**/*.test.ts'],
    environment: 'node',
    coverage: { include: ['src/core/**', 'config/**'] },
  },
});
