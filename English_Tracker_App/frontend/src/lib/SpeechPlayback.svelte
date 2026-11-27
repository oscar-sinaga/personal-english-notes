<script>
  import { onMount, onDestroy } from 'svelte';

  export let text;
  export let label = 'Play';
  export let playable = false;
  export let replayBySentence = false;
  export let disabled = false;

  let voices = [];
  let selected = '';
  let rate = 1;
  let part = -1;
  let utterance;
  let playing = false;
  let error = '';
  $: parts = replayBySentence
    ? (typeof Intl.Segmenter === 'function'
      ? Array.from(new Intl.Segmenter('en', { granularity: 'sentence' }).segment(text), item => item.segment.trim()).filter(Boolean)
      : text.split(/(?<=[.!?])\s+/).filter(Boolean))
    : [];
  $: if (part >= parts.length) part = -1;

  function refreshVoices() {
    voices = (window.speechSynthesis?.getVoices?.() ?? [])
      .filter(voice => voice.localService && /^en(?:-|$)/i.test(voice.lang));
    if (!voices.some(voice => voice.voiceURI === selected)) {
      selected = (voices.find(voice => voice.lang === 'en-US') || voices[0])?.voiceURI || '';
    }
    playable = voices.length > 0 && Boolean(window.SpeechSynthesisUtterance);
  }

  onMount(() => {
    refreshVoices();
    window.speechSynthesis?.addEventListener('voiceschanged', refreshVoices);
    return () => window.speechSynthesis?.removeEventListener('voiceschanged', refreshVoices);
  });

  function stop() {
    if (!utterance) return;
    utterance = null;
    playing = false;
    window.speechSynthesis?.cancel();
  }

  function play() {
    if (disabled) return;
    stop();
    refreshVoices();
    const voice = voices.find(option => option.voiceURI === selected);
    if (!voice || !window.SpeechSynthesisUtterance) {
      error = 'An English voice is unavailable on this device.';
      return;
    }
    error = '';
    window.speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(parts[part] ?? text);
    speech.voice = voice;
    speech.lang = voice.lang;
    speech.rate = Number(rate);
    utterance = speech;
    playing = true;
    const ended = () => {
      if (utterance !== speech) return;
      utterance = null;
      playing = false;
    };
    speech.onend = ended;
    speech.onerror = event => {
      if (utterance === speech && !['canceled', 'interrupted'].includes(event.error)) {
        error = 'Could not play audio with the selected device voice.';
        playable = false;
      }
      ended();
    };
    try {
      window.speechSynthesis.speak(speech);
    } catch {
      error = 'Could not start audio playback.';
      playable = false;
      ended();
    }
  }

  onDestroy(stop);
</script>

<div class="space-y-2">
  <div class="flex flex-wrap items-center gap-2">
    <button type="button" class="rounded-md bg-teal-400 px-3 py-2 text-xs font-semibold text-slate-950"
      disabled={disabled} on:click={playing ? stop : play}>{playing ? 'Stop playback' : label}</button>
    <label class="flex items-center gap-1 text-xs text-slate-300">Speed
      <select bind:value={rate} class="rounded border border-slate-700 bg-slate-950 px-1.5 py-2">
        <option value={0.7}>0.7×</option>
        <option value={0.85}>0.85×</option>
        <option value={1}>1×</option>
      </select>
    </label>
    {#if parts.length > 1}
      <label class="flex items-center gap-1 text-xs text-slate-300">Replay
        <select bind:value={part} class="rounded border border-slate-700 bg-slate-950 px-1.5 py-2">
          <option value={-1}>Whole passage</option>
          {#each parts as _, index}
            <option value={index}>Sentence {index + 1}</option>
          {/each}
        </select>
      </label>
    {/if}
    {#if voices.length > 1}
      <label class="flex min-w-0 max-w-full items-center gap-1 text-xs text-slate-300">Voice
        <select bind:value={selected} class="min-w-0 max-w-[12rem] rounded border border-slate-700 bg-slate-950 px-1.5 py-2">
          {#each voices as voice (voice.voiceURI)}
            <option value={voice.voiceURI}>{voice.name}</option>
          {/each}
        </select>
      </label>
    {/if}
  </div>
  {#if error}<p role="status" class="text-xs text-amber-200">{error}</p>{/if}
</div>
