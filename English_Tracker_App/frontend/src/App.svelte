<script>
  import { onMount } from 'svelte';
  import syllabusData from './syllabus.json';

  let progressMap = {};
  let expandedBlocks = {};
  let expandedChapters = {};

  let timerActive = false;
  let timeRemaining = 20 * 60; 
  let currentPillarIndex = 0;
  const pillars = ["Active Writing", "Thinking & Circumlocution", "Role-Play"];
  let interval;

  let selectedTopic = syllabusData.length > 0 ? syllabusData[0].id : "";
  let logContent = "";
  let logPillar = "Active_Writing";
  let exportStatus = "";

  const API_URL = "http://localhost:8000/api";

  onMount(async () => {
    if (syllabusData.length > 0) {
      expandedBlocks[syllabusData[0].id] = true;
    }
    try {
      const res = await fetch(`${API_URL}/progress`);
      const data = await res.json();
      if (data && data.length > 0) {
        data.forEach(d => { progressMap[d.module_name] = d.is_completed; });
        progressMap = progressMap; 
      }
    } catch (e) { console.error("Failed to fetch progress.", e); }
  });

  async function toggleNode(id) {
    const newState = !(progressMap[id] || false);
    progressMap[id] = newState;
    progressMap = progressMap; 
    try {
      await fetch(`${API_URL}/progress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ module_name: id, is_completed: newState })
      });
    } catch (e) { console.error(e); }
  }

  function toggleBlock(id) { expandedBlocks[id] = !expandedBlocks[id]; }
  function toggleChapter(id) { expandedChapters[id] = !expandedChapters[id]; }

  function startTimer() {
    if (timerActive) return;
    timerActive = true;
    interval = setInterval(() => {
      if (timeRemaining > 0) { timeRemaining--; } 
      else {
        clearInterval(interval);
        timerActive = false;
        alert(`Waktu Habis untuk fase ${pillars[currentPillarIndex]}!`);
      }
    }, 1000);
  }
  function pauseTimer() { timerActive = false; clearInterval(interval); }
  function nextPillar() {
    if (currentPillarIndex < 2) {
      currentPillarIndex++;
      timeRemaining = 20 * 60;
      pauseTimer();
    }
  }
  function resetTimer() {
    currentPillarIndex = 0;
    timeRemaining = 20 * 60;
    pauseTimer();
  }
  function formatTime(secs) {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  async function submitLog() {
    exportStatus = "Menyimpan...";
    try {
      const sanitizedFolder = selectedTopic.replace(/[^a-zA-Z0-9_\- ]/g, "").replace(/\s+/g, "_");
      const res = await fetch(`${API_URL}/export-log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_folder: sanitizedFolder, pillar: logPillar, content: logContent })
      });
      const data = await res.json();
      exportStatus = `Tersimpan di: ${data.filepath}`;
      logContent = "";
      setTimeout(() => { exportStatus = "" }, 5000);
    } catch (e) {
      exportStatus = "Gagal menyimpan log.";
    }
  }
</script>

