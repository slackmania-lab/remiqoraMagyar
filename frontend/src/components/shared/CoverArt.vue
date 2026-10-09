<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as tracksApi from '../../api/tracks'

const props = defineProps<{ dbId: number | null | undefined; prompt: string; initialUrl?: string | null }>()

const { t } = useI18n()
const url = ref<string | null>(props.initialUrl || null)
const working = ref(false)
const error = ref('')
let timer: ReturnType<typeof setInterval> | null = null

watch(
  () => props.initialUrl,
  (v) => {
    if (v) url.value = v
  },
)

function stopPoll() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}
onBeforeUnmount(stopPoll)

async function poll() {
  if (props.dbId == null) return
  try {
    const st = await tracksApi.coverStatus(props.dbId)
    if (st.status === 'done' && st.url) {
      url.value = `${st.url}?t=${Date.now()}`
      working.value = false
      stopPoll()
    } else if (st.status === 'failed' || st.status === 'cancelled') {
      error.value = st.error || st.status
      working.value = false
      stopPoll()
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
    working.value = false
    stopPoll()
  }
}

async function generate() {
  if (props.dbId == null || working.value) return
  error.value = ''
  working.value = true
  try {
    await tracksApi.requestCover(props.dbId, `${props.prompt}, no text, no watermark, no logo`)
    stopPoll()
    timer = setInterval(poll, 3000)
    void poll()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
    working.value = false
  }
}
</script>

<template>
  <div class="flex items-center gap-2">
    <a v-if="url" :href="url" target="_blank" rel="noopener" :title="t('trackCard.cover')">
      <img :src="url" :alt="t('trackCard.cover')" class="h-14 w-14 rounded-lg border border-border object-cover" loading="lazy" />
    </a>
    <button
      v-if="dbId != null && !url && !working"
      type="button"
      class="rounded-lg border border-border px-2 py-1 text-xs text-text-dim hover:bg-panel-2 hover:text-text"
      :title="t('trackCard.coverGenerate')"
      @click="generate"
    >
      {{ `🖼 ${t('trackCard.cover')}` }}
    </button>
    <span v-if="working" class="text-xs text-text-dim">{{ t('trackCard.coverWorking') }}…</span>
    <p v-if="error" class="text-xs text-status-failed">{{ error }}</p>
  </div>
</template>
