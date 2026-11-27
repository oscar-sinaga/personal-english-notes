<script>
  import { onMount, onDestroy } from 'svelte';

  export let transcript = '';
  export let audio = null;
  export let disabled = false;
  export let active = false;
  export let number = 1;
  export let onChange;

  const MAX_BYTES = 900000;
  const MAX_SECONDS = 60;
  const formats = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4', 'audio/webm'];
  const language = { langs: ['en-US'], processLocally: true, quality: 'dictation' };
  let recognitionClass;
  let local = 'unsupported';
  let phase = 'idle';
  let attempt;
  let elapsed = 0;
  let disposed = false;
  let supported = false;
  let message = '';
  let previousBlob;
  let audioUrl = '';
  let installing = false;

  $: active = phase !== 'idle';
  $: if (audio !== previousBlob) {
    previousBlob = audio;
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    audioUrl = audio ? URL.createObjectURL(audio) : '';
  }

  onMount(() => {
    supported = Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
    recognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (recognitionClass && 'processLocally' in recognitionClass.prototype
      && typeof recognitionClass.available === 'function') local = 'unchecked';
  });

  async function checkDictation() {
    if (local !== 'unchecked') return;
    let timeout;
    try {
      local = await Promise.race([
        recognitionClass.available(language),
        new Promise(resolve => { timeout = window.setTimeout(() => resolve('unchecked'), 1200); }),
      ]);
    } catch {
      local = 'unsupported';
    } finally {
      window.clearTimeout(timeout);
    }
  }

  async function installLanguage() {
    installing = true;
    message = '';
    try {
      const installed = await recognitionClass.install(language);
      if (disposed) return;
      local = installed ? 'available' : 'downloadable';
      if (!installed) message = 'The English dictation pack could not be installed.';
    } catch {
      if (!disposed) message = 'The browser could not install the English dictation pack.';
    } finally {
      installing = false;
    }
  }

  function clean(current) {
    window.clearInterval(current.timer);
    if (current.recognition) {
      current.recognition.onend = null;
      current.recognition.onerror = null;
      current.recognition.onresult = null;
      try { current.recognition.abort(); } catch { /* The recognizer may already be closed. */ }
    }
    for (const track of current.stream.getTracks()) track.stop();
  }

  function cancel() {
    const current = attempt;
    attempt = null;
    if (current) {
      current.recorder.onstop = null;
      if (current.recorder.state === 'recording') {
        try { current.recorder.stop(); } catch { /* The stream may have already ended. */ }
      }
      clean(current);
    }
  }

  function prepareDictation(current) {
    if (local !== 'available') return;
    try {
      const recognition = new recognitionClass();
      current.recognition = recognition;
      recognition.lang = 'en-US';
      recognition.processLocally = true;
      recognition.continuous = true;
      recognition.interimResults = true;
      current.dictationEnded = new Promise(resolve => {
        recognition.onend = resolve;
        recognition.onerror = resolve;
      });
      recognition.onresult = event => {
        current.words = Array.from(event.results, result => result[0].transcript).join(' ').trim();
      };
      recognition.start(current.stream.getAudioTracks()[0]);
    } catch {
      current.recognition = null;
      current.dictationEnded = null;
      message = 'On-device dictation could not start. You can enter the transcript yourself.';
    }
  }

  function stop() {
    if (!attempt || attempt.recorder.state !== 'recording') return;
    phase = 'finishing';
    try { attempt.recognition?.stop(); } catch { /* The recognizer may already be closed. */ }
    attempt.recorder.stop();
  }

  async function finish(current) {
    window.clearInterval(current.timer);
    if (current.dictationEnded) {
      await new Promise(resolve => {
        const fallback = window.setTimeout(resolve, 1100);
        current.dictationEnded.then(() => {
          window.clearTimeout(fallback);
          resolve();
        });
      });
    }
    if (attempt !== current || disposed) return;
    clean(current);
    attempt = null;
    phase = 'idle';
    if (!current.bytes || current.bytes > MAX_BYTES) {
      message = current.bytes ? 'The recording is too large. Try a shorter take.' : 'The browser captured no audio. Try again.';
      return;
    }
    const type = current.parts[0].type || current.recorder.mimeType;
    const blob = new Blob(current.parts, { type });
    onChange({ audio: blob, transcript: current.words ? current.words.slice(0, 6000) : transcript });
    message = current.words ? 'Replay your recording and check the transcript.' : 'Recording ready. Add a transcript for tutor feedback.';
  }

  async function record() {
    if (phase !== 'idle' || !supported || disabled) return;
    message = '';
    phase = 'starting';
    let stream;
    try {
      window.speechSynthesis?.cancel();
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!disposed) await checkDictation();
      if (disposed) {
        for (const track of stream.getTracks()) track.stop();
        return;
      }
      const mimeType = formats.find(format => MediaRecorder.isTypeSupported?.(format));
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType, audioBitsPerSecond: 48000 } : {});
      const current = { recorder, stream, parts: [], bytes: 0, words: '', started: Date.now() };
      attempt = current;
      recorder.ondataavailable = event => {
        if (attempt !== current || !event.data.size) return;
        current.bytes += event.data.size;
        if (current.bytes <= MAX_BYTES) current.parts.push(event.data);
        else stop();
      };
      recorder.onerror = () => {
        if (attempt !== current) return;
        cancel();
        phase = 'idle';
        message = 'Recording failed. Check the microphone and try again.';
      };
      recorder.onstop = () => { void finish(current); };
      recorder.start(500);
      phase = 'recording';
      elapsed = 0;
      prepareDictation(current);
      current.timer = window.setInterval(() => {
        elapsed = Math.floor((Date.now() - current.started) / 1000);
        if (elapsed >= MAX_SECONDS) stop();
      }, 250);
    } catch (err) {
      for (const track of stream?.getTracks() ?? []) track.stop();
      if (disposed) return;
      cancel();
      phase = 'idle';
      message = err.name === 'NotAllowedError' ? 'Allow microphone access to record. You can also type your answer.'
        : 'Could not start recording. Check your microphone or type your answer.';
    }
  }

  onDestroy(() => {
    disposed = true;
    cancel();
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  });
</script>

