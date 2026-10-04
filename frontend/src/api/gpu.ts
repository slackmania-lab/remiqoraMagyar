import { apiFetch } from './http'

export interface GpuStatus {
  available: boolean
  util_percent?: number
  mem_used_mib?: number
  mem_total_mib?: number
  temp_c?: number
}

export async function gpuStatus(): Promise<GpuStatus> {
  return apiFetch<GpuStatus>('/api/gpu')
}
