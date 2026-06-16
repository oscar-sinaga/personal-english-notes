<script>
  import { onMount } from 'svelte';

  // State for modules
  let modules = [
    { name: "Module A: Introduction", is_completed: false },
    { name: "Module B: The Histories", is_completed: false },
    { name: "Module C: Credit Lifecycle", is_completed: false },
    { name: "Module D: Toolbox", is_completed: false },
    { name: "Module E: Organizing", is_completed: false },
    { name: "Module F: Packing", is_completed: false },
    { name: "Module G: Making the Trip", is_completed: false }
  ];

  // State for Timer
  let timerActive = false;
  let timeRemaining = 20 * 60; // 20 minutes
  let currentPillarIndex = 0;
  const pillars = ["Active Writing", "Thinking & Circumlocution", "Role-Play"];
  let interval;

  // State for Logger
  let selectedTopic = "01_Block_A_Introduction";
  let logContent = "";
  let logPillar = "Active_Writing";
  let exportStatus = "";

  const API_URL = "http://localhost:8000/api";

  onMount(async () => {
    try {
      const res = await fetch(`${API_URL}/progress`);
      const data = await res.json();
      if (data && data.length > 0) {
        modules = modules.map(m => {
          const found = data.find(d => d.module_name === m.name);
          if (found) m.is_completed = found.is_completed;
          return m;
        });
      }
    } catch (e) {
      console.error("Failed to fetch progress. Is backend running?", e);
    }
  });

  async function toggleModule(mod) {
    mod.is_completed = !mod.is_completed;
    modules = modules; 
    try {
      await fetch(`${API_URL}/progress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ module_name: mod.name, is_completed: mod.is_completed })
      });
    } catch (e) {
      console.error(e);
    }
  }

  function startTimer() {
    if (timerActive) return;
    timerActive = true;
    interval = setInterval(() => {
      if (timeRemaining > 0) {
        timeRemaining--;
      } else {
        clearInterval(interval);
        timerActive = false;
        alert(`Waktu Habis untuk fase ${pillars[currentPillarIndex]}!`);
      }
    }, 1000);
  }

  function pauseTimer() {
    timerActive = false;
    clearInterval(interval);
  }

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
      const res = await fetch(`${API_URL}/export-log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic_folder: selectedTopic,
          pillar: logPillar,
          content: logContent
        })
      });
      const data = await res.json();
      exportStatus = `Tersimpan di: ${data.filepath}`;
      logContent = "";
    } catch (e) {
      console.error(e);
      exportStatus = "Gagal menyimpan log (Pastikan backend berjalan).";
    }
  }
</script>

<main>
  <h1 class="text-neon">Credit Intelligence Tracker</h1>
  <p>Lacak progres 7 Module Anda, pantau waktu 60 Menit (3 Pillar), dan log jurnal bahasa Inggris secara langsung!</p>

  <div class="glass-panel">
    <h2 class="text-neon">Syllabus Progress</h2>
    <div style="display: flex; flex-direction: column; gap: 0.5rem;">
      {#each modules as mod}
        <label style="display: flex; align-items: center; gap: 1rem; cursor: pointer;">
          <input type="checkbox" style="width: auto; margin:0;" checked={mod.is_completed} on:change={() => toggleModule(mod)} />
          <span style="opacity: {mod.is_completed ? 0.5 : 1}; text-decoration: {mod.is_completed ? 'line-through' : 'none'}">{mod.name}</span>
        </label>
      {/each}
    </div>
  </div>

  <div class="glass-panel" style="text-align: center;">
    <h2 class="text-neon">Habit Timer: {pillars[currentPillarIndex]}</h2>
    <div style="font-size: 4rem; font-weight: bold; margin: 1rem 0; font-variant-numeric: tabular-nums;">
      {formatTime(timeRemaining)}
    </div>
    <div style="display: flex; gap: 1rem; justify-content: center;">
      {#if !timerActive}
        <button on:click={startTimer}>Start</button>
      {:else}
        <button on:click={pauseTimer}>Pause</button>
      {/if}
      <button on:click={resetTimer} disabled={currentPillarIndex === 0 && timeRemaining === 20*60}>Reset</button>
      <button on:click={nextPillar} disabled={currentPillarIndex === 2}>Next Pillar</button>
    </div>
  </div>

  <div class="glass-panel">
    <h2 class="text-neon">Active English Logger</h2>
    <div style="display: flex; gap: 1rem;">
      <div style="flex: 1;">
        <label for="topic" style="display: block; margin-bottom: 0.5rem;">Topic Folder:</label>
        <select id="topic" bind:value={selectedTopic}>
          <option value="01_Block_A_Introduction">01_Block_A_Introduction</option>
          <option value="02_Block_B_Histories">02_Block_B_Histories</option>
          <option value="03_Block_C_Lifecycle">03_Block_C_Lifecycle</option>
          <option value="04_Block_D_Toolbox">04_Block_D_Toolbox</option>
          <option value="05_Block_E_Organizing">05_Block_E_Organizing</option>
        </select>
      </div>
      <div style="flex: 1;">
        <label for="pillar" style="display: block; margin-bottom: 0.5rem;">Pillar Phase:</label>
        <select id="pillar" bind:value={logPillar}>
          <option value="Active_Writing">1. Active Writing</option>
          <option value="Circumlocution">2. Thinking & Circumlocution</option>
          <option value="Role_Play">3. Role-Play (Transcript)</option>
        </select>
      </div>
    </div>
    
    <label for="content" style="display: block; margin-top: 1rem; margin-bottom: 0.5rem;">Log Content (Markdown supported):</label>
    <textarea id="content" bind:value={logContent} rows="8" placeholder="Type your 20-minute output here..."></textarea>
    
    <div style="display: flex; align-items: center; justify-content: space-between;">
      <button on:click={submitLog} disabled={!logContent.trim()}>Export & Save .md</button>
      {#if exportStatus}
        <span style="color: #4ade80; font-size: 0.9em; max-width: 50%; text-align: right;">{exportStatus}</span>
      {/if}
    </div>
  </div>
</main>
