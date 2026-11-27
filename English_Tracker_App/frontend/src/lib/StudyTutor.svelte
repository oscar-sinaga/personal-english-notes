<script>
  import { onMount } from 'svelte';
  import { requestJson } from '../practice.js';
  import SpeechAttempt from './SpeechAttempt.svelte';
  import SpeechPlayback from './SpeechPlayback.svelte';
  import VoicePrompt from './VoicePrompt.svelte';

  export let initialMode = 'speaking';
  export let aiEnabled = false;
  export let topicId = 'General';
  export let topicLabel = 'Credit risk';
  export let context = 'Study';
  export let book = '';
  export let page = null;

  const modes = { speaking: 'Speaking', listening: 'Listening', shadowing: 'Shadowing', roleplay: 'Role-play', case: 'Credit Risk Case Lab', excerpt: 'Ask about this excerpt' };
  const button = 'rounded-lg border border-slate-700 px-3 py-2 text-xs font-medium disabled:opacity-50';
  const accent = 'rounded-lg bg-teal-400 px-3 py-2 text-xs font-semibold text-slate-950 disabled:opacity-50';
  const input = 'w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-sm text-slate-100';
  const empty = () => ({ transcript: '', audio: null, feedback: null });
  const hasTake = take => Boolean(take.transcript.trim() || take.audio);
  const reading = initialMode === 'excerpt';
  let mode = initialMode;
  let lesson;
  let summary;
  let lessonTopic = '';
  let lessonTitle = '';
  let sourceBook = book || 'anderson';
  let sourcePage = page ?? '';
  let inheritedPage = page;
  let excerpt = '';
  let scenario = 'interviewer';
  let caseId = 'expected-loss';
  let cases = [];
  let caseNotes = '';
  let takes = [empty(), empty()];
  let firstActive = false;
  let secondActive = false;
  let retry = false;
  let showTranscript = false;
  let playable = false;
  let saved = false;
  let pendingId;
  let busy = '';
  let error = '';
  let status = '';

  $: listening = lesson?.mode === 'listening';
  $: hasFirst = hasTake(takes[0]);
  $: recording = firstActive || secondActive;
  $: if (reading && !lesson && !excerpt && book) sourceBook = book;
  $: if (reading && !lesson && !excerpt && page !== inheritedPage) {
    if (!sourcePage || sourcePage === inheritedPage) sourcePage = page ?? '';
    inheritedPage = page;
  }
  $: dirty = !saved && Boolean(lesson || excerpt.trim() || recording || takes.some(hasTake));

  onMount(() => {
    if (mode === 'case') loadCases();
    const warnUnsaved = event => {
      if (dirty || busy) {
        event.preventDefault();
        event.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', warnUnsaved);
    return () => window.removeEventListener('beforeunload', warnUnsaved);
  });

  export function canLeave() {
    if (busy) {
      status = 'Wait for the current request to finish before leaving this exercise.';
      return false;
    }
    return !dirty || window.confirm('Discard this unsaved guided practice?');
  }

  function post(path, json) {
    return requestJson('/tutor/' + path, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(json),
    });
  }

  async function loadCases() {
    if (cases.length || busy) return;
    busy = 'cases';
    error = '';
    try {
      cases = await requestJson('/tutor/cases');
    } catch (problem) {
      error = problem.message;
    } finally {
      busy = '';
    }
  }

  function reset() {
    lesson = undefined;
    summary = undefined;
    caseNotes = '';
    takes = [empty(), empty()];
    retry = false;
    showTranscript = false;
    saved = false;
    pendingId = undefined;
  }

  function switchMode(event) {
    const next = event.currentTarget.value;
    if (!canLeave()) {
      event.currentTarget.value = mode;
      return;
    }
    reset();
    mode = next;
    error = '';
    status = '';
    if (next === 'case') loadCases();
  }

  function useLesson(result, explanation, targetId = topicId, targetTitle = topicLabel) {
    reset();
    lesson = result;
    summary = explanation;
    lessonTopic = targetId || 'General';
    lessonTitle = targetTitle || lessonTopic;
  }

  async function start() {
    if (busy || recording || (lesson && !canLeave())) return;
    error = '';
    status = '';
    if (mode === 'case') {
      const chosen = cases.find(item => item.id === caseId);
      if (chosen) useLesson({ mode, case_id: chosen.id, question: chosen.question, script: chosen.scenario });
      return;
    }
    if (!aiEnabled) return;
    busy = 'lesson';
    const targetId = topicId;
    const topic = topicLabel || topicId;
    try {
      if (reading) {
        const data = await post('excerpt', { book: sourceBook, page: Number(sourcePage), excerpt });
        useLesson(data.lesson, data.summary, targetId, topic);
      } else {
        const data = await post('lesson', { mode, topic, scenario });
        useLesson(data, undefined, targetId, topic);
      }
    } catch (problem) {
      error = problem.message;
    } finally {
      busy = '';
    }
  }

  function changeTake(index, changes) {
    if (busy || saved) return;
    const previous = takes[index];
    // Feedback always belongs to the exact text sent to the tutor.
    const next = { ...previous, ...changes };
    if ('transcript' in changes && next.transcript !== previous.transcript) next.feedback = null;
    takes = takes.map((item, j) => j === index ? next : item);
    status = '';
  }

  async function getFeedback(index) {
    const answer = takes[index].transcript.trim();
    if (!answer || !lesson || busy || recording || !aiEnabled || saved) return;
    busy = 'feedback' + index;
    error = '';
    status = '';
    try {
      const output = await post('feedback', { lesson, answer });
      takes = takes.map((item, j) => j === index ? { ...item, feedback: output.feedback } : item);
      caseNotes = output.case_notes || caseNotes;
      if (listening) showTranscript = true;
    } catch (problem) {
      error = problem.message;
    } finally {
      busy = '';
    }
  }

  async function nextRolePlay() {
    const recent = [...takes].reverse().find(take => take.feedback?.follow_up);
    if (!recent || recording || !canLeave()) return;
    busy = 'lesson';
    error = '';
    status = '';
    try {
      const result = await post('lesson', {
        mode: 'roleplay', topic: lessonTitle, scenario: lesson.scenario,
        follow_up: recent.feedback.follow_up, prior_answer: recent.transcript.slice(0, 2000),
      });
      useLesson(result, undefined, lessonTopic, lessonTitle);
    } catch (problem) {
      error = problem.message;
    } finally {
      busy = '';
    }
  }

  async function save() {
    if (!lesson || saved || busy || recording || (!hasFirst && (!summary || hasTake(takes[1])))) return;
    busy = 'save';
    error = '';
    status = '';
    try {
      pendingId ??= crypto.randomUUID();
      const selectedTakes = hasFirst ? takes.slice(0, hasTake(takes[1]) ? 2 : 1) : [];
      const form = new FormData();
      form.append('data', JSON.stringify({
        topic_id: lessonTopic, context, lesson, summary: summary ?? null,
        attempts: selectedTakes.map(({ transcript, feedback }) => ({ transcript, feedback })),
      }));
      selectedTakes.forEach(({ audio }, index) => {
        if (audio) form.append('audio' + (index + 1), audio, 'attempt-' + (index + 1));
      });
      await requestJson('/tutor/practice/' + pendingId, { method: 'PUT', body: form });
      saved = true;
      status = 'Saved to Practice Journal. Review it there anytime.';
    } catch (problem) {
      error = problem.message;
    } finally {
      busy = '';
    }
  }
</script>

<section class="space-y-4 rounded-xl border border-slate-700 bg-slate-900/70 p-3 text-sm text-slate-100" aria-label={reading ? 'Book tutor' : 'Guided practice'}>
  <div class="flex flex-wrap items-center justify-between gap-1">
    <h3 class="font-semibold">{reading ? 'Ask about this excerpt' : modes[mode]}</h3>
    {#if !reading && lesson}
      <span class="text-xs text-slate-400">{lessonTitle}</span>
    {/if}
  </div>

  <fieldset disabled={Boolean(busy) || recording} class="space-y-3">
    {#if reading}
      <div class="grid grid-cols-2 gap-2">
        <label class="grid gap-1 text-xs text-slate-300">Book
          <select bind:value={sourceBook} class={input}><option value="anderson">Anderson</option><option value="siddiqi">Siddiqi</option></select>
        </label>
        <label class="grid gap-1 text-xs text-slate-300">PDF page
          <input bind:value={sourcePage} type="number" min="1" max="10000" step="1" class={input} inputmode="numeric" />
        </label>
      </div>
      <label class="grid gap-1 text-xs text-slate-300">Book excerpt
        <textarea bind:value={excerpt} maxlength="4000" rows="4" class={input} placeholder="Paste the passage you want to discuss."></textarea>
      </label>
    {:else}
      <label class="grid max-w-sm gap-1 text-xs text-slate-300">Exercise mode
        <select value={mode} on:change={switchMode} class={input}>
          {#each Object.entries(modes).filter(([id]) => id !== 'excerpt') as [value, name] (value)}
            <option {value}>{name}</option>
          {/each}
        </select>
      </label>
      {#if mode === 'roleplay'}
        <label class="grid max-w-sm gap-1 text-xs text-slate-300">Tutor role
          <select bind:value={scenario} class={input}>
            <option value="interviewer">Credit risk interviewer</option>
            <option value="senior-analyst">Senior risk analyst</option>
          </select>
        </label>
      {:else if mode === 'case'}
        <label class="grid max-w-sm gap-1 text-xs text-slate-300">Case
          <select bind:value={caseId} class={input}>
            {#each cases as item (item.id)}<option value={item.id}>{item.title}</option>{/each}
          </select>
        </label>
        {#if !cases.length}<button type="button" class={button} on:click={loadCases}>Load cases</button>{/if}
      {/if}
    {/if}
    <div class="flex flex-wrap gap-2">
      <button type="button" class={accent} on:click={start}
        disabled={mode === 'case' ? !cases.length : !aiEnabled || (reading && (!sourcePage || excerpt.trim().length < 10))}>
        {busy === 'lesson' ? 'Preparing…' : reading ? 'Explain excerpt' : mode === 'case' ? 'Open case' : 'Generate exercise'}
      </button>
      {#key lesson || mode}
        <VoicePrompt topic={lessonTitle || topicLabel || topicId} {lesson} attempts={takes}
          draftSource={reading ? { book: sourceBook, page: sourcePage, excerpt } : undefined} />
      {/key}
    </div>
    {#if !aiEnabled && mode !== 'case'}
      <p class="text-xs text-slate-400">Choose Codex or Claude in the English AI Assistant settings to generate a lesson.</p>
    {/if}
  </fieldset>

  {#if lesson}
    {#if lesson.source}
      <p class="rounded-md bg-slate-800 px-2 py-1 text-xs text-teal-200">{lesson.source.book === 'anderson' ? 'Anderson' : 'Siddiqi'} · PDF page {lesson.source.page}</p>
    {/if}
    {#if summary}
      <dl class="grid gap-2 text-xs leading-relaxed">
        <div><dt class="font-semibold text-teal-300">Konsep</dt><dd class="whitespace-pre-wrap break-words">{summary.concept}</dd></div>
        <div><dt class="font-semibold text-teal-300">Simple English</dt><dd class="whitespace-pre-wrap break-words">{summary.simple_english}</dd></div>
        <div><dt class="font-semibold text-teal-300">Useful phrases</dt><dd class="whitespace-pre-wrap break-words">{summary.phrases}</dd></div>
        <div><dt class="font-semibold text-teal-300">Illustration</dt><dd class="whitespace-pre-wrap break-words">{summary.example}</dd></div>
      </dl>
      <details class="text-xs text-slate-300"><summary class="cursor-pointer">Source excerpt</summary><p class="mt-2 whitespace-pre-wrap break-words">{lesson.source.excerpt}</p></details>
    {:else if lesson.script && (!listening || showTranscript)}
      <p class="whitespace-pre-wrap break-words rounded-lg bg-slate-950 p-3 leading-relaxed">{lesson.script}</p>
    {/if}

    <h4 class="font-semibold">{reading ? 'Explain it back' : 'Your challenge'}</h4>
    <p class="break-words">{lesson.question}</p>
    {#key lesson}
      <SpeechPlayback text={listening || lesson.mode === 'shadowing' || reading ? lesson.script : lesson.question}
        label={listening ? 'Play passage' : lesson.mode === 'shadowing' ? 'Play model sentence' : reading ? 'Listen to simple English' : 'Play question'}
        replayBySentence={listening && showTranscript} disabled={recording} bind:playable />
    {/key}
    {#if listening && !showTranscript}
      <button type="button" class={button} disabled={playable && !hasFirst} on:click={() => showTranscript = true}>
        {playable ? 'Reveal transcript' : 'Read instead'}
      </button>
      {#if playable && !hasFirst}<span class="text-xs text-slate-400">Answer first, then check the transcript.</span>{/if}
    {/if}

    {#key lesson}
      <div class="space-y-4">
        {#each takes as take, index (index)}
          {#if index === 0 || retry}
            <div class="space-y-2 rounded-lg border border-slate-700 p-2.5">
              <h5 class="text-xs font-semibold text-teal-200">Attempt {index + 1}</h5>
              {#if index === 0}
                <SpeechAttempt number={1} transcript={take.transcript} audio={take.audio} bind:active={firstActive}
                  disabled={Boolean(busy) || saved || secondActive} onChange={value => changeTake(0, value)} />
              {:else}
                <SpeechAttempt number={2} transcript={take.transcript} audio={take.audio} bind:active={secondActive}
                  disabled={Boolean(busy) || saved || firstActive} onChange={value => changeTake(1, value)} />
              {/if}
              <button type="button" class={button} on:click={() => getFeedback(index)}
                disabled={Boolean(busy) || recording || saved || !aiEnabled || !take.transcript.trim()}>
                {busy === 'feedback' + index ? 'Checking…' : 'Get tutor feedback'}
              </button>
              {#if take.feedback}
                <dl class="grid gap-2 text-xs leading-relaxed">
                  <div><dt class="font-semibold text-teal-300">{lesson.mode === 'shadowing' ? 'Wording' : 'Concept or comprehension'}</dt><dd class="whitespace-pre-wrap break-words">{take.feedback.concept_feedback}</dd></div>
                  <div><dt class="font-semibold text-teal-300">English feedback</dt><dd class="whitespace-pre-wrap break-words">{take.feedback.english_feedback}</dd></div>
                  <div><dt class="font-semibold text-teal-300">A natural answer</dt><dd class="whitespace-pre-wrap break-words">{take.feedback.natural_answer}</dd></div>
                </dl>
                {#if index === 0 && !retry && !saved}
                  <button type="button" class={accent} on:click={() => retry = true}>Try again</button>
                {/if}
              {:else if index === 0 && hasFirst && !retry && !saved}
                <button type="button" class={button} disabled={recording || Boolean(busy)} on:click={() => retry = true}>Try again</button>
              {/if}
            </div>
          {/if}
        {/each}
      </div>
    {/key}

    {#if caseNotes}
      <details class="rounded-lg border border-slate-700 p-2 text-xs">
        <summary class="cursor-pointer font-semibold">Case reasoning</summary>
        <p class="mt-2 leading-relaxed">{caseNotes}</p>
      </details>
    {/if}
    <div class="flex flex-wrap gap-2">
      <button type="button" class={accent} on:click={save}
        disabled={saved || Boolean(busy) || recording || (!hasFirst && (!summary || hasTake(takes[1])))}>
        {busy === 'save' ? 'Saving…' : 'Save to Practice Journal'}
      </button>
      {#if lesson.mode === 'roleplay' && takes.some(take => take.feedback?.follow_up)}
        <button type="button" class={button} on:click={nextRolePlay} disabled={Boolean(busy) || recording || !aiEnabled}>Continue role-play</button>
      {/if}
    </div>
  {/if}
  {#if error}<p role="alert" class="break-words text-xs text-rose-200">{error}</p>{/if}
  {#if status}<p role="status" class="break-words text-xs text-slate-200">{status}</p>{/if}
</section>
