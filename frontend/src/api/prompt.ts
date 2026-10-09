import { apiFetch, apiJson } from './http'

export interface PromptPrepareResult {
  style_en: string
  lyrics: string
  simple: string
  vocal_language: string
}

export interface PromptLang {
  code: string
  label: string
}

export interface PromptStatus {
  reachable: boolean
  engine?: string
  local_ready?: boolean
  model: string
  model_present?: boolean
  models?: string[]
  supported_langs?: PromptLang[]
  error?: string
}

export async function preparePrompt(text: string, target: string, model?: string, srcLang?: string): Promise<PromptPrepareResult> {
  return apiJson<PromptPrepareResult>('/api/prompt/prepare', { text, target, model: model || '', src_lang: srcLang || 'auto' })
}

export interface LyricLang {
  code: string
  label: string
}

export const LYRIC_LANGS: LyricLang[] = [
  { code: 'en', label: 'English' },
  { code: 'hu', label: 'Magyar' },
  { code: 'ar', label: 'العربية' },
  { code: 'sv', label: 'Svenska' },
  { code: 'no', label: 'Norsk' },
  { code: 'da', label: 'Dansk' },
  { code: 'de', label: 'Deutsch' },
  { code: 'fr', label: 'Français' },
  { code: 'it', label: 'Italiano' },
  { code: 'pt', label: 'Português' },
  { code: 'es', label: 'Español' },
]

export interface LyricsResult {
  lyrics: string
  lang: string
  model: string
}

export async function writeLyrics(theme: string, lang: string, verses: number, chorus: boolean, model?: string): Promise<LyricsResult> {
  return apiJson<LyricsResult>('/api/prompt/lyrics', { theme, lang, verses, chorus, model: model || '' })
}

export async function promptStatus(): Promise<PromptStatus> {
  return apiFetch<PromptStatus>('/api/prompt/status')
}
