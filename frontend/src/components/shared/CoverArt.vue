<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as tracksApi from '../../api/tracks'

const props = defineProps<{ dbId: number | null | undefined; prompt: string; initialUrl?: string | null }>()

const { t } = useI18n()
const url = ref<string | null>(props.initialUrl || null)
const working = ref(false)
const error = ref('')
const zoomed = ref(false)
// Prefilled from the track, but fully editable: the image can be anything,
// not just an album cover.
const promptText = ref(props.prompt)
const edited = ref(false)
const showPrompt = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

watch(
  () => props.initialUrl,
  (v) => {
    if (v) url.value = v
  },
)

watch(
  () => props.prompt,
  (v) => {
    if (!edited.value) promptText.value = v
  },
)

function stopPoll() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') zoomed.value = false
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  stopPoll()
  window.removeEventListener('keydown', onKey)
})

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
  // The no-text suffix only applies to the untouched auto prompt; a
  // hand-written prompt goes through verbatim.
  const prompt = edited.value ? promptText.value.trim() : `${promptText.value.trim()}, no text, no watermark, no logo`
  if (!prompt) {
    error.value = t('trackCard.coverEmptyPrompt')
    working.value = false
    return
  }
  try {
    await tracksApi.requestCover(props.dbId, prompt)
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
  <div class="space-y-1.5">
    <div class="flex items-center gap-2">
      <button
        v-if="url"
        type="button"
        class="shrink-0 rounded-lg border border-border p-0 hover:border-accent1/60"
        :title="t('trackCard.coverZoom')"
        @click="zoomed = true"
      >
        <img :src="url" :alt="t('trackCard.cover')" class="h-14 w-14 rounded-lg object-cover" loading="lazy" />
      </button>
      <a
        v-if="url"
        :href="url"
        download
        class="flex h-8 w-8 items-center justify-center rounded-lg text-text-dim hover:bg-panel-2 hover:text-text"
        :title="t('trackCard.coverDownload')"
        :aria-label="t('trackCard.coverDownload')"
      >
        ⬇
      </a>
      <button
        v-if="dbId != null && !working"
        type="button"
        class="flex h-8 w-8 items-center justify-center rounded-lg text-text-dim hover:bg-panel-2 hover:text-text"
        :title="t('trackCard.coverPrompt')"
        :aria-label="t('trackCard.coverPrompt')"
        :aria-pressed="showPrompt"
        @click="showPrompt = !showPrompt"
      >
        ✎
      </button>
      <button
        v-if="dbId != null && !working"
        type="button"
        class="rounded-lg border border-border px-2 py-1 text-xs text-text-dim hover:bg-panel-2 hover:text-text"
        :title="t('trackCard.coverGenerate')"
        @click="generate"
      >
        {{ url ? `↻ ${t('trackCard.cover')}` : `🖼 ${t('trackCard.cover')}` }}
      </button>
      <span v-if="working" class="text-xs text-text-dim">{{ t('trackCard.coverWorking') }}…</span>
    </div>
    <p v-if="error" class="text-xs text-status-failed">{{ error }}</p>
    <div v-if="dbId != null && !working && showPrompt" class="space-y-1">
      <textarea
        v-model="promptText"
        rows="2"
        class="w-full rounded-lg border border-border bg-panel-2 p-2 text-xs text-text"
        :placeholder="t('trackCard.coverPrompt')"
        :aria-label="t('trackCard.coverPrompt')"
        @input="edited = true"
      ></textarea>
    </div>
    <div
      v-if="zoomed && url"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4"
      role="dialog"
      :aria-label="t('trackCard.cover')"
      @click.self="zoomed = false"
    >
      <button
        type="button"
        class="absolute right-4 top-4 rounded-lg border border-border bg-panel px-3 py-1.5 text-sm text-text hover:bg-panel-2"
        @click="zoomed = false"
      >
        ✕ {{ t('trackCard.coverClose') }}
      </button>
      <img :src="url" :alt="t('trackCard.cover')" class="max-h-full max-w-full rounded-xl object-contain" @click.self="zoomed = false" />
    </div>
  </div>
</template>
