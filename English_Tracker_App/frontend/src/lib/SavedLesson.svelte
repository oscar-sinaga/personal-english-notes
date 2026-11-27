<script>
  import { apiUrl } from '../practice.js';
  import SpeechPlayback from './SpeechPlayback.svelte';

  export let entryId;
  export let data;
  export let previous = false;
</script>

<div class="space-y-3 break-words">
  {#if data.lesson.source}
    <div class="text-xs text-teal-200">
      {data.lesson.source.book === 'anderson' ? 'Anderson' : 'Siddiqi'} · PDF page {data.lesson.source.page}
    </div>
    <details class="rounded-lg border border-slate-700 p-2 text-xs">
      <summary class="cursor-pointer">Source excerpt</summary>
      <p class="mt-2 whitespace-pre-wrap">{data.lesson.source.excerpt}</p>
    </details>
  {/if}
  {#if data.summary}
    <dl class="space-y-2 text-sm">
      <div><dt class="font-semibold text-teal-300">Konsep</dt><dd class="whitespace-pre-wrap">{data.summary.concept}</dd></div>
      <div><dt class="font-semibold text-teal-300">Simple English</dt><dd class="whitespace-pre-wrap">{data.summary.simple_english}</dd></div>
      <div><dt class="font-semibold text-teal-300">Useful phrases</dt><dd class="whitespace-pre-wrap">{data.summary.phrases}</dd></div>
      <div><dt class="font-semibold text-teal-300">Illustration</dt><dd class="whitespace-pre-wrap">{data.summary.example}</dd></div>
    </dl>
  {:else if data.lesson.script}
    <p class="whitespace-pre-wrap text-sm text-slate-200">{data.lesson.script}</p>
  {/if}
  {#if data.lesson.script}
    <SpeechPlayback text={data.lesson.script} label="Play practice text" replayBySentence={data.lesson.mode === 'listening'} />
  {/if}
  {#if data.case_notes}
    <details class="rounded-lg border border-slate-700 p-2 text-xs">
      <summary class="cursor-pointer">Case reasoning</summary>
      <p class="mt-2">{data.case_notes}</p>
    </details>
  {/if}
  {#each data.attempts as attempt, index (index)}
    <article class="space-y-2 rounded-lg border border-slate-700 p-3 text-sm">
      <h4 class="text-xs font-semibold text-teal-200">{previous ? 'Previous attempt' : 'Attempt'} {index + 1}</h4>
      {#if attempt.transcript}<p class="whitespace-pre-wrap">{attempt.transcript}</p>{/if}
      {#if data.recordings.includes(index + 1)}
        <audio controls preload="metadata" class="w-full"
          aria-label={'Saved recording for attempt ' + (index + 1)}
          src={apiUrl + '/tutor/practice/' + entryId + '/audio/' + (index + 1)}></audio>
      {/if}
      {#if attempt.feedback}
        <dl class="space-y-1.5 text-xs text-slate-300">
          <div><dt class="font-semibold text-teal-300">Concept or comprehension</dt><dd class="whitespace-pre-wrap">{attempt.feedback.concept_feedback}</dd></div>
          <div><dt class="font-semibold text-teal-300">English feedback</dt><dd class="whitespace-pre-wrap">{attempt.feedback.english_feedback}</dd></div>
          <div><dt class="font-semibold text-teal-300">A natural answer</dt><dd class="whitespace-pre-wrap">{attempt.feedback.natural_answer}</dd></div>
        </dl>
      {/if}
    </article>
  {/each}
</div>
