<script>
  export let terms;
  export let term;
  export let definition;
  export let status = '';
  export let aiEnabled = false;
  export let askingAI = false;
  export let saving = false;
  export let exporting = false;
  export let add;
  export let ask;
  export let listen;
  export let download;
</script>

<details class="ui-card ui-details">
  <summary class="ui-title">Technical lexicon <span class="ml-1 text-sm font-normal text-slate-400">({terms.length})</span></summary>
  <form class="my-3 grid gap-3" on:submit|preventDefault={add}>
    <label class="ui-label">Term
      <input class="ui-input" bind:value={term} placeholder="e.g. LGD" disabled={askingAI || saving} required />
    </label>
    <label class="ui-label">Definition
      <textarea class="ui-input" bind:value={definition} rows="2" placeholder="Explain it in your own words" disabled={askingAI || saving}></textarea>
    </label>
    <div class="ui-actions">
      <button class="ui-button ui-primary" disabled={askingAI || saving || !term.trim() || !definition.trim()}>Save term</button>
      {#if aiEnabled}
        <button type="button" class="ui-button" disabled={askingAI || saving || !term.trim()} on:click={ask}>
          {askingAI ? 'Looking up…' : 'Define and save'}
        </button>
      {/if}
      {#if terms.length}
        <button type="button" class="ui-button ui-quiet" on:click={download} disabled={exporting}>
          {exporting ? 'Preparing PDF…' : 'Export PDF'}
        </button>
      {/if}
    </div>
  </form>
  {#if status}<p class="my-2 text-sm text-slate-300" role="status">{status}</p>{/if}
  {#if terms.length}
    <ul class="divide-y divide-slate-700">
      {#each terms as entry (entry.id)}
        <li class="py-3">
          <div class="flex flex-wrap items-center justify-between gap-1">
            <strong class="wrap-anywhere text-sm text-teal-300">{entry.term}</strong>
            <button type="button" class="ui-button ui-quiet" aria-label={'Listen to ' + entry.term} on:click={() => listen(entry.term)}>Listen</button>
          </div>
          <p class="wrap-anywhere whitespace-pre-wrap text-sm leading-relaxed text-slate-300">{entry.definition}</p>
        </li>
      {/each}
    </ul>
  {:else}
    <p class="text-sm text-slate-400">Saved terms appear here.</p>
  {/if}
</details>
