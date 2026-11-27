<script>
  import { onMount, onDestroy } from 'svelte';
  import { requestJson } from '../practice.js';
  import SavedLesson from './SavedLesson.svelte';

  export let entryId = '';
  export let mode = 'review';
  export let back;

  let cards = [];
  let card;
  let answer = '';
  let previous;
  let busy = false;
  let error = '';
  let status = '';
  let heading;
  const controller = new AbortController();
  const action = 'ui-button';
  const primary = 'ui-button ui-primary';

  function get(path, options = {}) {
    return requestJson('/tutor/' + path, { ...options, signal: controller.signal });
  }

  async function run(task) {
    if (busy) return;
    busy = true;
    error = '';
    try { await task(); }
    catch (problem) { if (!controller.signal.aborted) error = problem.message; }
    finally { busy = false; }
  }

  function dateLabel(datetime) {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium', timeZone: 'Asia/Jakarta',
    }).format(new Date(datetime));
  }

  onMount(() => {
    heading.focus();
    run(async () => {
      if (mode === 'details') {
        previous = await get('practice/' + entryId);
      } else if (entryId) {
        card = await get('reviews/' + entryId);
      } else {
        cards = await get('reviews');
      }
    });
  });
  onDestroy(() => controller.abort());

  function openCard(selected) {
    card = selected;
    answer = '';
    previous = undefined;
    error = '';
    status = '';
  }

  function reveal() {
    if (!answer.trim()) return;
    run(async () => { previous = await get('practice/' + card.id); });
  }

  function finish(result) {
    if (!previous || !answer.trim()) return;
    run(async () => {
      const saved = await get('reviews/' + card.id, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer, result, version: card.version }),
      });
      status = 'Next review ' + dateLabel(saved.due_at) + ' (WIB).';
      cards = cards.map(item => item.id === card.id ? { ...item, ...saved } : item)
        .sort((a, b) => a.due_at.localeCompare(b.due_at));
      card = undefined;
      answer = '';
      previous = undefined;
    });
  }
</script>

<section class="mt-4 space-y-4" aria-label={mode === 'details' ? 'Saved practice' : 'Review practice'}>
  <div class="flex flex-wrap items-center justify-between gap-2">
    <h3 class="text-base font-semibold" bind:this={heading} tabindex="-1">{mode === 'details' ? 'Saved practice' : 'Review practice'}</h3>
    <button type="button" class={action} disabled={busy} on:click={back}>Back to journal</button>
  </div>
  {#if error}<p role="alert" class="text-sm text-rose-200">{error}</p>{/if}
  {#if status}<p role="status" class="text-sm text-teal-200">{status}</p>{/if}
  {#if busy}<p role="status" class="text-xs text-slate-400">Loading…</p>{/if}
  {#if mode === 'details'}
    {#if previous}
      <p class="text-sm font-semibold">{previous.lesson.question}</p>
      <SavedLesson {entryId} data={previous} />
    {/if}
  {:else if card}
    <p class="text-xs text-slate-400">{card.topic_id} · Review {dateLabel(card.due_at)} (WIB)</p>
    <p class="text-sm font-semibold">{card.question}</p>
    <label class="ui-label">Recall your answer before looking at the original
      <textarea bind:value={answer} disabled={busy} maxlength="6000" rows="4"
        class="ui-input"></textarea>
    </label>
    {#if !previous}
      <button type="button" class={primary} disabled={busy || !answer.trim()} on:click={reveal}>Reveal previous feedback</button>
    {:else}
      <SavedLesson entryId={card.id} data={previous} previous={true} />
      <div class="flex flex-wrap gap-2">
        <button type="button" class={action} disabled={busy || !answer.trim()} on:click={() => finish('again')}>Try again tomorrow</button>
        <button type="button" class={primary} disabled={busy || !answer.trim()} on:click={() => finish('remembered')}>I remembered</button>
      </div>
    {/if}
  {:else if cards.length}
    <ul class="space-y-2">
      {#each cards as item (item.id)}
        <li class="space-y-1 rounded-lg border border-slate-700 p-3">
          <p class="text-sm">{item.question}</p>
          <p class="text-xs text-slate-400">{item.topic_id} · {new Date(item.due_at) <= new Date() ? 'Due now' : dateLabel(item.due_at) + ' (WIB)'}</p>
          <button type="button" class={action} on:click={() => openCard(item)}>Review this practice</button>
        </li>
      {/each}
    </ul>
  {:else if !busy && !error && !status}
    <p class="text-sm text-slate-400">Saved guided practices will appear here for review.</p>
  {/if}
</section>