<div class="space-y-2">
  <div class="flex flex-wrap items-center gap-2">
    {#if phase === 'recording'}
      <button type="button" class="ui-button border-rose-400 bg-rose-950 text-rose-100" on:click={stop}>
        Stop recording · {elapsed}s
      </button>
    {:else}
      <button type="button" disabled={disabled || !supported || active} on:click={record}
        class="ui-button">
        {phase === 'starting' ? 'Opening microphone…' : phase === 'finishing' ? 'Preparing recording…' : audio ? 'Record again' : 'Record answer'}
      </button>
    {/if}
    {#if local === 'downloadable' && typeof recognitionClass?.install === 'function'}
      <button type="button" class="ui-button ui-quiet" disabled={installing || active || disabled} on:click={installLanguage}>
        {installing ? 'Installing…' : 'Install on-device English dictation'}
      </button>
    {/if}
  </div>
  {#if !supported}<p class="text-xs text-slate-400">Recording is unavailable in this browser. Type or paste a transcript.</p>{/if}
  {#if audioUrl}
    <audio controls preload="metadata" src={audioUrl} class="w-full" aria-label={'Recording for attempt ' + number}></audio>
    <button type="button" disabled={disabled || active} on:click={() => onChange({ audio: null })} class="ui-button ui-quiet">
      Remove this recording
    </button>
  {/if}
  {#if message}<p role="status" class="text-xs text-amber-100">{message}</p>{/if}
  <label class="ui-label">
    {number === 1 ? 'Answer or transcript' : 'Second answer or transcript'}
    <textarea value={transcript} on:input={event => onChange({ transcript: event.currentTarget.value })}
      maxlength="6000" rows="3" disabled={disabled || active}
      class="ui-input"
      placeholder="Speak, type, or paste your response in English."></textarea>
  </label>
</div>
