/** Two separate Hungarian word banks for the dice buttons.
 *
 * PROMPT bank -> style descriptions for the prompt bridge
 *   ("melankolikus folk hegedűvel, köd hangulatban").
 * THEME bank -> song themes for the lyricist
 *   ("elhagyott kikötő, őszi eső").
 * Split because one shared bank repeats itself too fast. Pure frontend,
 * no backend needed - edit and extend freely.
 *
 * Users can append their own words in Settings (/settings); those live in
 * the backend DB and are merged in by loadCustomBanks().
 */
import { getWordbanks } from '../api/settings'

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

export const PROMPT_CATS = ['moods', 'genres', 'instruments', 'images', 'extras', 'eras', 'tempo', 'vocals', 'production'] as const
export const THEME_CATS = ['places', 'feelings', 'objects', 'times'] as const

/** Built-in banks, exposed read-only for the Settings page display. */
export const BUILTIN_PROMPT: Record<string, string[]> = {}
export const BUILTIN_THEME: Record<string, string[]> = {}

let customPrompt: Record<string, string[]> = {}
let customTheme: Record<string, string[]> = {}
let loaded = false
let loading: Promise<void> | null = null

/** Fetch user word banks once (cached); dice falls back to built-ins until loaded. */
export function loadCustomBanks(): Promise<void> {
  if (loaded) return Promise.resolve()
  if (loading) return loading
  loading = getWordbanks()
    .then((banks) => {
      customPrompt = banks.prompt || {}
      customTheme = banks.theme || {}
      loaded = true
    })
    .catch(() => {
      loaded = true // offline backend: stick to built-ins
    })
    .finally(() => {
      loading = null
    })
  return loading
}

function withCustom(base: string[], cat: string, custom: Record<string, string[]>): string[] {
  const extra = (custom[cat] || []).filter((w) => typeof w === 'string' && w.trim())
  return extra.length > 0 ? [...base, ...extra] : base
}

// ---------------------------------------------------------------------------
// PROMPT bank (style descriptions)
// ---------------------------------------------------------------------------

const P_MOODS = [
  'szomorú', 'vidám', 'epikus', 'sötét', 'álmodozó', 'vad', 'nyugodt',
  'melankolikus', 'ünnepélyes', 'lázadó', 'nosztalgikus', 'sejtelmes',
  'játékos', 'drámai', 'törékeny', 'büszke', 'fájdalmas', 'reményteli',
  'baljós', 'mámoros', 'higgadt', 'szilaj', 'bensőséges', 'fenyegető',
  'fénylő', 'keserédes', 'pajkos', 'komor', 'lebegő', 'tüzes',
]

const P_GENRES = [
  'rock', 'techno', 'folk', 'blues', 'metal', 'pop', 'jazz', 'ambient',
  'punk', 'country', 'reggae', 'szintipop', 'ballada', 'keringő', 'rap',
  'sanzon', 'operett', 'musical', 'gospel', 'soul', 'funk', 'disco',
  'grunge', 'indie', 'lofi', 'drum and bass', 'hardstyle', 'skandináv',
  'norvég folk', 'izlandi', 'tuareg', 'indiai', 'szaharai',
]

const P_INSTRUMENTS = [
  'gitár', 'zongora', 'hegedű', 'dob', 'harmonika', 'furulya', 'szaxofon',
  'cselló', 'hárfa', 'trombita', 'bendzsó', 'cimbalom', 'basszusgitár',
  'szintetizátor', 'tambura', 'brácsa', 'nagybőgő', 'klarinét', 'oboa',
  'orgona', 'tangóharmonika', 'szájharmonika', 'ukulele', 'mandolin',
]

const P_IMAGES = [
  'eső', 'éjszakai város', 'tenger', 'hegyek', 'vonat', 'kikötő', 'sivatag',
  'erdő', 'folyó', 'csillagos ég', 'köd', 'tábortűz', 'hóesés', 'naplemente',
  'elhagyott gyár', 'kis kocsma', 'vihar', 'hajnal', 'alkonyat', 'metró',
  'tetőterasz', 'kastély', 'piac', 'templom', 'híd', 'sziget',
]

const P_EXTRAS = [
  'akusztikusan', 'elektronikusan', 'élő dobokkal', 'vonósnégyessel',
  'visszhangos gitárral', 'dübörgő basszussal',
]

const P_ERAS = [
  '80-as évek', 'középkori hangulat', 'futurisztikus', '60-as évek',
  'mesebeli', '70-es évek', 'barokk', 'vadnyugati', 'viking', 'űrkorszak',
]

const P_TEMPO = [
  'lassú tempóban', 'pörgős ritmussal', 'közepes tempóban',
  'szaggatott ritmussal', 'andalgósan', 'száguldva', 'lüktetve',
]

const P_VOCALS = [
  'női énekkel', 'férfihangon', 'kórussal', 'suttogós vokállal',
  'gyerekkórussal', 'tiszta énekhangon', 'torz vokállal', 'ének nélkül',
]

