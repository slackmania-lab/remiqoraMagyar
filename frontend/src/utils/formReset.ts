import { ref } from 'vue'

/** Bumped by the "New form" buttons; PromptBridge/LyricistBox watch it and
 * clear their own input buffers so the whole form returns to a clean slate. */
export const formResetToken = ref(0)

export function fireFormReset(): void {
  formResetToken.value += 1
}
