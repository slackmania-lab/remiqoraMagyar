<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { LYRIC_LANGS, promptStatus, writeLyrics } from '../../api/prompt'

const emit = defineEmits<{ apply: [lyrics: string, lang: string] }>()

const { t } = useI18n()
const theme = ref('')
const lang = ref(localStorage.getItem('lyricist_lang') || 'en')
const verses = ref(3)
const chorus = ref(true)
const models = ref<string[]>([])
const selectedModel = ref(localStorage.getItem('lyricist_model') || '')
const loading = ref(false)
const error = ref('')
const result = ref('')

const LYRIC_DEFAULTS = ['qwen3:8b', 'qwen3.5:9b', 'llama3.1:8b', 'qwen2.5:3b']

onMounted(async () => {
  try {
    const st = await promptStatus()
    models.value = st.models || []
    if (!selectedModel.value || !models.value.includes(selectedModel.value)) {
      selectedModel.value = LYRIC_DEFAULTS.find((m) => models.value.includes(m)) || st.model || ''
    }
    if (!LYRIC_LANGS.some((l) => l.code === lang.value)) lang.value = 'en'
  } catch {
    // offline: the box still renders, submit will surface the error
  }
})

function onLangChange() {
  localStorage.setItem('lyricist_lang', lang.value)
}

function onModelChange() {
  localStorage.setItem('lyricist_model', selectedModel.value)
}

async function submit() {
  error.value = ''
  result.value = ''
  if (!theme.value.trim()) return
  loading.value = true
  try {
    const r = await writeLyrics(theme.value.trim(), lang.value, verses.value, chorus.value, selectedModel.value)
    result.value = r.lyrics
    apply()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

function apply() {
  if (result.value) emit('apply', result.value, lang.value)
}
</script>

<template>
  <div class="space-y-2 rounded-lg border border-border bg-panel-2/50 p-3">
    <div class="flex items-center justify-between">
      <label class="text-[13px] font-medium text-text">{{ t('lyricist.title') }}</label>
      <span class="text-[11px] text-text-dim">{{ t('lyricist.hint') }}</span>
    </div>
    <textarea
      v-model="theme"
      rows="2"
      class="w-full rounded-lg border border-border bg-panel p-2.5 text-sm text-text"
      :placeholder="t('lyricist.placeholder')"
    ></textarea>
    <div class="flex flex-wrap items-center gap-2">
      <select
        v-model="lang"
        class="rounded-lg border border-border bg-panel px-2 py-1.5 text-xs text-text"
        :title="t('lyricist.langTitle')"
        @change="onLangChange"
      >
        <option v-for="l in LYRIC_LANGS" :key="l.code" :value="l.code">{{ l.label }}</option>
      </select>
      <label class="flex items-center gap-1 text-xs text-text-dim">
        {{ t('lyricist.verses') }}
        <input v-model.number="verses" type="number" min="1" max="8" class="w-12 rounded border border-border bg-panel px-1 py-1 text-xs text-text" />
      </label>
      <label class="flex items-center gap-1 text-xs text-text-dim">
        <input v-model="chorus" type="checkbox" class="rounded border-border" />
        {{ t('lyricist.chorus') }}
      </label>
      <select
        v-if="models.length"
        v-model="selectedModel"
        class="max-w-36 rounded-lg border border-border bg-panel px-2 py-1.5 text-xs text-text"
        :title="t('lyricist.modelTitle')"
        @change="onModelChange"
      >
        <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
      </select>
      <button
        type="button"
        class="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text hover:bg-panel disabled:opacity-50"
        :disabled="loading || !theme.trim()"
        @click="submit"
      >
        {{ loading ? t('lyricist.working') : t('lyricist.submit') }}
      </button>
      <button
        v-if="result"
        type="button"
        class="accent-gradient rounded-lg px-3 py-1.5 text-xs font-medium text-white"
        @click="apply"
      >
        {{ t('lyricist.apply') }}
      </button>
    </div>
    <p v-if="error" class="rounded-lg bg-status-failed/10 p-2 text-xs text-status-failed">{{ error }}</p>
    <div v-if="result" class="whitespace-pre-wrap rounded-lg bg-panel p-2 font-mono text-xs text-text">{{ result }}</div>
  </div>
</template>
