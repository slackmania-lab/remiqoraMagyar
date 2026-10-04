import { createI18n } from 'vue-i18n'
import ru from '../locales/ru'
import en from '../locales/en'
import hu from '../locales/hu'

export type LocaleCode = 'ru' | 'en' | 'hu'
const STORAGE_KEY = 'remiqora_locale'

// The interface follows the system language until the user picks one.
// Hungarian first (this edition's audience), then the original rule: any
// Russian among the preferred languages counts (people in Ukraine, Belarus
// or Kazakhstan often list uk/be/kk first and ru second).
function systemLocale(): LocaleCode {
  const preferred = navigator.languages?.length ? navigator.languages : [navigator.language ?? '']
  const langs = preferred.map((lang) => lang.toLowerCase())
  if (langs.some((lang) => lang.startsWith('hu'))) return 'hu'
  return langs.some((lang) => lang.startsWith('ru')) ? 'ru' : 'en'
}

function detectInitialLocale(): LocaleCode {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'ru' || saved === 'en' || saved === 'hu') return saved
  } catch {
    // localStorage unavailable (private browsing) - fall through to the system language.
  }
  return systemLocale()
}

const initialLocale = detectInitialLocale()
document.documentElement.lang = initialLocale

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: 'en',
  messages: { ru, en, hu },
})

export function setLocale(locale: LocaleCode) {
  ;(i18n.global.locale as any).value = locale
  document.documentElement.lang = locale
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // ignore - just won't persist across reloads
  }
}

export function currentLocale(): LocaleCode {
  return (i18n.global.locale as any).value
}
