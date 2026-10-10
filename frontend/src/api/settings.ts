import { apiFetch, apiJson } from './http'

export interface AppSettings {
  artist: string
}

export const getSettings = () => apiFetch<AppSettings>('/api/settings')
export const saveSettings = (settings: AppSettings) => apiJson<AppSettings>('/api/settings', settings, 'PUT')

export interface Wordbanks {
  prompt: Record<string, string[]>
  theme: Record<string, string[]>
}

export const getWordbanks = () => apiFetch<Wordbanks>('/api/settings/wordbanks')
export const saveWordbanks = (banks: Wordbanks) => apiJson<Wordbanks>('/api/settings/wordbanks', banks, 'PUT')
