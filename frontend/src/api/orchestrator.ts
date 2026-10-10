import { apiFetch, apiJson } from './http'
import type { ModelId, OrchestratorStatus } from '../types'

export interface Yue2ModelSpecConfig {
  id: string
  family: string
  path: string
  task: string
  mode: string
  model_spec_override?: string
}

export interface OrchestratorConfig {
  yue2_specs: {
    yue2: Yue2ModelSpecConfig
    sheetsage2: Yue2ModelSpecConfig
    muscriptor: Yue2ModelSpecConfig
    [key: string]: Yue2ModelSpecConfig
  }
}

export function getConfig(): Promise<OrchestratorConfig> {
  return apiFetch<OrchestratorConfig>('/api/orchestrator/config')
}

export function getStatus(): Promise<OrchestratorStatus> {
  return apiFetch<OrchestratorStatus>('/api/orchestrator/status')
}

export function switchModel(model: ModelId): Promise<OrchestratorStatus> {
  return apiJson<OrchestratorStatus>('/api/orchestrator/switch', { model })
}

export function stopActive(): Promise<OrchestratorStatus> {
  return apiJson<OrchestratorStatus>('/api/orchestrator/stop', {})
}

export interface LogFile {
  name: string
  size: number
  mtime: number
}

export interface LogTail {
  name: string
  size: number
  next_offset: number
  truncated: boolean
  lines: string[]
}

export async function listLogs(): Promise<LogFile[]> {
  const json = await apiFetch<{ logs: LogFile[] }>('/api/orchestrator/logs')
  return json.logs
}

export async function readLog(name: string, offset = 0, limit = 200): Promise<LogTail> {
  const qs = `offset=${offset}&limit=${limit}`
  return apiFetch<LogTail>(`/api/orchestrator/logs/${encodeURIComponent(name)}?${qs}`)
}