const P_PROD = [
  'nyers hangzással', 'csiszolt produkció', 'lofi', 'visszhangosan',
  'telt hangzással', 'minimalistán', 'garázszenekarosan', 'stúdiótisztán',
]

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

/** One random Hungarian tag list for the prompt bridge: exactly ONE genre,
 *  1-2 moods, then 2-4 more slots from the rest (never a second genre). */
export function rollPrompt(): string {
  const genre = pick(withCustom(P_GENRES, 'genres', customPrompt))
  const moods = shuffle(withCustom(P_MOODS, 'moods', customPrompt))
  const tags = [genre, moods[0]]
  if (moods.length > 1 && Math.random() < 0.5) tags.push(moods[1])
  const fillers: Array<() => string | null> = [
    () => `${pick(withCustom(P_INSTRUMENTS, 'instruments', customPrompt))} kísérettel`,
    () => pick(withCustom(P_VOCALS, 'vocals', customPrompt)),
    () => pick(withCustom(P_TEMPO, 'tempo', customPrompt)),
    () => `${pick(withCustom(P_IMAGES, 'images', customPrompt))} hangulatban`,
    () => pick(withCustom(P_PROD, 'production', customPrompt)),
    () => (Math.random() < 0.35 ? pick(withCustom(P_EXTRAS, 'extras', customPrompt)) : null),
  ]
  const extraCount = 2 + Math.floor(Math.random() * 3)
  for (const make of shuffle(fillers).slice(0, extraCount)) {
    const tag = make()
    if (tag && !tags.includes(tag)) tags.push(tag)
  }
  if (Math.random() < 0.4) {
    const era = pick(withCustom(P_ERAS, 'eras', customPrompt))
    if (!tags.includes(era)) tags.push(era)
  }
  return tags.join(', ')
}

// ---------------------------------------------------------------------------
// THEME bank (lyricist song themes)
// ---------------------------------------------------------------------------

const T_PLACES = [
  'elhagyott kikötő', 'őszi eső', 'éjféli vonat', 'kihűlt kávé', 'üres játszótér',
  'hajnali metró', 'leégett ház', 'csonka hold', 'vasárnapi piac', 'ködös folyópart',
  'bezárt mozi', 'rozsdás híd', 'néptelen strand', 'villanypózna fénye',
  'padlásszoba', 'kórházi folyosó', 'éjjeli benzinkút', 'szőlőhegy',
  'panelrengeteg', 'folyóparti pad', 'templomtorony', 'vurstli', 'lomtár',
  'tanyasi udvar', 'alagút', 'kilátó', 'szökőkút', 'vasútállomás',
]

const T_FEELINGS = [
  'búcsúzás', 'honvágy', 'féltékenység', 'megbocsátás', 'szabadságvágy',
  'magány', 'hála', 'düh', 'reménykedés', 'felejtés', 'várakozás',
  'bűntudat', 'felszabadulás', 'nosztalgia', 'szerelem első látásra',
  'utolsó tánc', 'hazatérés', 'elbukás', 'újratervezés', 'cinkosság',
]

const T_OBJECTS = [
  'törött óra', 'megfakult fénykép', 'elveszett kulcs', 'régi bakelit',
  'papírhajó', 'kigyulladt levél', 'üres boríték', 'rozsdás bicikli',
  'kölcsönkapott kabát', 'befejezetlen levél', 'tengerészcsomó',
  'kinyílt esernyő', 'lejárt vonatjegy', 'recsegő rádió', 'poros padlásláda',
]

const T_TIMES = [
  'hajnal előtt', 'éjfél után', 'alkonyatkor', 'hétfő reggel', 'szilveszter éjjelén',
  'nyárutón', 'tél derekán', 'márciusban', 'egy esős kedden', 'holdtöltekor',
]

/** One random Hungarian song theme for the lyricist.
 * Fixed structure: feelings (+times) and places (+objects). */
export function rollTheme(): string {
  const places = withCustom(T_PLACES, 'places', customTheme)
  const feelings = withCustom(T_FEELINGS, 'feelings', customTheme)
  const objects = withCustom(T_OBJECTS, 'objects', customTheme)
  const times = withCustom(T_TIMES, 'times', customTheme)
  let out = `${pick(feelings)}, ${pick(places)}`
  if (Math.random() < 0.6) out += `, ${pick(times)}`
  if (Math.random() < 0.5) out += `, ${pick(objects)}`
  return out
}

Object.assign(BUILTIN_PROMPT, { moods: P_MOODS, genres: P_GENRES, instruments: P_INSTRUMENTS, images: P_IMAGES, extras: P_EXTRAS, eras: P_ERAS, tempo: P_TEMPO, vocals: P_VOCALS, production: P_PROD });
Object.assign(BUILTIN_THEME, { places: T_PLACES, feelings: T_FEELINGS, objects: T_OBJECTS, times: T_TIMES });
