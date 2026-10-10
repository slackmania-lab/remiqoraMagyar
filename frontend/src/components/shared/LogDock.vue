<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { listLogs, readLog } from '../../api/orchestrator'
import type { LogFile } from '../../api/orchestrator'
import { ollamaStart, ollamaStatus, ollamaStop } from '../../api/ollama'
import type { OllamaServiceStatus } from '../../api/ollama'

interface Pane {
  source: string
  lines: string[]
  offset: number
  follow: boolean
  error: string
}

const { t } = useI18n()
const files = ref<LogFile[]>([])
const ollama = ref<OllamaServiceStatus | null>(null)
const ollamaBusy = ref(false)
const ollamaError = ref('')
const panes = ref<Pane[]>([
  { source: localStorage.getItem('logdock_0') || 'yue2_server.log', lines: [], offset: 0, follow: true, error: '' },
  { source: localStorage.getItem('logdock_1') || 'ace_step_api.log', lines: [], offset: 0, follow: true, error: '' },
])
const boxRefs = ref<Array<HTMLElement | null>>([])
let timer: ReturnType<typeof setInterval> | null = null

function scrollBottom(i: number) {
  const el = boxRefs.value[i]
  if (el) el.scrollTop = el.scrollHeight
}

async function pollPane(i: number) {
  const pane = panes.value[i]
  if (!pane.source) return
  try {
    // Cheap incremental follow: only the bytes since last time (cap 100 lines per tick).
    const tail = await readLog(pane.source, pane.offset, 100)
    // Server rotated/truncated the file: restart from the end.
    if (tail.size < pane.offset) {
      pane.offset = 0
      pane.lines = []
      return
    }
    pane.offset = tail.next_offset
    if (tail.lines.length > 0) {
      pane.lines = [...pane.lines.slice(-400), ...tail.lines]
      if (pane.follow) requestAnimationFrame(() => scrollBottom(i))
    }
    pane.error = ''
  } catch (err) {
    pane.error = err instanceof Error ? err.message : String(err)
  }
}

async function refresh() {
  try {
    files.value = await listLogs()
  } catch {
    files.value = []
    return
  }
  try {
    ollama.value = await ollamaStatus()
  } catch {
    ollama.value = null
  }
  for (let i = 0; i < panes.value.length; i++) {
    const pane = panes.value[i]
    if (pane.source && !files.value.some((f) => f.name === pane.source)) {
      // Fall back to the most recent log when the saved one is gone.
      pane.source = files.value[0]?.name || ''
      pane.offset = 0
      pane.lines = []
    }
    await pollPane(i)
  }
}

function onSourceChange(i: number) {
  const pane = panes.value[i]
  localStorage.setItem(`logdock_${i}`, pane.source)
  pane.offset = 0
  pane.lines = []
  pane.error = ''
  void pollPane(i)
}

async function onOllamaToggle() {
  if (ollamaBusy.value) return
  ollamaBusy.value = true
  ollamaError.value = ''
  try {
    const res = ollama.value?.managed ? await ollamaStop() : await ollamaStart()
    if (!res.ok) ollamaError.value = res.error || 'error'
    ollama.value = await ollamaStatus()
    await refresh()
  } catch (err) {
    ollamaError.value = err instanceof Error ? err.message : String(err)
  } finally {
    ollamaBusy.value = false
  }
}

refresh()
timer = setInterval(refresh, 2000)
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="space-y-2">
    <div class="flex flex-wrap items-center gap-2">
      <h3 class="text-sm font-semibold text-text">{{ t('logs.title') }}</h3>
      <button
        type="button"
        class="rounded-lg border border-border px-2.5 py-1 text-xs font-medium text-text-dim hover:bg-panel-2 hover:text-text disabled:opacity-50"
        :disabled="ollamaBusy"
        :title="t('logs.ollamaHint')"
        @click="onOllamaToggle"
      >
        {{ ollama?.managed ? `⏹ Ollama` : `▶ Ollama` }}
      </button>
      <span v-if="ollama" class="text-xs text-text-dim">
        {{ ollama.managed ? t('logs.ollamaManaged') : ollama.external ? t('logs.ollamaExternal') : t('logs.ollamaOff') }}
      </span>
      <span v-if="ollamaError" class="text-xs text-status-failed">{{ ollamaError }}</span>
    </div>
    <div class="grid grid-cols-1 gap-3 xl:grid-cols-2">
      <div v-for="(pane, i) in panes" :key="i" class="overflow-hidden rounded-xl border border-border bg-black/60">
        <div class="flex items-center gap-2 border-b border-border bg-panel-2/60 px-2 py-1.5">
          <select
            v-model="pane.source"
            class="min-w-0 flex-1 rounded border border-border bg-panel px-1.5 py-1 font-mono text-xs text-text"
            :aria-label="t('logs.source')"
            @change="onSourceChange(i)"
          >
            <option value="">{{ t('logs.noSource') }}</option>
            <option v-for="f in files" :key="f.name" :value="f.name">{{ f.name }}</option>
          </select>
          <label class="flex shrink-0 cursor-pointer items-center gap-1 text-xs text-text-dim">
            <input v-model="pane.follow" type="checkbox" class="rounded border-border" />
            {{ t('logs.follow') }}
          </label>
        </div>
        <div
          :ref="(el) => { boxRefs[i] = el as HTMLElement | null }"
          class="h-44 overflow-y-auto whitespace-pre-wrap break-all p-2 font-mono text-[11px] leading-4 text-green-300/90"
        >
          <span v-if="pane.error" class="text-status-failed">{{ pane.error }}</span>
          <template v-else>{{ pane.lines.join('\n') || t('logs.empty') }}</template>
        </div>
      </div>
    </div>
  </div>
</template>
