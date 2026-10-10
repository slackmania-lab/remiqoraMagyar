import { apiFetch } from './http'

export interface OllamaServiceStatus {
  managed: boolean
  running: boolean
  external: boolean
  on_path: boolean
}

export interface OllamaAction {
  ok: boolean
  already?: boolean
  error?: string
}

export async function ollamaStatus(): Promise<OllamaServiceStatus> {
  return apiFetch<OllamaServiceStatus>('/api/ollama/status')
}

export async function ollamaStart(): Promise<OllamaAction> {
  return apiFetch<OllamaAction>('/api/ollama/start', { method: 'POST' })
}

export async function ollamaStop(): Promise<OllamaAction> {
  return apiFetch<OllamaAction>('/api/ollama/stop', { method: 'POST' })
}
