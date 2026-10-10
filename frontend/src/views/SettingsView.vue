<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getWordbanks, saveWordbanks } from '../api/settings'
import type { Wordbanks } from '../api/settings'
import { BUILTIN_PROMPT, BUILTIN_THEME, PROMPT_CATS, THEME_CATS } from '../utils/wordbank'

const { t } = useI18n()
// One textarea per category, one word/phrase per line. Saved to the backend
// DB and merged into the dice rolls (built-ins stay).
const promptText = ref<Record<string, string>>({})
const themeText = ref<Record<string, string>>({})
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const savedAt = ref('')

function toText(banks: Wordbanks, key: 'prompt' | 'theme', cat: string): string {
  return ((banks[key] || {})[cat] || []).join('\n')
}

function fromText(raw: string): string[] {
  return raw
    .split('\n')
    .map((w) => w.trim())
    .filter((w) => w.length > 0)
    .slice(0, 200)
}

onMounted(async () => {
  try {
    const banks = await getWordbanks()
    for (const cat of PROMPT_CATS) promptText.value[cat] = toText(banks, 'prompt', cat)
    for (const cat of THEME_CATS) themeText.value[cat] = toText(banks, 'theme', cat)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
})

async function save() {
  error.value = ''
  savedAt.value = ''
  saving.value = true
  try {
    const banks: Wordbanks = { prompt: {}, theme: {} }
    for (const cat of PROMPT_CATS) {
      const words = fromText(promptText.value[cat] || '')
      if (words.length > 0) banks.prompt[cat] = words
    }
    for (const cat of THEME_CATS) {
      const words = fromText(themeText.value[cat] || '')
      if (words.length > 0) banks.theme[cat] = words
    }
    await saveWordbanks(banks)
    savedAt.value = new Date().toLocaleTimeString()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <div>
      <h1 class="text-xl font-semibold text-text">{{ t('settings.title') }}</h1>
      <p class="mt-1 text-sm text-text-dim">{{ t('settings.subtitle') }}</p>
    </div>
    <p v-if="loading" class="text-sm text-text-dim">{{ t('common.loading') }}</p>
    <template v-else>
      <section class="space-y-3">
        <h2 class="text-lg font-semibold text-text">{{ t('settings.promptBank') }}</h2>
        <p class="text-sm text-text-dim">{{ t('settings.promptHint') }}</p>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div v-for="cat in PROMPT_CATS" :key="cat">
            <label class="mb-1 block text-[13px] font-medium text-text">{{ t(`settings.cats.${cat}`) }}</label>
            <textarea
              v-model="promptText[cat]"
              rows="4"
              class="w-full rounded-lg border border-border bg-panel-2 p-2 text-sm text-text"
              :placeholder="t('settings.wordPlaceholder')"
            ></textarea>
            <p class="mt-1 text-[11px] leading-4 text-text-dim">
              <span class="font-medium">{{ t('settings.builtin') }}:</span> {{ (BUILTIN_PROMPT[cat] || []).join(', ') }}
            </p>
          </div>
        </div>
      </section>
      <section class="space-y-3">
        <h2 class="text-lg font-semibold text-text">{{ t('settings.themeBank') }}</h2>
        <p class="text-sm text-text-dim">{{ t('settings.themeHint') }}</p>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div v-for="cat in THEME_CATS" :key="cat">
            <label class="mb-1 block text-[13px] font-medium text-text">{{ t(`settings.cats.${cat}`) }}</label>
            <textarea
              v-model="themeText[cat]"
              rows="4"
              class="w-full rounded-lg border border-border bg-panel-2 p-2 text-sm text-text"
              :placeholder="t('settings.wordPlaceholder')"
            ></textarea>
            <p class="mt-1 text-[11px] leading-4 text-text-dim">
              <span class="font-medium">{{ t('settings.builtin') }}:</span> {{ (BUILTIN_THEME[cat] || []).join(', ') }}
            </p>
          </div>
        </div>
      </section>
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="accent-gradient rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          :disabled="saving"
          @click="save"
        >
          {{ saving ? t('settings.saving') : t('settings.save') }}
        </button>
        <p v-if="savedAt" class="text-xs text-text-dim">{{ t('settings.saved', { time: savedAt }) }}</p>
        <p v-if="error" class="text-xs text-status-failed">{{ error }}</p>
      </div>
    </template>
  </div>
</template>
