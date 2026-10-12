<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { LYRIC_LANGS, promptStatus, writeLyrics } from '../../api/prompt'
import { formResetToken } from '../../utils/formReset'
import { rollTheme } from '../../utils/wordbank'

const emit = defineEmits<{ apply: [lyrics: string, lang: string] }>()

const { t } = useI18n()
const theme = ref('')
const lang = ref(localStorage.getItem('lyricist_lang') || 'en')
const verses = ref(3)
const sections = ref<string[]>(['chorus'])
const mood = ref('')
const models = ref<string[]>([])
const selectedModel = ref(localStorage.getItem('lyricist_model') || '')
const loading = ref(false)
const error = ref('')
const result = ref('')

const LYRIC_DEFAULTS = ['qwen3:8b', 'qwen3.5:9b', 'llama3.1:8b', 'qwen2.5:3b']

// Optional song parts in canonical order; labels are the literal ABC-style tags.
const SECTION_CODES = ['intro', 'chorus', 'postchorus', 'bridge', 'break', 'guitarsolo', 'drumsolo', 'tablasolo', 'outro'] as const

function sectionTag(code: string): string {
  const map: Record<string, string> = {
    intro: '[Intro]', chorus: '[Chorus]', postchorus: '[Post-Chorus]', bridge: '[Bridge]', break: '[Break]',
    guitarsolo: '[Guitar Solo]', drumsolo: '[Drum Solo]', tablasolo: '[Tabla Solo]', outro: '[Outro]',
  }
  return map[code] || code
}

function toggleSection(code: string) {
  const i = sections.value.indexOf(code)
  if (i === -1) sections.value.push(code)
  else sections.value.splice(i, 1)
}

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
    // The model list is fetched on mount, but Ollama may have been started
    // since (e.g. from the LogDock) — refresh once so the dropdown is alive.
    if (!models.value.length) {
      try {
        const st = await promptStatus()
        models.value = st.models || []
        if (!selectedModel.value || !models.value.includes(selectedModel.value)) {
          selectedModel.value = LYRIC_DEFAULTS.find((m) => models.value.includes(m)) || st.model || ''
        }
      } catch {
        // submit below will surface the real error
      }
    }
    const r = await writeLyrics(theme.value.trim(), lang.value, verses.value, sections.value, mood.value.trim(), selectedModel.value)
    result.value = r.lyrics
    apply()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

function apply() {
  if (result.value) {
    emit('apply', result.value, lang.value)
    // The preview was auto-inserted: clear the temporary copy.
    result.value = ''
  }
}

watch(formResetToken, () => {
  theme.value = ''
  result.value = ''
  error.value = ''
})
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
      <label
        v-for="code in SECTION_CODES"
        :key="code"
        class="flex cursor-pointer items-center gap-1 rounded-lg border px-2 py-1 text-xs"
        :class="sections.includes(code) ? 'border-accent1/60 text-text' : 'border-border text-text-dim hover:text-text'"
        :title="sectionTag(code)"
      >
        <input type="checkbox" class="sr-only" :checked="sections.includes(code)" @change="toggleSection(code)" />
        {{ sectionTag(code) }}
      </label>
      <input
        v-model="mood"
        class="w-28 rounded-lg border border-border bg-panel px-2 py-1.5 text-xs text-text"
        :placeholder="t('lyricist.mood')"
        :title="t('lyricist.moodTitle')"
      />
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
        class="rounded-lg border border-border px-2.5 py-1.5 text-xs text-text hover:bg-panel"
        :title="t('lyricist.dice')"
        @click="theme = rollTheme(); result = ''; error = ''"
      >
        🎲
      </button>
      <button
        type="button"
        class="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text hover:bg-panel disabled:opacity-50"
        :disabled="loading || !theme.trim()"
        @click="submit"
      >
        {{ loading ? t('lyricist.working') : t('lyricist.submit') }}
      </button>
    </div>
    <p v-if="error" class="rounded-lg bg-status-failed/10 p-2 text-xs text-status-failed">{{ error }}</p>
  </div>
</template>
