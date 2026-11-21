import { readFileSync, readdirSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'

const require = createRequire(import.meta.url)

function pdfSupportAssets() {
  return {
    name: 'pdf-support-assets',
    apply: 'build',
    generateBundle() {
      const packageDir = dirname(require.resolve('pdfjs-dist/package.json'))
      for (const directory of ['cmaps', 'iccs', 'standard_fonts', 'wasm']) {
        const sourceDir = join(packageDir, directory)
        for (const file of readdirSync(sourceDir, { withFileTypes: true })) {
          if (!file.isFile()) continue
          this.emitFile({
            type: 'asset',
            fileName: `assets/pdfjs/${directory}/${file.name}`,
            source: readFileSync(join(sourceDir, file.name))
          })
        }
      }
    }
  }
}

export default defineConfig({
  plugins: [
    tailwindcss(),
    svelte(),
    pdfSupportAssets(),
  ],
  server: {
    port: 4321,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:6234',
    },
  }
})