<main class="max-w-4xl mx-auto p-4 md:p-8 font-sans text-slate-100">
  <header class="mb-10 text-center">
    <h1 class="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-400 drop-shadow-sm mb-3">Credit Intelligence Tracker</h1>
    <p class="text-slate-400 text-lg">Interactive Syllabus & Active English Habit Builder</p>
  </header>

  <!-- Syllabus Tree Section -->
  <section class="bg-slate-900/40 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-2xl mb-8">
    <h2 class="text-2xl font-bold text-sky-400 mb-6 flex items-center gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
      Syllabus Progress (Level 3)
    </h2>
    <div class="flex flex-col gap-2 max-h-[500px] overflow-y-auto pr-4">
      {#each syllabusData as block}
        <div class="block-node">
          <button class="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-slate-800/40 hover:bg-sky-900/20 border border-transparent hover:border-sky-500/30 transition-all text-left group cursor-pointer" on:click={() => toggleBlock(block.id)}>
            <span class="text-slate-500 group-hover:text-sky-400 transition-transform duration-300 {expandedBlocks[block.id] ? 'rotate-90 text-sky-400' : ''}">▶</span>
            <strong class="text-sky-300 text-lg">{block.name}</strong>
          </button>
          
          {#if expandedBlocks[block.id]}
            <div class="ml-4 mt-2 pl-4 border-l-2 border-sky-500/20 flex flex-col gap-2 pb-3 animate-in">
              {#each block.children as chapter}
                <div class="chapter-node">
                  <button class="w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition-colors text-left group cursor-pointer" on:click={() => toggleChapter(chapter.id)}>
                    <span class="text-slate-500 text-sm transition-transform duration-300 {expandedChapters[chapter.id] ? 'rotate-90 text-sky-400' : ''}">▶</span>
                    <span class="text-slate-200">{chapter.name}</span>
                  </button>

                  {#if expandedChapters[chapter.id]}
                    <div class="ml-6 mt-1 pl-4 border-l border-dashed border-white/10 flex flex-col gap-1 py-2 animate-in">
                      {#each chapter.children as sub}
                        <label class="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 cursor-pointer transition-colors group">
                          <input type="checkbox" class="w-4 h-4 rounded border-slate-600 text-sky-500 focus:ring-sky-500 focus:ring-offset-slate-900 bg-slate-800 cursor-pointer" checked={progressMap[sub.id]} on:change={() => toggleNode(sub.id)} />
                          <span class="text-sm text-slate-300 group-hover:text-white transition-colors {progressMap[sub.id] ? 'line-through opacity-50' : ''}">{sub.name}</span>
                        </label>
                      {/each}
                      {#if chapter.children.length === 0}
                        <label class="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 cursor-pointer transition-colors">
                          <input type="checkbox" class="w-4 h-4 rounded border-slate-600 text-sky-500 focus:ring-sky-500 focus:ring-offset-slate-900 bg-slate-800 cursor-pointer" checked={progressMap[chapter.id]} on:change={() => toggleNode(chapter.id)} />
                          <span class="text-sm text-slate-300 {progressMap[chapter.id] ? 'line-through opacity-50' : ''}">Mark chapter as completed</span>
                        </label>
                      {/if}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </section>

  <!-- Timer Section -->
  <section class="bg-gradient-to-br from-slate-800/80 to-slate-900/90 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl mb-8 text-center relative overflow-hidden">
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1 bg-gradient-to-r from-transparent via-sky-500 to-transparent opacity-50"></div>
    
    <h2 class="text-2xl font-bold text-sky-400 mb-2 flex items-center justify-center gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      Habit Timer: {pillars[currentPillarIndex]}
    </h2>
    
    <div class="text-7xl md:text-8xl font-black my-6 tracking-tight tabular-nums text-transparent bg-clip-text bg-gradient-to-br from-sky-300 to-indigo-500 drop-shadow-[0_0_15px_rgba(56,189,248,0.4)]">
      {formatTime(timeRemaining)}
    </div>
    
    <div class="flex flex-wrap justify-center gap-4 mt-8">
      {#if !timerActive}
        <button class="px-6 py-3 rounded-xl font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30 hover:bg-sky-500/30 hover:shadow-[0_0_15px_rgba(56,189,248,0.3)] transition-all flex items-center gap-2 cursor-pointer" on:click={startTimer}>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" /></svg>
          Start
        </button>
      {:else}
        <button class="px-6 py-3 rounded-xl font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 transition-all flex items-center gap-2 cursor-pointer" on:click={pauseTimer}>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
          Pause
        </button>
      {/if}
      <button class="px-6 py-3 rounded-xl font-semibold bg-slate-600/20 text-slate-300 border border-slate-600/40 hover:bg-slate-600/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer" on:click={resetTimer} disabled={currentPillarIndex === 0 && timeRemaining === 20*60}>
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" /></svg>
        Reset
      </button>
      <button class="px-6 py-3 rounded-xl font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 hover:bg-indigo-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer" on:click={nextPillar} disabled={currentPillarIndex === 2}>
        Next Phase
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
      </button>
    </div>
  </section>

  <!-- Logger Section -->
  <section class="bg-slate-900/40 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-2xl">
    <h2 class="text-2xl font-bold text-sky-400 mb-6 flex items-center gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
      Active English Logger
    </h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <div class="flex flex-col gap-2">
        <label for="topic" class="text-sm font-medium text-slate-300">Topic Folder:</label>
        <div class="relative">
          <select id="topic" bind:value={selectedTopic} class="w-full appearance-none bg-slate-800/80 border border-slate-600 text-slate-200 rounded-lg py-3 px-4 pr-10 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-shadow cursor-pointer">
            {#each syllabusData as block}
              <option value={block.id}>{block.name}</option>
            {/each}
          </select>
          <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
            <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
          </div>
        </div>
      </div>
      
      <div class="flex flex-col gap-2">
        <label for="pillar" class="text-sm font-medium text-slate-300">Pillar Phase:</label>
        <div class="relative">
          <select id="pillar" bind:value={logPillar} class="w-full appearance-none bg-slate-800/80 border border-slate-600 text-slate-200 rounded-lg py-3 px-4 pr-10 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-shadow cursor-pointer">
            <option value="Active_Writing">1. Active Writing</option>
            <option value="Circumlocution">2. Thinking & Circumlocution</option>
            <option value="Role_Play">3. Role-Play (Transcript)</option>
          </select>
          <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
            <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
          </div>
        </div>
      </div>
    </div>
    
    <div class="flex flex-col gap-2">
      <div class="flex justify-between items-end">
        <label for="content" class="text-sm font-medium text-slate-300">Log Content (Markdown supported):</label>
      </div>
      <textarea id="content" bind:value={logContent} rows="8" class="w-full bg-slate-800/60 border border-slate-600 text-slate-200 rounded-xl p-4 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-shadow resize-y" placeholder="Type your 20-minute output here..."></textarea>
    </div>
    
    <div class="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
      <button class="w-full sm:w-auto px-8 py-3 rounded-xl font-bold bg-gradient-to-r from-sky-500 to-indigo-500 text-white shadow-lg shadow-sky-500/20 hover:shadow-sky-500/40 hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2 cursor-pointer" on:click={submitLog} disabled={!logContent.trim()}>
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
        Export & Save .md
      </button>
      
      {#if exportStatus}
        <div class="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm animate-in flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>
          {exportStatus}
        </div>
      {/if}
    </div>
  </section>
</main>
