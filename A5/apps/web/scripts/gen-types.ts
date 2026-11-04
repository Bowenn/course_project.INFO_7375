// Generates src/types/scene.ts from the backend's JSON Schema (exported from the Pydantic models).
// Usage: `npm run gen:types` writes the file; `npm run check:types` fails if it is stale.
import { readFile, writeFile } from 'node:fs/promises'
import { compile } from 'json-schema-to-typescript'

const SCHEMA = new URL('../../../server/scene/scene.schema.json', import.meta.url)
const OUTPUT = new URL('../src/types/scene.ts', import.meta.url)
const BANNER = `/*
 * Generated from server/scene/scene.schema.json (Pydantic models in server/scene/schema.py).
 * Do not edit by hand: run \`make schemas\`.
 */`

const schema = JSON.parse(await readFile(SCHEMA, 'utf8'))
const source = await compile(schema, 'Scene', { bannerComment: BANNER })

if (process.argv.includes('--check')) {
  const current = await readFile(OUTPUT, 'utf8').catch(() => '')
  if (current !== source) {
    console.error('src/types/scene.ts is stale. Run `make schemas`.')
    process.exit(1)
  }
} else {
  await writeFile(OUTPUT, source)
  console.log('wrote src/types/scene.ts')
}
