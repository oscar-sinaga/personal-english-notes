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

  // Lexicon state
  let vocabularies = [];
  let newTerm = "";
  let newDef = "";
  let vocabStatus = "";

  const API_URL = "http://localhost:8000/api";

  onMount(async () => {
    if (syllabusData.length > 0) {
      expandedBlocks[syllabusData[0].id] = true;
    }
    fetchProgress();
    fetchVocab();
  });

  async function fetchProgress() {
    try {
      const res = await fetch(`${API_URL}/progress`);
      const data = await res.json();
      if (data && data.length > 0) {
        data.forEach(d => { progressMap[d.module_name] = d.is_completed; });
        progressMap = progressMap; 
      }
    } catch (e) { console.error("Failed to fetch progress.", e); }
  }

  async function fetchVocab() {
    try {
      const res = await fetch(`${API_URL}/vocabulary`);
      vocabularies = await res.json();
    } catch (e) { console.error("Failed to fetch vocab.", e); }
  }

  async function addVocab() {
    if (!newTerm.trim() || !newDef.trim()) return;
    try {
      const res = await fetch(`${API_URL}/vocabulary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ term: newTerm, definition: newDef })
      });
      if (res.ok) {
        newTerm = "";
        newDef = "";
        fetchVocab();
        vocabStatus = "Saved!";
        setTimeout(() => vocabStatus = "", 3000);
      }
    } catch (e) {
      console.error(e);
    }
  }

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
        alert(`Time's up for ${pillars[currentPillarIndex]} phase!`);
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
    exportStatus = "Saving...";
    try {
      const sanitizedFolder = selectedTopic.replace(/[^a-zA-Z0-9_\- ]/g, "").replace(/\s+/g, "_");
      const res = await fetch(`${API_URL}/export-log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_folder: sanitizedFolder, pillar: logPillar, content: logContent })
      });
      const data = await res.json();
      exportStatus = `Saved in IDE: ${data.filepath.split('\\').pop()}`;
      logContent = "";
      setTimeout(() => { exportStatus = "" }, 5000);
    } catch (e) {
      exportStatus = "Failed to save.";
    }
  }

  // Calculate Progress
  $: totalNodes = syllabusData.reduce((acc, block) => {
    let blockCount = 0;
    block.children.forEach(ch => {
      blockCount += ch.children.length > 0 ? ch.children.length : 1;
    });
    return acc + blockCount;
  }, 0);
  
  $: completedNodes = Object.values(progressMap).filter(Boolean).length;
  $: progressPercent = totalNodes > 0 ? Math.round((completedNodes / totalNodes) * 100) : 0;
</script>

<main class="min-h-screen bg-slate-950 font-sans text-slate-100 p-4 md:p-6 lg:h-screen lg:overflow-hidden flex flex-col">
  
  <!-- Top Navbar -->
  <header class="flex justify-between items-center bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl mb-6 flex-shrink-0">
    <div class="flex items-center gap-4">
      <div class="h-10 w-10 bg-teal-500/20 text-teal-400 rounded-lg flex items-center justify-center border border-teal-500/30">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
      </div>
      <div>
        <h1 class="text-xl md:text-2xl font-bold tracking-tight text-white">Credit Risk Learning Dashboard</h1>
        <p class="text-xs text-slate-400 font-mono tracking-wider">PORTFOLIO TRACKER & LEXICON SYSTEM</p>
      </div>
    </div>
    <div class="text-right">
      <div class="text-xs text-slate-400 mb-1">OVERALL COMPLETION RISK</div>
      <div class="flex items-center gap-3">
        <div class="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
          <div class="h-full bg-teal-500 rounded-full transition-all duration-500" style="width: {progressPercent}%"></div>
        </div>
        <span class="font-mono font-bold {progressPercent > 50 ? 'text-teal-400' : 'text-amber-400'}">{progressPercent}%</span>
      </div>
    </div>
  </header>

  <!-- 3-Column Dashboard Layout -->
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 overflow-hidden">
    
    <!-- Left Column: Syllabus Tree (Scrollable) -->
    <section class="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full overflow-hidden">
      <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">Course Syllabus</h2>
      
      <div class="overflow-y-auto pr-2 custom-scrollbar flex-1">
        {#each syllabusData as block}
          <div class="mb-2">
            <button class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-all text-left group cursor-pointer" on:click={() => toggleBlock(block.id)}>
              <span class="text-slate-500 text-xs transition-transform duration-300 {expandedBlocks[block.id] ? 'rotate-90 text-teal-400' : ''}">▶</span>
              <strong class="text-slate-200 text-sm">{block.name}</strong>
            </button>
            
            {#if expandedBlocks[block.id]}
              <div class="ml-3 mt-1 pl-3 border-l-2 border-slate-800 flex flex-col gap-1 pb-2">
                {#each block.children as chapter}
                  <div class="mt-1">
                    <button class="w-full flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-slate-800 transition-colors text-left group cursor-pointer" on:click={() => toggleChapter(chapter.id)}>
                      <span class="text-slate-600 text-[10px] transition-transform duration-300 {expandedChapters[chapter.id] ? 'rotate-90 text-teal-400' : ''}">▶</span>
                      <span class="text-slate-300 text-sm truncate" title={chapter.name}>{chapter.name}</span>
                    </button>

                    {#if expandedChapters[chapter.id]}
                      <div class="ml-4 mt-1 pl-3 border-l border-dashed border-slate-700 flex flex-col gap-1">
                        {#each chapter.children as sub}
                          <label class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-800 cursor-pointer transition-colors group">
                            <input type="checkbox" class="w-3.5 h-3.5 rounded border-slate-600 text-teal-500 bg-slate-900 cursor-pointer" checked={progressMap[sub.id]} on:change={() => toggleNode(sub.id)} />
                            <span class="text-xs text-slate-400 group-hover:text-slate-200 transition-colors {progressMap[sub.id] ? 'line-through opacity-50' : ''} truncate">{sub.name}</span>
                          </label>
                        {/each}
                        {#if chapter.children.length === 0}
                          <label class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-800 cursor-pointer transition-colors">
                            <input type="checkbox" class="w-3.5 h-3.5 rounded border-slate-600 text-teal-500 bg-slate-900 cursor-pointer" checked={progressMap[chapter.id]} on:change={() => toggleNode(chapter.id)} />
                            <span class="text-xs text-slate-400 {progressMap[chapter.id] ? 'line-through opacity-50' : ''}">Mark complete</span>
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

    <!-- Center Column: Main Operations (Timer & Logger) -->
    <section class="lg:col-span-6 flex flex-col gap-6 h-full overflow-y-auto custom-scrollbar pr-2">
      
      <!-- Timer Panel -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-teal-500 to-sky-500"></div>
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider">Phase Controller</h2>
          <span class="px-3 py-1 bg-slate-800 rounded-full text-xs font-mono text-teal-400 border border-slate-700">{pillars[currentPillarIndex]}</span>
        </div>
        
        <div class="text-center">
          <div class="text-7xl font-black tracking-tight tabular-nums text-white mb-6 font-mono drop-shadow-[0_0_10px_rgba(20,184,166,0.3)]">
            {formatTime(timeRemaining)}
          </div>
          <div class="flex justify-center gap-3">
            {#if !timerActive}
              <button class="px-6 py-2 rounded-lg font-bold bg-teal-500 hover:bg-teal-400 text-slate-950 transition-colors cursor-pointer" on:click={startTimer}>Start Run</button>
            {:else}
              <button class="px-6 py-2 rounded-lg font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-colors cursor-pointer" on:click={pauseTimer}>Halt</button>
            {/if}
            <button class="px-6 py-2 rounded-lg font-bold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors cursor-pointer disabled:opacity-50" on:click={resetTimer}>Reset</button>
            <button class="px-6 py-2 rounded-lg font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 transition-colors cursor-pointer disabled:opacity-50" on:click={nextPillar} disabled={currentPillarIndex === 2}>Next Stage</button>
          </div>
        </div>
      </div>

      <!-- Logger Panel -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex-1 flex flex-col">
        <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">Documentation Input</h2>
        
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div class="flex flex-col gap-1.5">
            <label for="topic" class="text-xs text-slate-500">Mapping Topic:</label>
            <select id="topic" bind:value={selectedTopic} class="bg-slate-950 border border-slate-800 text-slate-300 text-sm rounded-lg py-2 px-3 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 cursor-pointer outline-none">
              {#each syllabusData as block}
                <option value={block.id}>{block.name}</option>
              {/each}
            </select>
          </div>
          <div class="flex flex-col gap-1.5">
            <label for="pillar" class="text-xs text-slate-500">Activity Type:</label>
            <select id="pillar" bind:value={logPillar} class="bg-slate-950 border border-slate-800 text-slate-300 text-sm rounded-lg py-2 px-3 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 cursor-pointer outline-none">
              <option value="Active_Writing">Active Writing</option>
              <option value="Circumlocution">Circumlocution</option>
              <option value="Role_Play">Role-Play Summary</option>
            </select>
          </div>
        </div>
        
        <div class="flex-1 flex flex-col min-h-[250px]">
          <textarea id="content" bind:value={logContent} class="flex-1 w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg p-4 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none resize-none" placeholder="Draft your technical summary here... (Markdown supported)"></textarea>
        </div>
        
        <div class="mt-4 flex items-center justify-between">
          <button class="px-6 py-2 rounded-lg font-bold bg-white text-slate-900 hover:bg-slate-200 transition-colors disabled:opacity-50 cursor-pointer" on:click={submitLog} disabled={!logContent.trim()}>
            Save to IDE
          </button>
          {#if exportStatus}
            <span class="text-teal-400 text-sm flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>
              {exportStatus}
            </span>
          {/if}
        </div>
      </div>
    </section>

    <!-- Right Column: Lexicon Bank -->
    <section class="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full overflow-hidden">
      <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2 flex justify-between items-center">
        Technical Lexicon
        <span class="bg-slate-800 text-slate-300 text-xs px-2 py-0.5 rounded-full">{vocabularies.length} terms</span>
      </h2>
      
      <!-- Add New Term -->
      <div class="bg-slate-950 border border-slate-800 rounded-lg p-3 mb-4">
        <input type="text" bind:value={newTerm} placeholder="Risk Term (e.g. LGD)" class="w-full bg-transparent border-b border-slate-800 text-sm text-slate-200 px-1 py-2 mb-2 focus:border-teal-500 outline-none">
        <textarea bind:value={newDef} rows="2" placeholder="English definition/circumlocution..." class="w-full bg-transparent text-sm text-slate-300 px-1 py-1 focus:outline-none resize-none mb-2"></textarea>
        <div class="flex justify-between items-center">
          <button class="text-xs bg-slate-800 hover:bg-slate-700 text-white px-3 py-1.5 rounded cursor-pointer transition-colors" on:click={addVocab}>+ Add Term</button>
          {#if vocabStatus} <span class="text-teal-400 text-xs">{vocabStatus}</span> {/if}
        </div>
      </div>

      <!-- Lexicon List (Scrollable) -->
      <div class="overflow-y-auto pr-2 custom-scrollbar flex-1 flex flex-col gap-3">
        {#if vocabularies.length === 0}
          <div class="text-center text-slate-600 text-sm mt-4 italic">No terms added yet.</div>
        {/if}
        {#each vocabularies as v}
          <div class="bg-slate-800/40 border border-slate-800 rounded-lg p-3 group hover:border-slate-700 transition-colors">
            <h3 class="font-bold text-teal-400 text-sm mb-1 group-hover:text-teal-300">{v.term}</h3>
            <p class="text-slate-400 text-xs leading-relaxed">{v.definition}</p>
          </div>
        {/each}
      </div>
    </section>
  </div>
</main>
