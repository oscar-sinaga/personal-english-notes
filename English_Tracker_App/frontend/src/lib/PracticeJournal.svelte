<script>
  import { onDestroy, onMount, tick } from 'svelte';
  import StudyReview from './StudyReview.svelte';
  import { apiUrl, contexts, requestJson, skills, statuses } from '../practice.js';

  export let close;
  export let openEntry;

  const emptyFilters = () => ({ q: '', skill: '', context: '', status: '', start: '', end: '' });
  let dialog;
  let heading;
  let filters = emptyFilters();
  let applied = '';
  let entries = [];
  let nextOffset = null;
  let loading = false;
  let error = '';
  let study;
  let returnFocusId;
  let request;

  onMount(() => {
    dialog.showModal();
    heading.focus();
    applyFilters();
  });

  onDestroy(() => request?.abort());

  function applyFilters() {
    applied = new URLSearchParams(Object.entries(filters).filter(([, value]) => value)).toString();
    loadPage(0);
  }

  function clearFilters() {
    filters = emptyFilters();
    applyFilters();
  }

  async function loadPage(offset) {
    request?.abort();
    const current = new AbortController();
    request = current;
    loading = true;
    error = '';
    try {
      const query = new URLSearchParams(applied);
      query.set('offset', offset);
      const data = await requestJson('/practice?' + query, { signal: current.signal });
      if (current.signal.aborted) return;
      entries = offset ? [...entries, ...data.items] : data.items;
      nextOffset = data.next_offset;
    } catch (issue) {
      if (!current.signal.aborted) error = issue.message;
    } finally {
      if (!current.signal.aborted) loading = false;
    }
  }

  function edit(entry) {
    if (openEntry(entry)) dialog.close();
  }

  function showStudy(event, selection) {
    returnFocusId = event.currentTarget.id;
    study = selection;
    dialog.scrollTop = 0;
  }

  async function backFromStudy() {
    study = undefined;
    await tick();
    document.getElementById(returnFocusId)?.focus();
  }
</script>

<dialog bind:this={dialog} on:close={close} aria-labelledby="practice-journal-title" class="ui-dialog">
  <div class="ui-dialog-header">
    <h2 id="practice-journal-title" bind:this={heading} tabindex="-1" class="ui-dialog-title">Practice journal</h2>
    <div class="ui-actions">
      {#if !study}
        <button type="button" id="journal-review" class="ui-button ui-primary" on:click={event => showStudy(event, { mode: 'review' })}>Review practice</button>
      {/if}
      <button type="button" class="ui-button ui-quiet" on:click={() => dialog.close()}>Close</button>
    </div>
  </div>

  {#if study}
    <StudyReview mode={study.mode} entryId={study.id || ''} back={backFromStudy} />
  {:else}
    <form class="my-4 grid gap-3" on:submit|preventDefault={applyFilters}>
      <div>
        <label for="journal-search" class="ui-label">Search topic, notes, or feedback</label>
        <div class="mt-1.5 flex gap-2">
          <input id="journal-search" class="ui-input flex-1" type="search" bind:value={filters.q} maxlength="200" />
          <button class="ui-button" disabled={loading}>Search</button>
        </div>
      </div>
      <details class="ui-details rounded-lg border border-slate-700 px-3">
        <summary class="text-sm font-medium text-slate-300">Filters and export</summary>
        <div class="grid gap-3 pb-3 sm:grid-cols-2">
          <div class="ui-label">
            <label for="journal-skill">Skill</label>
            <select class="ui-input" id="journal-skill" bind:value={filters.skill}>
              <option value="">All skills</option>
              {#each skills as skill}<option value={skill}>{skill}</option>{/each}
            </select>
          </div>
          <div class="ui-label">
            <label for="journal-context">Context</label>
            <select class="ui-input" id="journal-context" bind:value={filters.context}>
              <option value="">All contexts</option>
              {#each contexts as context}<option value={context}>{context}</option>{/each}
            </select>
          </div>
          <label class="ui-label">Created from
            <input type="date" bind:value={filters.start} max={filters.end || undefined} class="ui-input" />
          </label>
          <label class="ui-label">Created through
            <input type="date" bind:value={filters.end} min={filters.start || undefined} class="ui-input" />
          </label>
          <div class="ui-label">
            <label for="journal-status">Status</label>
            <select class="ui-input" id="journal-status" bind:value={filters.status}>
              <option value="">All statuses</option>
              {#each Object.entries(statuses) as [value, label]}<option {value}>{label}</option>{/each}
            </select>
          </div>
          <div class="ui-actions sm:col-span-2">
            <button class="ui-button" disabled={loading}>Apply filters</button>
            <a class="ui-button ui-quiet" href={apiUrl + '/practice/export.csv?' + applied}>Export filtered journal CSV</a>
            <a class="ui-button ui-quiet" href={apiUrl + '/sessions/export.csv'}>Export study sessions CSV</a>
          </div>
        </div>
      </details>
    </form>

    {#if applied}
      <button type="button" class="ui-button ui-quiet mb-3" on:click={clearFilters} disabled={loading}>Clear search and filters</button>
    {/if}
    {#if error}
      <p role="alert" class="text-sm text-rose-200">{error}</p>
      <button type="button" class="ui-button mt-2" on:click={() => loadPage(0)}>Retry</button>
    {/if}
    {#if loading}<p role="status" class="text-sm text-slate-300">Loading journal…</p>{/if}
    {#if !entries.length && !loading && !error}
      <p class="rounded-lg border border-slate-700 p-4 text-sm text-slate-300">
        {applied ? 'No practice matches these filters.' : 'Saved exercises will appear here.'}
      </p>
    {/if}
    <div class="grid gap-3" aria-busy={loading}>
      {#each entries as entry (entry.id)}
        <article class="rounded-xl border border-slate-700 bg-slate-950 p-4">
          <h3 class="wrap-anywhere text-base font-semibold">{entry.topic_id}</h3>
          <p class="mt-1 text-sm text-slate-400">{entry.skill} · {entry.context} · {statuses[entry.status]} · <time datetime={entry.created_at}>{entry.created_at.slice(0, 10)}</time></p>
          <p class="mt-2 line-clamp-2 whitespace-pre-wrap wrap-anywhere text-sm leading-relaxed text-slate-200">{entry.content}</p>
          <div class="ui-actions mt-3">
            {#if entry.guided}
              <button type="button" id={'journal-details-' + entry.id} class="ui-button"
                on:click={event => showStudy(event, { mode: 'details', id: entry.id })}>Study details</button>
              <button type="button" id={'journal-recall-' + entry.id} class="ui-button"
                on:click={event => showStudy(event, { mode: 'review', id: entry.id })}>Review now</button>
            {:else}
              <button type="button" class="ui-button" on:click={() => edit(entry)}>Open entry</button>
            {/if}
            <a class="ui-button ui-quiet" href={apiUrl + '/practice/' + entry.id + '/markdown'}>Download Markdown</a>
          </div>
        </article>
      {/each}
      {#if nextOffset !== null}
        <button type="button" class="ui-button justify-self-start" on:click={() => loadPage(nextOffset)} disabled={loading}>Load more</button>
      {/if}
    </div>
  {/if}
</dialog>
