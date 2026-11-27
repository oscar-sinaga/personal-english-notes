<script>
  import { onMount, tick } from 'svelte';
  import 'pdfjs-dist/web/pdf_viewer.css';
  import { MAX_BOOK_EXCERPT, MIN_BOOK_EXCERPT } from '../practice.js';

  export let url;
  export let title;
  export let filename;
  export let page = 1;
  export let expanded = false;
  export let onExcerpt;

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
  let selectedExcerpt = '';
  let sendingExcerpt = false;
  let textDialog;
  let textField;
  let textPage = 0;
  let pageText = '';
  let pageTextError = '';
  let textChoiceError = '';
  let loadingPageText = false;
  let textRequest = 0;

  $: requestedPage = page;
  $: selectionError = excerptError(selectedExcerpt);
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

  export async function leaveFullscreenForTutor() {
    if (!expanded) return;
    expanded = false;
    controlsVisible = false;
    if (document.fullscreenElement === reader) {
      await document.exitFullscreen().catch(() => {});
    }
  }

  function handleKeydown(event) {
    if (!expanded || textDialog?.open || event.key !== 'Escape') return;
    event.preventDefault();
    exitFullscreen();
  }

  onMount(() => {
    const viewport = viewer;
    loadBook();
    document.addEventListener('fullscreenchange', syncFullscreen);
    document.addEventListener('selectionchange', readPdfSelection);
    viewport.addEventListener('pointerdown', beginPdfSelection);
    return () => {
      live = false;
      document.removeEventListener('fullscreenchange', syncFullscreen);
      document.removeEventListener('selectionchange', readPdfSelection);
      viewport.removeEventListener('pointerdown', beginPdfSelection);
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
    selectedExcerpt = '';
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

  function excerptError(text) {
    if (text.length < MIN_BOOK_EXCERPT) return 'Select at least 10 characters to ask the tutor.';
    if (text.length > MAX_BOOK_EXCERPT) return 'Select a shorter passage of up to 4,000 characters.';
    return '';
  }

  function readPdfSelection() {
    if (readyPage !== page || textDialog?.open) return;
    const selection = window.getSelection();
    if (!selection?.rangeCount || selection.isCollapsed) return;
    const range = selection.getRangeAt(0);
    if (textContainer.contains(range.startContainer) && textContainer.contains(range.endContainer)) {
      selectedExcerpt = selection.toString().trim();
    }
  }

  function beginPdfSelection(event) {
    if (event.button === 0) selectedExcerpt = '';
  }

  async function shareExcerpt(excerpt, number) {
    if (sendingExcerpt) return false;
    sendingExcerpt = true;
    try {
      return await onExcerpt({ page: number, excerpt });
    } finally {
      sendingExcerpt = false;
    }
  }

  async function askAboutSelection() {
    readPdfSelection();
    if (readyPage !== page || excerptError(selectedExcerpt)) return;
    if (await shareExcerpt(selectedExcerpt, page)) {
      selectedExcerpt = '';
      const selection = window.getSelection();
      if (textContainer?.contains(selection?.anchorNode)) selection.removeAllRanges();
    }
  }

  async function openPageText() {
    if (readyPage !== page) return;
    const id = ++textRequest;
    const number = page;
    textPage = number;
    pageText = '';
    pageTextError = '';
    textChoiceError = '';
    loadingPageText = true;
    textDialog.showModal();
    try {
      const sourcePage = await documentProxy.getPage(number);
      const content = await sourcePage.getTextContent();
      if (!live || id !== textRequest || !textDialog.open) return;
      pageText = content.items.map(item => 'str' in item
        ? item.str + (item.hasEOL ? '\n' : '') : '').join('').trim();
      if (!pageText) pageTextError = 'This PDF page has no selectable text. You can paste an excerpt in Reading notes.';
    } catch {
      if (live && id === textRequest) pageTextError = 'Could not load the page text. Close this panel and try again.';
    } finally {
      if (live && id === textRequest) {
        loadingPageText = false;
        await tick();
        if (textDialog.open && textField) {
          textField.focus();
          textField.setSelectionRange(0, 0);
        }
      }
    }
  }

  async function askFromPageText() {
    const excerpt = pageText.slice(textField.selectionStart, textField.selectionEnd).trim();
    textChoiceError = excerptError(excerpt);
    if (textChoiceError) {
      textField.focus();
      return;
    }
    textDialog.close();
    if (!(await shareExcerpt(excerpt, textPage)) && live) {
      textDialog.showModal();
      textField.focus();
    }
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
  <div class="study-actions flex shrink-0 flex-wrap items-center gap-x-3 gap-y-2 border-b border-slate-700 bg-slate-900 px-3 py-2"
    hidden={expanded && !controlsVisible && !selectedExcerpt}>
    <p role="status" class="min-w-36 flex-1 text-sm text-slate-300">
      {selectedExcerpt ? selectionError || 'Selection ready · PDF page ' + page : 'Highlight a sentence to ask the tutor.'}
    </p>
    <div class="ml-auto flex flex-wrap items-center gap-2">
      <button type="button" class="reader-button min-h-11" aria-haspopup="dialog"
        on:click={openPageText} disabled={readyPage !== page || sendingExcerpt}>Page text</button>
      <button type="button" class="rounded-lg bg-teal-400 px-3 py-2 text-sm font-semibold text-slate-950 min-h-11
        hover:bg-teal-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-300
        disabled:bg-slate-800 disabled:text-slate-400"
        on:mousedown|preventDefault on:click={askAboutSelection}
        disabled={readyPage !== page || !!selectionError || sendingExcerpt}>Ask tutor</button>
    </div>
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

  <dialog bind:this={textDialog} aria-labelledby="pdf-text-title"
    class="m-auto max-h-[90dvh] w-[min(94vw,38rem)] overflow-auto rounded-xl border border-slate-600 bg-slate-900 p-4 text-slate-100 backdrop:bg-slate-950/80">
    <div class="flex items-center justify-between gap-3">
      <h2 id="pdf-text-title" class="text-base font-semibold">PDF page {textPage} text</h2>
      <button type="button" class="reader-button min-h-11" on:click={() => textDialog.close()}>Close</button>
    </div>
    {#if loadingPageText}
      <p role="status" class="mt-3 text-sm">Loading page text…</p>
    {:else if pageTextError}
      <p role="status" class="mt-3 text-sm text-slate-300">{pageTextError}</p>
    {:else}
      <p id="pdf-select-help" class="mt-3 text-sm text-slate-300">Select the passage you want to study. You can edit this copy of the page.</p>
      <textarea aria-label="Text from PDF page" aria-describedby="pdf-select-help" bind:this={textField}
        bind:value={pageText} rows="10" class="my-3 w-full rounded-lg border border-slate-600 bg-slate-950 p-3 text-sm leading-relaxed"></textarea>
      <button type="button" class="min-h-11 rounded-lg bg-teal-400 px-3 py-2 text-sm font-semibold text-slate-950
        focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-300"
        on:click={askFromPageText}>Use selected text</button>
      {#if textChoiceError}<p role="alert" class="mt-2 text-sm text-amber-200">{textChoiceError}</p>{/if}
    {/if}
  </dialog>
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
  .reader-expanded .study-actions,
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
  .study-actions[hidden] { display: none; }
  .reader-expanded .study-actions {
    top: max(.5rem, env(safe-area-inset-top));
    inset-inline: max(.5rem, env(safe-area-inset-left)) max(.5rem, env(safe-area-inset-right));
    width: fit-content;
    margin-inline: auto;
    border-radius: .75rem;
  }
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
  .reader-button:focus-visible, .reader-viewport:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--color-teal-300);
    outline-offset: -2px;
  }
</style>
