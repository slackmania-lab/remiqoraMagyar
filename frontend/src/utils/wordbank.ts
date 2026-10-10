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

export const PROMPT_CATS = ['moods', 'genres', 'instruments', 'images', 'extras', 'eras'] as const
export const THEME_CATS = ['places', 'feelings', 'objects', 'times'] as const

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
  'női énekkel', 'férfihangon', 'kórussal', 'lassú tempóban', 'pörgős ritmussal',
  'akusztikusan', 'elektronikusan', 'élő dobokkal', 'vonósnégyessel',
  'suttogós vokállal', 'dübörgő basszussal', 'visszhangos gitárral',
  'gyerekkórussal', 'torzított hangzással', 'tiszta énekhangon',
]

const P_ERAS = [
  '80-as évek', 'középkori hangulat', 'futurisztikus', '60-as évek',
  'mesebeli', '70-es évek', 'barokk', 'vadnyugati', 'viking', 'űrkorszak',
]

/** One random Hungarian song description for the prompt bridge. */
export function rollPrompt(): string {
  const mood = pick(withCustom(P_MOODS, 'moods', customPrompt))
  const genre = pick(withCustom(P_GENRES, 'genres', customPrompt))
  const instrument = pick(withCustom(P_INSTRUMENTS, 'instruments', customPrompt))
  const image = pick(withCustom(P_IMAGES, 'images', customPrompt))
  const extra = pick(withCustom(P_EXTRAS, 'extras', customPrompt))
  const templates = [
    `${mood} ${genre} ${instrument} kísérettel, ${image} hangulatban`,
    `${mood} dal ${image}-ról, ${genre} alapokon`,
    `${genre} ${extra}, ${mood} hangzással`,
    `${mood} ${genre}, ${instrument} és ${image}`,
    `${instrument}-szólós ${genre}, ${mood} lélekkel`,
    `${image} ihlette ${mood} ${genre}`,
  ]
  let out = pick(templates)
  if (!out.includes(extra) && Math.random() < 0.5) out += `, ${extra}`
  const eras = withCustom(P_ERAS, 'eras', customPrompt)
  if (Math.random() < 0.25) out += `, ${pick(eras)}`
  return out
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

/** One random Hungarian song theme for the lyricist. */
export function rollTheme(): string {
  const places = withCustom(T_PLACES, 'places', customTheme)
  const feelings = withCustom(T_FEELINGS, 'feelings', customTheme)
  const objects = withCustom(T_OBJECTS, 'objects', customTheme)
  const times = withCustom(T_TIMES, 'times', customTheme)
  const templates = [
    `${pick(places)}, ${pick(times)}`,
    `${pick(places)}, ${pick(feelings)}`,
    `${pick(feelings)} ${pick(times)}`,
    `${pick(objects)} és ${pick(feelings)}`,
    `${pick(places)} — ${pick(objects)}`,
    `${pick(times)} a ${pick(places)} mellett`,
  ]
  return pick(templates)
}
