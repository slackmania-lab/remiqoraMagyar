import { acceptHMRUpdate, defineStore } from 'pinia'
import * as api from '../api/yue2'
import type { CotMode, GenerateOptions } from '../api/yue2'
import * as tracksApi from '../api/tracks'
import { useOrchestratorStore } from './orchestrator'
import type { JobStatus } from '../types'
import { i18n } from '../i18n'

const t = i18n.global.t

const HEALTH_MS = 5000

export interface Yue2Job {
  id: string
  status: JobStatus
  createdAt: number
  /** The name shown on the card and stored as the track title; the user can rename it. */
  title: string
  /** The style tags the track was generated with. Never overwritten by a rename. */
  style: string
  lyrics: string
  cot: CotMode
  precision: 'q8_0' | 'q4_0'
  seed: number
  error?: string
  audioUrl?: string
  abcPlan?: string | null
  durationSec?: number | null
  wallSec?: number | null
  savedFilename?: string | null
  saveError?: string | null
  dbId?: number | null
  finalized: boolean
  favorite: boolean
  params?: Record<string, any>
}

export const useYue2Store = defineStore('yue2', {
  state: () => ({
    jobs: [] as Yue2Job[],
    health: null as api.HealthResponse | null,
    healthError: false,
    historyLoaded: false,
    // Set by a TrackCard's "insert into form" action; GenerateForm watches
    // this and copies it into its own local ABC textarea state.
    pendingAbcInsert: null as string | null,
    pendingParamsInsert: null as Record<string, any> | null,
    _aborters: {} as Record<string, AbortController>,
    _healthTimer: null as ReturnType<typeof setTimeout> | null,
  }),
  actions: {
    requestInsertParams(params: Record<string, any>) {
      this.pendingParamsInsert = { ...params }
    },
    clearPendingParamsInsert() {
      this.pendingParamsInsert = null
    },
    async loadHistory() {
      try {
        const tracks = await tracksApi.listTracks('yue2')
        const savedJobs: Yue2Job[] = tracks.map((t) => ({
          id: `saved_${t.id}`,
          status: 'done',
          createdAt: new Date(t.created_at).getTime() || Date.now(),
          title: t.title,
          // The tags live in the saved params; the title is only a fallback for tracks saved before they were recorded.
          style: (t.params.style as string) || t.title,
          lyrics: t.lyrics,
          cot: (t.params.cot as CotMode) || 'off',
          precision: (t.params.precision as 'q8_0' | 'q4_0') || 'q8_0',
          seed: t.seed ?? 0,
          audioUrl: t.audio_url,
          abcPlan: t.abc_url ? '' : null,
          durationSec: t.duration_ms ? t.duration_ms / 1000 : null,
          wallSec: t.wall_ms ? t.wall_ms / 1000 : null,
          savedFilename: t.filename,
          dbId: t.id,
          finalized: true,
          favorite: t.favorite,
          params: t.params,
        }))
        // Keep any jobs still in-flight this session (not yet in the saved list).
        const inFlightIds = new Set(this.jobs.filter((j) => !j.finalized).map((j) => j.id))
        this.jobs = [...this.jobs.filter((j) => inFlightIds.has(j.id)), ...savedJobs].sort((a, b) => b.createdAt - a.createdAt)
      } finally {
        this.historyLoaded = true
      }
    },
    async refreshHealth() {
      // Don't hammer a stopped engine: it answers every probe with 503,
      // which only spams the backend log. The orchestrator status bar
      // already shows "stopped".
      const orchStatus = useOrchestratorStore().statuses['yue2']?.status
      if (orchStatus === 'stopped' || orchStatus == null) {
        this.healthError = false
        return
      }
      try {
        this.health = await api.health()
        this.healthError = false
      } catch {
        this.healthError = true
      }
    },
    startBackgroundTasks() {
      if (this._healthTimer) return
      const tick = async () => {
        await this.refreshHealth()
        this._healthTimer = setTimeout(tick, HEALTH_MS)
      }
      void tick()
    },
    stopBackgroundTasks() {
      if (this._healthTimer) clearTimeout(this._healthTimer)
      this._healthTimer = null
    },
    async generateBatch(params: { lyrics: string; style: string; cot: CotMode; precision: 'q8_0' | 'q4_0'; baseSeed: number; randomSeed: boolean; seeds?: number[]; batchSize: number; options: GenerateOptions; instrumental?: boolean }) {
      const newJobs: Yue2Job[] = []
      for (let i = 0; i < params.batchSize; i++) {
        const seed = params.seeds && params.seeds.length === params.batchSize
          ? params.seeds[i]
          : params.randomSeed ? Math.floor(Math.random() * 2147483647) : params.baseSeed + i
        newJobs.push({
          id: `g_${Date.now()}_${i}`,
          status: 'queued',
          createdAt: Date.now(),
          title: `${seed}_${params.style}`,
          style: params.style,
          lyrics: params.lyrics,
          cot: params.cot,
          precision: params.precision,
          seed,
          finalized: false,
          favorite: false,
          params: { ...params.options, cot: params.cot, precision: params.precision, style: params.style, lyrics: params.lyrics, instrumental: !!params.instrumental },
        })
      }
      const sessionExtra = params.instrumental ? api.instrumentalSessionOptions() : undefined
      this.jobs.unshift(...newJobs)
      for (const { id } of newJobs) {
        // Look the job back up through the reactive `jobs` array instead of
        // mutating the raw object still held in `newJobs`: Pinia/Vue only
        // tracks changes made through the reactive proxy, so mutating the
        // original (pre-unshift) reference never triggers a re-render even
        // though the same data ends up saved to the server correctly.
        const job = this.jobs.find((j) => j.id === id)
        if (job) await this._generateOne(job, params.options, sessionExtra)
      }
    },
    async _generateOne(job: Yue2Job, options: GenerateOptions, sessionExtra?: Record<string, string>) {
      job.status = 'running'
      const aborter = new AbortController()
      this._aborters[job.id] = aborter
      try {
        const started = performance.now()
        const result = await api.generateTrack(job.lyrics, job.seed, options, job.precision, aborter.signal, sessionExtra)
        const wallMs = result.timing?.wall_ms ?? performance.now() - started
        const durationMs = result.timing?.audio_duration_ms
        if (typeof result.audio !== 'string') throw new Error(t('storeErrors.serverNoAudio'))
        const blob = api.base64AudioBlob(result.audio)
        const abcPlan = api.abcFromResult(result)
        job.audioUrl = URL.createObjectURL(blob)
        job.wallSec = wallMs / 1000
        job.durationSec = durationMs ? durationMs / 1000 : null
        job.abcPlan = abcPlan || null
        job.status = 'done'
        job.finalized = true

        try {
          const saved = await tracksApi.saveTrack(
            {
              model: 'yue2',
              title: job.title,
              lyrics: job.lyrics,
              seed: job.seed,
              duration_ms: durationMs,
              wall_ms: wallMs,
              params: job.params || { cot: job.cot, precision: job.precision },
            },
            blob,
            'wav',
            abcPlan || null,
          )
          job.savedFilename = saved.filename
          job.saveError = null
          job.dbId = saved.id
          job.favorite = saved.favorite
        } catch (err) {
          job.savedFilename = null
          job.saveError = err instanceof Error ? err.message : String(err)
          job.dbId = null
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          job.status = 'cancelled'
        } else {
          job.status = 'failed'
          job.error = err instanceof Error ? err.message : String(err)
        }
        job.finalized = true
      } finally {
        delete this._aborters[job.id]
      }
    },
    cancel(jobId: string) {
      this._aborters[jobId]?.abort()
    },
    requestInsertAbc(abc: string) {
      this.pendingAbcInsert = abc
    },
    clearPendingAbcInsert() {
      this.pendingAbcInsert = null
    },
    async deleteJob(job: Yue2Job) {
      if (job.dbId != null) {
        try {
          await tracksApi.deleteTrack(job.dbId)
        } catch {
          // ignore - still remove locally so the UI doesn't get stuck
        }
      }
      this.jobs = this.jobs.filter((j) => j.id !== job.id)
    },
    async renameJob(job: Yue2Job, title: string) {
      if (job.dbId == null) return
      await tracksApi.renameTrack(job.dbId, title)
      const target = this.jobs.find((j) => j.id === job.id)
      if (target) target.title = title
    },
    async toggleFavorite(job: Yue2Job) {
      if (job.dbId == null) return
      const next = !job.favorite
      job.favorite = next
      try {
        const saved = await tracksApi.setTrackFavorite(job.dbId, next)
        const target = this.jobs.find((j) => j.id === job.id)
        if (target) target.favorite = saved.favorite
      } catch {
        const target = this.jobs.find((j) => j.id === job.id)
        if (target) target.favorite = !next
      }
    },
  },
})

// Without this, editing this file while the dev server is running leaves
// already-mounted components bound to a stale store instance (old action
// closures) instead of picking up the new code - looks like "it's fixed in
// a fresh tab but stuck in the one I already had open".
if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useYue2Store, import.meta.hot))
}
