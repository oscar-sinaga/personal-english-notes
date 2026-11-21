<script>
  import { onMount, tick } from 'svelte';
  import 'pdfjs-dist/web/pdf_viewer.css';

  export let url;
  export let title;
  export let filename;
  export let page = 1;
  export let expanded = false;

  const supportUrl = import.meta.env.DEV
    ? '/node_modules/pdfjs-dist/'
    : import.meta.env.BASE_URL + 'assets/pdfjs/';
  let documentProxy;
  let loadingTask;
  let pdfjs;
  let renderTask;
  let textLayer;
  let renderId = 0;
  let live = true;
  let canvas;
  let textContainer;
  let viewer;
  let reader;
  let expandButton;
  let controlsButton;
  let controlsVisible = false;
  let nativeFullscreen = false;
  let width = 0;
  let zoom = 1;
  let sheetWidth = 0;
  let sheetHeight = 0;
  let sheetScale = 1;
  let requestedPage;
  let readyPage = 0;
  let error = '';
  let needsLogin = false;
  let downloadUrl = '';
  let downloadStatus = '';
  let downloadRequest;

  $: requestedPage = page;
  $: if (documentProxy && width && canvas && textContainer) {
    drawPage(documentProxy, page, width, zoom, expanded, canvas, textContainer);
  }

  async function reportError(reason, pageDrawId = renderId) {
    let status = reason?.status;
    if (!status) {
      // A blocked JavaScript worker may fail before PDF.js receives the HTTP status.
      try {
        const access = await fetch(url, { credentials: 'same-origin', headers: { Range: 'bytes=0-0' } });
        status = access.status;
        access.body?.cancel().catch(() => {});
      } catch { /* The network itself may be unavailable. */ }
    }
    if (!live || pageDrawId !== renderId) return;
    needsLogin = status === 401 || status === 403;
    error = needsLogin
      ? 'Your access to this book has expired. Open English Tracker again from ACC.'
      : 'This page could not be loaded. Try again.';
  }

  async function loadBook() {
    error = '';
    needsLogin = false;
    documentProxy = undefined;
    readyPage = 0;
    try {
      await loadingTask?.destroy();
      const [library, worker] = await Promise.all([
        import('pdfjs-dist/legacy/build/pdf.mjs'),
        import('pdfjs-dist/legacy/build/pdf.worker.min.mjs?url')
      ]);
      if (!live) return;
      pdfjs = library;
      pdfjs.GlobalWorkerOptions.workerSrc = worker.default;
      loadingTask = pdfjs.getDocument({
        url, withCredentials: true, disableStream: true, disableAutoFetch: true,
        cMapUrl: supportUrl + 'cmaps/',
        iccUrl: supportUrl + 'iccs/',
        standardFontDataUrl: supportUrl + 'standard_fonts/',
        wasmUrl: supportUrl + 'wasm/',
        useWorkerFetch: true
      });
      const book = await loadingTask.promise;
      if (!live) return;
      page = Math.min(Math.max(1, page), book.numPages);
      documentProxy = book;
    } catch (reason) {
      if (live) await reportError(reason);
    }
  }

  function enterFullscreen() {
    expanded = true;
    controlsVisible = false;
    if (document.fullscreenEnabled && !document.fullscreenElement) {
      // Browsers that decline native fullscreen still use the full viewport.
      reader.requestFullscreen?.().catch(() => {});
    }
    tick().then(() => controlsButton?.focus({ preventScroll: true }));
  }

  async function restoreReader() {
    if (!expanded) return;
    expanded = false;
    controlsVisible = false;
    await tick();
    expandButton?.focus({ preventScroll: true });
  }

  function syncFullscreen() {
    const isNative = document.fullscreenElement === reader;
    if (nativeFullscreen && !isNative) restoreReader();
    nativeFullscreen = isNative;
    if (isNative && !expanded) document.exitFullscreen().catch(() => {});
  }

  async function exitFullscreen() {
    if (document.fullscreenElement === reader) {
      try {
        await document.exitFullscreen();
      } catch {
        return;
      }
    }
    await restoreReader();
  }

  function handleKeydown(event) {
    if (!expanded || event.key !== 'Escape') return;
    event.preventDefault();
    exitFullscreen();
  }

  onMount(() => {
    loadBook();
    document.addEventListener('fullscreenchange', syncFullscreen);
    return () => {
      live = false;
      document.removeEventListener('fullscreenchange', syncFullscreen);
      renderTask?.cancel();
      textLayer?.cancel();
      loadingTask?.destroy().catch(() => {});
      downloadRequest?.abort();
      if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    };
  });

  async function drawPage(book, number, availableWidth, magnification, fullSize, surface, textHost) {
    const id = ++renderId;
    renderTask?.cancel();
    textLayer?.cancel();
    readyPage = 0;
    try {
      const sourcePage = await book.getPage(number);
      if (!live || id !== renderId) return;
      const natural = sourcePage.getViewport({ scale: 1 });
      const fitWidth = Math.max(1, availableWidth - 2);
      const fit = (fullSize ? fitWidth : Math.min(fitWidth, 980)) / natural.width;
      const viewport = sourcePage.getViewport({ scale: fit * magnification });
      // A single canvas keeps phone memory bounded, including at higher zoom.
      const ratio = Math.min(window.devicePixelRatio || 1, 2,
        Math.sqrt(4_000_000 / (viewport.width * viewport.height)),
        4096 / Math.max(viewport.width, viewport.height));
      sheetWidth = viewport.width;
      sheetHeight = viewport.height;
      sheetScale = viewport.scale;
      surface.width = Math.max(1, Math.floor(viewport.width * ratio));
      surface.height = Math.max(1, Math.floor(viewport.height * ratio));
      textHost.replaceChildren();
      renderTask = sourcePage.render({
        canvas: surface, viewport,
        transform: [surface.width / viewport.width, 0, 0, surface.height / viewport.height, 0, 0]
      });
      textLayer = new pdfjs.TextLayer({
        textContentSource: sourcePage.streamTextContent(), container: textHost, viewport
      });
      await Promise.all([renderTask.promise, textLayer.render()]);
      if (live && id === renderId) readyPage = number;
    } catch (reason) {
      if (live && id === renderId && reason.name !== 'RenderingCancelledException') {
        await reportError(reason, id);
      }
    }
  }

  function showPage(next) {
    if (!documentProxy || !Number.isInteger(next)) return;
    error = '';
    needsLogin = false;
    page = Math.min(Math.max(1, next), documentProxy.numPages);
    requestedPage = page;
    viewer.scrollTop = 0;
  }

  async function prepareDownload() {
    downloadRequest = new AbortController();
    downloadStatus = 'Preparing PDF…';
    try {
      const reply = await fetch(url, { credentials: 'same-origin', signal: downloadRequest.signal });
      if (reply.status === 401 || reply.status === 403) {
        downloadStatus = 'Open English Tracker again from ACC to save the file.';
        return;
      }
      if (!reply.ok || !reply.headers.get('content-type')?.startsWith('application/pdf')) {
        throw new Error('PDF unavailable');
      }
      const file = await reply.blob();
      if (live) {
        downloadUrl = URL.createObjectURL(file);
        downloadStatus = '';
      }
    } catch {
      if (live) downloadStatus = 'Download failed. Try again.';
    } finally {
      downloadRequest = undefined;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<section class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-xl"
  class:reader-expanded={expanded} bind:this={reader} aria-label={title + ' reader'}>
  {#if expanded}
    <button type="button" class="reader-button controls-toggle" aria-controls="pdf-toolbar" aria-expanded={controlsVisible}
      bind:this={controlsButton} on:click={() => controlsVisible = !controlsVisible}>
      {controlsVisible ? 'Hide controls' : 'Show controls'}
    </button>
  {/if}
  <div id="pdf-toolbar" class="reader-toolbar flex flex-wrap items-center gap-2 border-b border-slate-800 p-2"
    hidden={expanded && !controlsVisible}>
    <button type="button" class="reader-button" on:click={() => showPage(page - 1)} disabled={!documentProxy || page <= 1}>Previous</button>
    <form class="flex items-center gap-1" on:submit|preventDefault={() => showPage(requestedPage)}>
      <input type="number" aria-label="Page number" class="w-16 rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm"
        min="1" max={documentProxy?.numPages} bind:value={requestedPage} disabled={!documentProxy} />
      <span class="text-sm text-slate-300">/ {documentProxy?.numPages ?? '–'}</span>
      <button class="reader-button" disabled={!documentProxy}>Go</button>
    </form>
    <button type="button" class="reader-button" on:click={() => showPage(page + 1)} disabled={!documentProxy || page >= documentProxy.numPages}>Next</button>
    <div class="flex items-center gap-1">
      <button type="button" class="reader-button" aria-label="Zoom out" on:click={() => zoom -= .25} disabled={!documentProxy || zoom <= 1}>−</button>
      <button type="button" class="reader-button" aria-label="Reset zoom" on:click={() => zoom = 1} disabled={!documentProxy || zoom === 1}>{Math.round(zoom * 100)}%</button>
      <button type="button" class="reader-button" aria-label="Zoom in" on:click={() => zoom += .25} disabled={!documentProxy || zoom >= 2.5}>+</button>
    </div>
    {#if downloadUrl}
      <a class="reader-button text-teal-300" href={downloadUrl} download={filename}>Save PDF</a>
    {:else}
      <button type="button" class="reader-button text-teal-300" on:click={prepareDownload} disabled={!documentProxy || !!downloadRequest}>Prepare download</button>
    {/if}
    {#if expanded}
      <button type="button" class="reader-button" on:click={exitFullscreen}>Exit full screen</button>
    {:else}
      <button type="button" class="reader-button" bind:this={expandButton} on:click={enterFullscreen}>Full screen</button>
    {/if}
    {#if downloadStatus}<span role="status" class="text-sm text-slate-300">{downloadStatus}</span>{/if}
  </div>
  <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard scrolling for the document viewport.) -->
  <div class="reader-viewport relative h-[66dvh] overflow-auto bg-slate-800 lg:h-auto lg:min-h-0 lg:flex-1"
    bind:this={viewer} bind:clientWidth={width} role="region" aria-label={title + ' pages'} tabindex="0">
    {#if error}
      <div class="p-4" role="alert">
        <p class="text-sm text-rose-200">{error}</p>
        {#if needsLogin}<a href="/" class="mt-2 inline-block text-sm text-teal-300 underline">Return to ACC</a>
        {:else}<button type="button" class="reader-button mt-2" on:click={loadBook}>Retry</button>{/if}
      </div>
    {:else if readyPage !== page}
      <p role="status" class="absolute inset-x-0 top-0 z-10 bg-slate-800 p-3 text-sm text-slate-200">Loading {title}…</p>
    {/if}
    <div class="pdf-sheet relative mx-auto bg-white" class:invisible={!!error || readyPage !== page}
      style:width={sheetWidth + 'px'} style:height={sheetHeight + 'px'} style:--total-scale-factor={sheetScale}>
      <canvas bind:this={canvas} class="block h-full w-full" aria-hidden="true"></canvas>
      <div class="textLayer" bind:this={textContainer}></div>
    </div>
  </div>
</section>

<style>
  :global(body:has(.reader-expanded)) {
    overflow: hidden;
  }
  .reader-expanded {
    position: fixed;
    inset: 0;
    z-index: 60;
    width: 100%;
    height: 100dvh;
    border: 0;
    border-radius: 0;
    padding-inline: env(safe-area-inset-left) env(safe-area-inset-right);
  }
  .reader-expanded .reader-viewport {
    height: 100%;
    overscroll-behavior: contain;
  }
  .reader-expanded .reader-toolbar,
  .reader-expanded .controls-toggle {
    position: absolute;
    z-index: 15;
    background: var(--color-slate-950);
    border: 1px solid var(--color-slate-600);
    box-shadow: 0 3px 12px rgb(0 0 0 / 40%);
  }
  .reader-expanded .reader-toolbar {
    bottom: calc(3.5rem + env(safe-area-inset-bottom));
    inset-inline: max(.5rem, env(safe-area-inset-left)) max(.5rem, env(safe-area-inset-right));
    width: fit-content;
    max-height: 50dvh;
    margin-inline: auto;
    overflow: auto;
    border-radius: .75rem;
  }
  .reader-toolbar[hidden] { display: none; }
  .reader-expanded .controls-toggle {
    bottom: max(.5rem, env(safe-area-inset-bottom));
    right: max(.5rem, env(safe-area-inset-right));
    min-height: 44px;
  }
  .reader-button {
    flex-shrink: 0;
    border: 1px solid var(--color-slate-700);
    border-radius: .375rem;
    padding: .4rem .55rem;
    font-size: .875rem;
    line-height: 1.25rem;
  }
  .reader-button:hover:not(:disabled) { background: var(--color-slate-800); }
  .reader-button:disabled { opacity: .45; }
</style>
