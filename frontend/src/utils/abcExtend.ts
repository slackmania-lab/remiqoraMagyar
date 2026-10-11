import { parseAbcToMidi } from '../audio/abcParser'

/** Rough plan length in seconds, from the ABC note timings. */
export function estimateAbcSeconds(abc: string): number {
  if (!abc.trim()) return 0
  try {
    const notes = parseAbcToMidi(abc)
    let end = 0
    for (const n of notes) end = Math.max(end, n.startSec + n.durationSec)
    return Math.round(end)
  } catch {
    return 0
  }
}

function isBareVoiceSelector(line: string): boolean {
  // Body blocks start with "V: Vocal" / "V: Ins" (no '='), unlike the header
  // voice definitions ("V: Vocal clef=treble ...").
  return /^V:\s*\S+\s*$/.test(line) && !line.includes('=')
}

/**
 * Repeat the plan body (all voice blocks) to lengthen the composition.
 * Header (X/T/M/L/Q/K + voice definitions) stays untouched; only complete
 * voice blocks are duplicated, so voices never go out of sync.
 * Returns null when the text has no recognizable body to repeat.
 */
export function extendAbc(abc: string, times: number): string | null {
  if (times < 2) return abc
  const lines = abc.replace(/\r\n/g, '\n').split('\n')
  const starts: number[] = []
  lines.forEach((line, i) => {
    if (isBareVoiceSelector(line)) starts.push(i)
  })
  if (starts.length < 2) return null
  const header = lines.slice(0, starts[0])
  const blocks: string[][] = starts.map((s, k) => lines.slice(s, starts[k + 1] ?? lines.length))
  // Trim trailing empty lines per block; rejoin with a blank line like the originals.
  const clean = blocks.map((b) => {
    let end = b.length
    while (end > 0 && b[end - 1].trim() === '') end--
    return b.slice(0, end)
  })
  const out: string[] = [...header]
  for (let r = 0; r < times; r++) {
    for (const b of clean) {
      out.push('', ...b)
    }
  }
  return out.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n'
}
