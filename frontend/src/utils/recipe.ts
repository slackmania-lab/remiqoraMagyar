/** Generation "recipe" files: tiny shareable JSON snapshots of a generation form.
 *
 * Saved automatically on every submit as `<title>.remiqora.json` so any track
 * can be reproduced later (same engine + model + seed + settings) or sent to
 * someone else, who loads it back with the Import button. GPU sampling is not
 * bit-exact across machines/drivers, so treat recipes as near-deterministic:
 * same music, possible minute rendering differences.
 */

export interface Recipe {
  app: 'remiqora'
  kind: 'recipe'
  version: 1
  engine: 'yue2' | 'ace_step'
  title: string
  createdAt: string
  params: Record<string, unknown>
  note?: string
}

export function recipeFilename(title: string, seed?: number | null): string {
  const clean = (title || 'untitled')
    .replace(/[\\/:*?"<>|]/g, '')
    .trim()
    .slice(0, 80) || 'untitled'
  // The seed leads the filename so recipes sort/find by it: "1495549958_Title.remiqora.json".
  const prefix = typeof seed === 'number' && Number.isFinite(seed) ? `${seed}_` : ''
  return `${prefix}${clean}.remiqora.json`
}

export function downloadRecipe(recipe: Recipe): void {
  const blob = new Blob([JSON.stringify(recipe, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const params = (recipe.params || {}) as Record<string, unknown>
  const seeds = params.seeds
  const firstSeed = Array.isArray(seeds) && typeof seeds[0] === 'number'
    ? (seeds[0] as number)
    : typeof params.seed === 'number' ? (params.seed as number) : null
  const a = document.createElement('a')
  a.href = url
  a.download = recipeFilename(recipe.title, firstSeed)
  document.body.appendChild(a)
  a.click()
  setTimeout(() => {
    URL.revokeObjectURL(url)
    a.remove()
  }, 1000)
}

export function readRecipeFile(file: File): Promise<Recipe> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('read failed'))
    reader.onload = () => {
      try {
        const data = JSON.parse(String(reader.result)) as Partial<Recipe>
        if (data?.app !== 'remiqora' || data?.kind !== 'recipe' || !data?.engine || typeof data?.params !== 'object') {
          reject(new Error('bad recipe'))
          return
        }
        resolve(data as Recipe)
      } catch {
        reject(new Error('bad recipe'))
      }
    }
    reader.readAsText(file)
  })
}
