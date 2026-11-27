<script>
  import { onMount } from 'svelte';
  import StudyReview from './StudyReview.svelte';
  import { apiUrl, contexts, requestJson, skills, statuses } from '../practice.js';

  export let close;
  export let openEntry;

  let dialog;
  let filters = { q: '', skill: '', context: '', status: '', start: '', end: '' };
  let applied = '';
  let entries = [];
  let nextOffset = null;
  let loading = false;
  let error = '';
  let study;

  onMount(() => {
    dialog.showModal();
    applyFilters();
  });

  function applyFilters() {
    applied = new URLSearchParams(Object.entries(filters).filter(([, value]) => value)).toString();
    loadPage(0);
  }

  async function loadPage(offset) {
    loading = true;
    error = '';
    try {
      const query = new URLSearchParams(applied);
      query.set('offset', offset);
      const data = await requestJson('/practice?' + query);
      entries = offset ? [...entries, ...data.items] : data.items;
      nextOffset = data.next_offset;
    } catch (issue) {
      error = issue.message;
    } finally {
      loading = false;
    }
  }

  function edit(entry) {
    if (openEntry(entry)) dialog.close();
  }
</script>

<dialog bind:this={dialog} on:close={close} aria-labelledby="practice-journal-title" class="m-auto max-h-[90dvh] w-[min(94vw,58rem)] overflow-auto rounded-2xl border border-slate-700 bg-slate-900 p-5 text-slate-100 backdrop:bg-slate-950/80 md:p-7">
  <div class="flex items-center justify-between gap-4">
    <h2 id="practice-journal-title" class="text-xl font-semibold">Practice journal</h2>
    <div class="flex flex-wrap gap-2 justify-end">
      {#if !study}
        <button type="button" class="rounded-lg border border-teal-800 px-3 py-1.5 text-sm text-teal-200" on:click={() => study = { mode: 'review' }}>Review practice</button>
      {/if}
      <button type="button" class="rounded-lg border border-slate-700 px-3 py-1.5 text-sm" on:click={() => dialog.close()}>Close</button>
    </div>
  </div>

  {#if study}
    <StudyReview mode={study.mode} entryId={study.id || ''} back={() => study = null} />
  {:else}
  <form class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" on:submit|preventDefault={applyFilters}>
    <label class="grid gap-1 text-xs text-slate-300">Search topic, notes, or feedback
      <input bind:value={filters.q} maxlength="200" class="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
    </label>
    <label class="grid gap-1 text-xs text-slate-300">Skill
      <select bind:value={filters.skill} class="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
        <option value="">All skills</option>
        {#each skills as skill}<option value={skill}>{skill}</option>{/each}
      </select>
    </label>
    <label class="grid gap-1 text-xs text-slate-300">Context
      <select bind:value={filters.context} class="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
        <option value="">All contexts</option>
        {#each contexts as context}<option value={context}>{context}</option>{/each}
      </select>
    </label>
    <label class="grid gap-1 text-xs text-slate-300">Created from
      <input type="date" bind:value={filters.start} max={filters.end || undefined} class="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
    </label>
    <label class="grid gap-1 text-xs text-slate-300">Created through
      <input type="date" bind:value={filters.end} min={filters.start || undefined} class="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
    </label>
    <label class="grid gap-1 text-xs text-slate-300">Status
      <select bind:value={filters.status} class="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
        <option value="">All statuses</option>
        {#each Object.entries(statuses) as [value, label]}<option {value}>{label}</option>{/each}
      </select>
    </label>
    <button type="submit" class="rounded-lg bg-teal-400 px-3 py-2 text-sm font-semibold text-slate-950 disabled:opacity-60" disabled={loading}>Apply filters</button>
    <a class="rounded-lg border border-slate-700 px-3 py-2 text-center text-sm text-teal-300" href={apiUrl + '/practice/export.csv?' + applied}>Export filtered journal CSV</a>
    <a class="rounded-lg border border-slate-700 px-3 py-2 text-center text-sm text-teal-300" href={apiUrl + '/sessions/export.csv'}>Export study sessions CSV</a>
  </form>

  <div class="mt-5 grid gap-3" aria-live="polite">
    {#if error}<p class="text-sm text-rose-300">{error}</p>{/if}
    {#if loading}<p class="text-sm text-slate-400">Loading journal…</p>{/if}
    {#if !entries.length && !loading && !error}
      <p class="text-sm text-slate-400">No matching entries. Save your first exercise from the dashboard.</p>
    {/if}
    {#each entries as entry (entry.id)}
      <article class="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <h3 class="break-words text-sm font-semibold">{entry.topic_id}</h3>
        <p class="mt-1 text-xs text-slate-400">{entry.skill} · {entry.context} · {statuses[entry.status]} · {entry.created_at.slice(0, 10)}</p>
        <p class="mt-2 line-clamp-2 whitespace-pre-wrap break-words text-sm text-slate-300">{entry.content}</p>
        <div class="mt-3 flex flex-wrap gap-4 text-sm text-teal-300">
          {#if entry.guided}
            <button type="button" class="underline underline-offset-2" on:click={() => study = { mode: 'details', id: entry.id }}>Study details</button>
            <button type="button" class="underline underline-offset-2" on:click={() => study = { mode: 'review', id: entry.id }}>Review now</button>
          {:else}
            <button type="button" class="underline underline-offset-2" on:click={() => edit(entry)}>Open entry</button>
          {/if}
          <a class="underline underline-offset-2" href={apiUrl + '/practice/' + entry.id + '/markdown'}>Download Markdown</a>
        </div>
      </article>
    {/each}
    {#if nextOffset !== null}
      <button type="button" class="rounded-lg border border-slate-700 p-2 text-sm disabled:opacity-60" on:click={() => loadPage(nextOffset)} disabled={loading}>Load more</button>
    {/if}
  </div>
  {/if}
</dialog>
