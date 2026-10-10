/** Shared Hungarian "prompt parts" word bank for the dice buttons.
 *
 * Pure frontend, no backend needed: rolls a Hungarian description that flows
 * into the prompt bridge (which translates it) or straight into the lyricist
 * as a theme. Edit/extend freely — more words, more surprise.
 */

const MOODS = [
  'szomorú', 'vidám', 'epikus', 'sötét', 'álmodozó', 'vad', 'nyugodt',
  'melankolikus', 'ünnepélyes', 'lázadó', 'nosztalgikus', 'sejtelmes',
  'játékos', 'drámai', 'törékeny', 'büszke',
]

const GENRES = [
  'rock', 'techno', 'folk', 'blues', 'metal', 'pop', 'jazz', 'ambient',
  'punk', 'country', 'reggae', 'szintipop', 'ballada', 'keringő', 'rap',
]

const INSTRUMENTS = [
  'gitár', 'zongora', 'hegedű', 'dob', 'harmonika', 'furulya', 'szaxofon',
  'cselló', 'hárfa', 'trombita', 'bendzsó', 'cimbalom', 'basszusgitár',
  'szintetizátor', 'tambura',
]

const IMAGES = [
  'eső', 'éjszakai város', 'tenger', 'hegyek', 'vonat', 'kikötő', 'sivatag',
  'erdő', 'folyó', 'csillagos ég', 'köd', 'tábortűz', 'hóesés', 'naplemente',
  'elhagyott gyár', 'kis kocsma',
]

const EXTRAS = [
  'női énekkel', 'férfihangon', 'kórussal', 'lassú tempóban', 'pörgős ritmussal',
  'akusztikusan', 'elektronikusan', 'élő dobokkal', 'vonósnégyessel',
]

const ERAS = ['80-as évek', 'középkori hangulat', 'futurisztikus', '60-as évek', 'mesebeli']

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function maybe<T>(arr: T[], chance: number): T | '' {
  return Math.random() < chance ? pick(arr) : ''
}

/** One random Hungarian song description, e.g. "melankolikus folk hegedűvel, köd hangulatban". */
export function rollPrompt(): string {
  const mood = pick(MOODS)
  const genre = pick(GENRES)
  const instrument = pick(INSTRUMENTS)
  const image = pick(IMAGES)
  const extra = pick(EXTRAS)
  const era = maybe(ERAS, 0.25)
  const templates = [
    `${mood} ${genre} ${instrument} kísérettel, ${image} hangulatban`,
    `${mood} dal ${image}-ról, ${genre} alapokon`,
    `${genre} ${extra}, ${mood} hangzással`,
    `${mood} ${genre}, ${instrument} és ${image}`,
  ]
  let out = pick(templates)
  if (!out.includes(extra) && Math.random() < 0.6) out += `, ${extra}`
  if (era) out += `, ${era}`
  return out
}
