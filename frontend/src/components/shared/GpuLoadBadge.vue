<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { gpuStatus } from '../../api/gpu'

const props = defineProps<{ active: boolean }>()

const { t } = useI18n()
const text = ref('')
const title = ref('')
let timer: ReturnType<typeof setInterval> | null = null

function fmtGB(mib: number): string {
  return `${(mib / 1024).toFixed(1)}`
}

async function poll() {
  try {
    const st = await gpuStatus()
    if (!st.available || st.util_percent == null) {
      text.value = ''
      return
    }
    const mem = st.mem_used_mib != null && st.mem_total_mib != null ? ` · ${fmtGB(st.mem_used_mib)}/${fmtGB(st.mem_total_mib)} GB` : ''
    const temp = st.temp_c != null ? ` · ${st.temp_c}°C` : ''
    text.value = `GPU ${st.util_percent}%${mem}${temp}`
    title.value = t('feed.gpuLoadTitle')
  } catch {
    text.value = ''
  }
}

function start() {
  void poll()
  if (!timer) timer = setInterval(poll, 3000)
}

function stop() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  text.value = ''
}

watch(
  () => props.active,
  (on) => (on ? start() : stop()),
  { immediate: true },
)
onBeforeUnmount(stop)
</script>

<template>
  <span
    v-if="text"
    class="rounded-lg border border-border bg-panel-2 px-2.5 py-1 text-xs tabular-nums text-text-dim"
    :title="title"
  >
    <span class="mr-1 inline-block h-2 w-2 rounded-full bg-status-done align-middle" aria-hidden="true"></span>{{ text }}
  </span>
</template>
