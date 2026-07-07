<script>
  import { onMount } from 'svelte';
  import syllabusData from './syllabus.json';
  import { marked } from 'marked';
  import DOMPurify from 'dompurify';
  import markedKatex from 'marked-katex-extension';
  import { draggable } from './draggable.js';

  marked.use(markedKatex({ 
    throwOnError: false,
    output: 'html',
    nonStandard: true
  }));

  function renderMarkdown(text) {
    if (!text) return "";
    let processedText = text
      .replace(/\\\[/g, '\n$$$$\n')
      .replace(/\\\]/g, '\n$$$$\n')
      .replace(/\\\(/g, '$$')
      .replace(/\\\)/g, '$$')
      .replace(/\$\$(.*?)\$\$/gs, '\n$$$$\n$1\n$$$$\n');
      
    return DOMPurify.sanitize(marked.parse(processedText), {
      ADD_TAGS: ['math', 'semantics', 'mrow', 'mi', 'mo', 'mn', 'msup', 'mfrac', 'annotation'],
      ADD_ATTR: ['mathvariant', 'encoding', 'display', 'xmlns', 'aria-hidden', 'class', 'style']
    });
  }

  let progressMap = {};
  let expandedBlocks = {};
  let expandedChapters = {};

  let topicDropdownOpen = false;
  let ddBlocks = {};
  let ddChapters = {};

  let timerActive = false;
  let customMinutes = 20;
  let timeRemaining = customMinutes * 60; 
  let currentPillarIndex = 0;
  const pillars = ["Active Writing", "Thinking & Circumlocution", "Role-Play"];
  let interval;
  let activeTimerPillar = "";
  let elapsedSessionSeconds = 0;

  let selectedTopic = syllabusData.length > 0 ? syllabusData[0].id : "";
  let logContent = "";
  let logPillar = "Active_Writing";
  let exportStatus = "";

  // Lexicon state
  let vocabularies = [];
  let newTerm = "";
  let newDef = "";
  let vocabStatus = "";
  let isAskingAI = false;
  let isExportingPDF = false;

  // Session Stats
  let sessionStats = { total_hours: 0, total_minutes: 0, last_topic: null };
  let sessionStatus = "";
  let weeklyStats = [];

  // App Layout State
  let appMode = "dashboard"; // 'dashboard' or 'reading'
  
  // PDF TOC State
  let tocData = [];
  let tocTree = [];
  let pdfPage = 1;

  // Reading Mode Layout State
  let tocWidth = 320;
  let isResizing = false;
  let companionWidth = 320;
  let isResizingCompanion = false;
  let showGrammarModal = false;
  let showDictionaryModal = false;
  let showInteractionsModal = false;

  let savedInteractions = [];
  let interactionsFilter = "All"; // 'All', 'Chatbot', 'Grammar', 'Explain'
  let isFetchingInteractions = false;
  let showCompanion = false;
  let showToc = true;
  let showHeader = true;
  let doubtContent = "";
  let doubtImageBase64 = null;
  let doubtStatus = "";

  // Chatbot State
  let isChatOpen = false;
  let isChatMaximized = false;
  let chatMessages = [];
  let chatInput = "";
  let isChatLoading = false;
  let chatContainer;


  const API_URL = "http://127.0.0.1:6234/api";

  function buildTocTree(flatToc) {
    let root = [];
    let stack = [{ level: 0, children: root }];
    
    flatToc.forEach((item, index) => {
      const node = { ...item, id: index, children: [], expanded: false };
      
      while (stack[stack.length - 1].level >= item.level) {
        stack.pop();
      }
      
      stack[stack.length - 1].children.push(node);
      stack.push(node);
    });
    
    return root;
  }

  onMount(async () => {
    if (syllabusData.length > 0) {
      expandedBlocks[syllabusData[0].id] = true;
    }
    fetchProgress();
    fetchVocab();
    fetchToc();
    fetchSessionStats();
    fetchWeeklyStats();
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

  async function fetchToc() {
    try {
      const res = await fetch(`${API_URL}/toc`);
      const data = await res.json();
      if (!data.error) {
        tocData = data;
        tocTree = buildTocTree(data);
      }
    } catch (e) { console.error("Failed to fetch TOC.", e); }
  }

  async function fetchSessionStats() {
    try {
      const res = await fetch(`${API_URL}/sessions/stats`);
      sessionStats = await res.json();
    } catch (e) { console.error("Failed to fetch session stats.", e); }
  }

  async function fetchWeeklyStats() {
    try {
      const res = await fetch(`${API_URL}/sessions/weekly`);
      weeklyStats = await res.json();
    } catch (e) { console.error("Failed to fetch weekly stats.", e); }
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
      vocabStatus = "Failed to add term";
      console.error(e);
    }
  }

  async function askAIVocab() {
    if (!newTerm.trim()) {
      vocabStatus = "Enter term first";
      return;
    }
    isAskingAI = true;
    vocabStatus = "Asking AI...";
    try {
      const res = await fetch(`${API_URL}/vocabulary/ai_define`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ term: newTerm })
      });
      if (res.ok) {
        const data = await res.json();
        newDef = data.definition;
        vocabStatus = "AI definition loaded!";
        await addVocab();
      } else {
        vocabStatus = "AI failed";
      }
    } catch (e) {
      console.error(e);
      vocabStatus = "Error connecting to AI";
    } finally {
      isAskingAI = false;
    }
  }

  async function exportVocabPDF() {
    isExportingPDF = true;
    vocabStatus = "Generating PDF...";
    try {
      const res = await fetch(`${API_URL}/vocabulary/export_pdf`);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "Smart_Lexicon.pdf";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        vocabStatus = "PDF Downloaded!";
      } else {
        vocabStatus = "Failed to export PDF";
      }
    } catch (e) {
      console.error(e);
      vocabStatus = "Error exporting PDF";
    } finally {
      isExportingPDF = false;
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

  function toggleDropdownBlock(id) { ddBlocks[id] = !ddBlocks[id]; ddBlocks = ddBlocks; }
  function toggleDropdownChapter(id) { ddChapters[id] = !ddChapters[id]; ddChapters = ddChapters; }
  function selectTopic(id) { selectedTopic = id; topicDropdownOpen = false; }

  function changePdfPage(page) {
    pdfPage = page;
  }

  // --- Resize Handlers (TOC) ---
  function startResize(e) {
    isResizing = true;
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
  }
  function handleResize(e) {
    if (isResizing) {
      // 24px is the left padding of <main>
      let newWidth = e.clientX - 24;
      if (newWidth < 200) newWidth = 200;
      if (newWidth > 800) newWidth = 800;
      tocWidth = newWidth;
    }
  }
  function stopResize() {
    isResizing = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
  }

  // --- Resize Handlers (Companion) ---
  function startResizeCompanion(e) {
    isResizingCompanion = true;
    document.addEventListener('mousemove', handleResizeCompanion);
    document.addEventListener('mouseup', stopResizeCompanion);
  }
  function handleResizeCompanion(e) {
    if (isResizingCompanion) {
      // 24px is the right padding of <main>
      let newWidth = window.innerWidth - e.clientX - 24;
      if (newWidth < 250) newWidth = 250;
      if (newWidth > 800) newWidth = 800;
      companionWidth = newWidth;
    }
  }
  function stopResizeCompanion() {
    isResizingCompanion = false;
    document.removeEventListener('mousemove', handleResizeCompanion);
    document.removeEventListener('mouseup', stopResizeCompanion);
  }

  function startTimer() {
    if (timerActive) return;
    timerActive = true;
    activeTimerPillar = appMode === 'reading' ? "Reading Comprehension" : pillars[currentPillarIndex];
    interval = setInterval(() => {
      if (timeRemaining > 0) { 
        timeRemaining--; 
        elapsedSessionSeconds++;
      } 
      else {
        clearInterval(interval);
        timerActive = false;
        logStudySession();
        alert(`Time's up for ${activeTimerPillar} phase!`);
      }
    }, 1000);
  }
  function pauseTimer() { timerActive = false; clearInterval(interval); }
  function nextPillar() {
    if (elapsedSessionSeconds >= 60) logStudySession();
    if (currentPillarIndex < pillars.length - 1) {
      currentPillarIndex++;
      elapsedSessionSeconds = 0;
      timeRemaining = customMinutes * 60;
      pauseTimer();
    }
  }
  function resetTimer() {
    currentPillarIndex = 0;
    elapsedSessionSeconds = 0;
    timeRemaining = customMinutes * 60;
    pauseTimer();
  }
  function formatTime(secs) {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  async function logStudySession() {
    const elapsedMins = Math.round(elapsedSessionSeconds / 60);
    
    if (elapsedMins <= 0) {
      sessionStatus = "Too short to log (< 1 min).";
      setTimeout(() => sessionStatus = "", 2000);
      return;
    }
    
    sessionStatus = "Saving session...";
    try {
      const res = await fetch(`${API_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          topic_id: selectedTopic || "General", 
          pillar: activeTimerPillar || (appMode === 'reading' ? "Reading Comprehension" : pillars[currentPillarIndex]), 
          duration_minutes: elapsedMins 
        })
      });
      if (res.ok) {
        sessionStatus = `Logged ${elapsedMins} mins!`;
        fetchSessionStats();
        fetchWeeklyStats();
        elapsedSessionSeconds = 0;
        timeRemaining = customMinutes * 60; // Reset timer visually
        pauseTimer();
      } else {
        sessionStatus = "Failed to log.";
      }
    } catch (e) {
      sessionStatus = "Error saving.";
    }
    setTimeout(() => sessionStatus = "", 3000);
  }

  async function submitLog() {
    exportStatus = "Saving...";
    try {
      const sanitizedFolder = selectedTopic.replace(/[^a-zA-Z0-9_\- ]/g, "").replace(/\s+/g, "_") || "General";
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

  async function submitDoubt() {
    doubtStatus = "Sending to IDE...";
    try {
      const sanitizedFolder = selectedTopic.replace(/[^a-zA-Z0-9_\- ]/g, "").replace(/\s+/g, "_") || "General";
      const res = await fetch(`${API_URL}/export-log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_folder: sanitizedFolder, pillar: "Grammar_Doubt", content: doubtContent })
      });
      const data = await res.json();
      doubtStatus = `Saved! Ask Antigravity IDE to check it.`;
      doubtContent = "";
      setTimeout(() => { doubtStatus = "" }, 8000);
    } catch (e) {
      doubtStatus = "Failed.";
    }
  }

  function playAudio(text) {
    try {
      // Menggunakan API Youdao (sangat stabil & bebas token)
      const url = `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(text)}&type=2`;
      const audio = new Audio(url);
      audio.play().catch(e => {
        console.error("Audio error:", e);
        alert("Gagal memutar. Mungkin browser memblokir audio.");
      });
    } catch (e) {
      alert("Gagal memutar suara.");
    }
  }
  // Flat map for topic names
  let topicNames = {};
  let isTranslating = false;
  let translateResult = null;
  let translateMode = 'quick';
  let isCheckingGrammar = false;
  let grammarResult = null;
  let grammarError = "";
  let isExplaining = false;
  let explainResult = null;
  let isRecording = false;
  let isTranscribing = false;
  let mediaRecorder = null;
  let audioChunks = [];

  async function translateDoubt(mode) {
    if (!doubtContent || !doubtContent.trim()) return;
    isTranslating = true;
    translateMode = mode;
    doubtStatus = mode === 'quick' ? "Quick translating..." : "Deep translating...";
    try {
      const res = await fetch(`${API_URL}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: doubtContent, mode: mode })
      });
      const data = await res.json();
      translateResult = data;
      doubtStatus = "Translation complete!";
      setTimeout(() => { doubtStatus = "" }, 3000);
    } catch (e) {
      doubtStatus = "Translation failed.";
      setTimeout(() => { doubtStatus = "" }, 3000);
    } finally {
      isTranslating = false;
    }
  }

  function handlePaste(e) {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        const reader = new FileReader();
        reader.onload = () => {
          doubtImageBase64 = reader.result;
        };
        reader.readAsDataURL(file);
        break;
      }
    }
  }

  async function explainDoubt() {
    if ((!doubtContent || !doubtContent.trim()) && !doubtImageBase64) return;
    isExplaining = true;
    explainResult = { core_concept: "", practical_example: "", analogy: "", english_explanation: "", phrasing_breakdown: "" };
    doubtStatus = "Casting Magic Explain...";
    let rawText = "";

    let textToSend = doubtContent;
    if (!textToSend || !textToSend.trim()) {
      textToSend = "Tolong jelaskan makna, komponen, dan insight dari gambar/grafik ini secara detail.";
    }

    try {
      const res = await fetch(`${API_URL}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToSend, image_base64: doubtImageBase64 })
      });
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        rawText += decoder.decode(value, { stream: true });
        
        const extractSection = (startTag, endTag) => {
          const start = rawText.indexOf(startTag);
          if (start === -1) return "";
          const contentStart = start + startTag.length;
          let end = endTag ? rawText.indexOf(endTag, contentStart) : -1;
          if (end === -1) end = rawText.length;
          return rawText.substring(contentStart, end).trim();
        };

        explainResult = {
          core_concept: extractSection("[CORE_CONCEPT]", "[PRACTICAL_EXAMPLE]"),
          practical_example: extractSection("[PRACTICAL_EXAMPLE]", "[ANALOGY]"),
          analogy: extractSection("[ANALOGY]", "[ENGLISH_EXPLANATION]"),
          english_explanation: extractSection("[ENGLISH_EXPLANATION]", "[PHRASING_BREAKDOWN]"),
          phrasing_breakdown: extractSection("[PHRASING_BREAKDOWN]", null)
        };
      }
      
      doubtStatus = "Magic complete!";
      setTimeout(() => { doubtStatus = "" }, 3000);
    } catch (e) {
      console.error(e);
      doubtStatus = "Magic failed.";
      setTimeout(() => { doubtStatus = "" }, 3000);
    } finally {
      isExplaining = false;
    }
  }

  function scrollToBottom() {
    setTimeout(() => {
      if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 50);
  }

  async function sendChatMessage() {
    if (!chatInput.trim() || isChatLoading) return;
    
    const userMsg = { role: "user", content: chatInput.trim() };
    chatMessages = [...chatMessages, userMsg];
    chatInput = "";
    isChatLoading = true;
    scrollToBottom();
    
    chatMessages = [...chatMessages, { role: "assistant", content: "" }];
    
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: chatMessages.slice(0, -1) })
      });
      
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        chatMessages[chatMessages.length - 1].content += chunk;
        chatMessages = [...chatMessages];
        scrollToBottom();
      }
    } catch (e) {
      console.error(e);
      chatMessages[chatMessages.length - 1].content = `Error: ${e.message || "Network Error"}`;
      chatMessages = [...chatMessages];
    } finally {
      isChatLoading = false;
      scrollToBottom();
    }
  }

  async function checkGrammar() {
    if (!logContent || !logContent.trim()) return;
    isCheckingGrammar = true;
    grammarResult = null;
    grammarError = "";
    
    try {
      const res = await fetch(`${API_URL}/check-grammar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: logContent })
      });
      const data = await res.json();
      if (!res.ok) {
        grammarError = data.detail || "Failed to check grammar.";
      } else {
        grammarResult = data;
      }
    } catch (e) {
      grammarError = "Network error while checking grammar.";
    } finally {
      isCheckingGrammar = false;
    }
  }

  async function toggleDictionary() {
    showDictionaryModal = !showDictionaryModal;
    if (showDictionaryModal && dictResult === null) {
      // maybe fetch random word of the day later
    }
  }

  async function openInteractionsModal() {
    showInteractionsModal = true;
    isFetchingInteractions = true;
    try {
      const res = await fetch(`${API_URL}/interactions`);
      if (res.ok) {
        const data = await res.json();
        savedInteractions = data.interactions || [];
      }
    } catch (e) {
      console.error("Failed to load interactions", e);
    } finally {
      isFetchingInteractions = false;
    }
  }

  async function toggleRecording() {
    if (isRecording) {
      // Stop recording
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
      }
      isRecording = false;
    } else {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          isTranscribing = true;
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          const formData = new FormData();
          formData.append("audio", audioBlob, "recording.webm");

          try {
            const res = await fetch(`${API_URL}/transcribe`, {
              method: "POST",
              body: formData
            });
            const data = await res.json();
            if (res.ok && data.text) {
              // Append or set the text
              logContent = logContent.trim() ? logContent + " " + data.text : data.text;
            } else {
              grammarError = data.detail || "Transcription failed.";
            }
          } catch (e) {
            grammarError = "Network error during transcription.";
          } finally {
            isTranscribing = false;
            // Stop all tracks to release mic
            stream.getTracks().forEach(track => track.stop());
          }
        };

        mediaRecorder.start();
        isRecording = true;
      } catch (err) {
        grammarError = "Mikrofon tidak diizinkan atau tidak ditemukan.";
      }
    }
  }

  $: {
    syllabusData.forEach(block => {
      topicNames[block.id] = block.name;
      block.children.forEach(ch => {
        topicNames[ch.id] = ch.name;
        ch.children.forEach(sub => {
          topicNames[sub.id] = sub.name;
        });
      });
    });
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

<svelte:head>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
</svelte:head>

<main class="h-screen min-h-[800px] bg-slate-950 font-sans text-slate-100 p-4 md:p-6 flex flex-col" style="{isResizing || isResizingCompanion ? 'cursor: col-resize;' : ''}">
  
  <!-- Interactions Modal -->
  {#if showInteractionsModal}
  <div class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
    <div class="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-800/30 rounded-t-xl shrink-0">
        <div>
          <h2 class="text-lg font-bold text-slate-100 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-fuchsia-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
            Saved Learnings
          </h2>
          <p class="text-[11px] text-slate-400 uppercase tracking-widest mt-1">Your AI Interaction History</p>
        </div>
        <div class="flex items-center gap-4">
          <select bind:value={interactionsFilter} class="bg-slate-800 border border-slate-700 text-sm text-slate-300 rounded px-2 py-1 outline-none">
            <option value="All">All Types</option>
            <option value="Chatbot">Chatbot</option>
            <option value="Grammar">Grammar</option>
            <option value="Explain">Magic Explain</option>
          </select>
          <button class="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors" on:click={() => showInteractionsModal = false}>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      </div>
      
      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-6 custom-scrollbar bg-slate-900 rounded-b-xl">
        {#if isFetchingInteractions}
          <div class="text-center py-10 text-slate-400 animate-pulse">Loading history...</div>
        {:else if savedInteractions.length === 0}
          <div class="text-center py-10 text-slate-500">No interactions saved yet. Start using Chatbot or Magic Explain!</div>
        {:else}
          <div class="flex flex-col gap-4">
            {#each savedInteractions.filter(i => interactionsFilter === 'All' || i.interaction_type === interactionsFilter) as item}
              <div class="bg-slate-800/40 border border-slate-700/50 rounded-lg p-4 hover:bg-slate-800/60 transition-colors group">
                <div class="flex items-center justify-between mb-3 border-b border-slate-700/50 pb-2">
                  <span class="text-xs font-bold px-2 py-0.5 rounded {item.interaction_type === 'Chatbot' ? 'bg-sky-900/50 text-sky-400' : item.interaction_type === 'Grammar' ? 'bg-amber-900/50 text-amber-400' : 'bg-purple-900/50 text-purple-400'}">
                    {item.interaction_type}
                  </span>
                  <span class="text-[10px] text-slate-500 font-mono">
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </div>
                
                <div class="mb-3">
                  <div class="text-[10px] font-bold text-slate-500 uppercase mb-1">Your Input</div>
                  <div class="text-sm text-slate-300 italic border-l-2 border-slate-600 pl-3">"{item.input_text}"</div>
                </div>
                
                <div>
                  <div class="text-[10px] font-bold text-slate-500 uppercase mb-1 flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-teal-500"></span> AI Response
                  </div>
                  <div class="text-sm text-slate-200 markdown-body bg-slate-950/30 p-3 rounded-md">
                    {@html renderMarkdown(item.response_text)}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
  {/if}

  <!-- Top Navbar -->
  {#if showHeader}
  <header class="flex justify-between items-center bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl mb-6 flex-shrink-0 relative z-20 transition-all">
    <div class="flex items-center gap-4">
      <div class="h-10 w-10 bg-teal-500/20 text-teal-400 rounded-lg flex items-center justify-center border border-teal-500/30">
        {#if appMode === 'dashboard'}
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
        {:else}
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
        {/if}
      </div>
      <div>
        <h1 class="text-xl md:text-2xl font-bold tracking-tight text-white">Credit Risk Learning System</h1>
        <p class="text-xs text-slate-400 font-mono tracking-wider">
          {appMode === 'dashboard' ? 'PORTFOLIO TRACKER & LEXICON' : 'DEDICATED PDF VIEWER'}
        </p>
      </div>
    </div>
    <div class="flex items-center gap-6">
      
      <!-- Mode Switcher Buttons -->
      <div class="flex border border-slate-700 rounded-lg p-1 bg-slate-950">
        <button class="px-4 py-1.5 text-xs font-bold rounded-md transition-colors {appMode === 'dashboard' ? 'bg-teal-500 text-slate-950' : 'text-slate-400 hover:text-white'}" on:click={() => appMode = 'dashboard'}>
          Dashboard
        </button>
        <button class="px-4 py-1.5 text-xs font-bold rounded-md transition-colors {appMode === 'reading' ? 'bg-teal-500 text-slate-950' : 'text-slate-400 hover:text-white'}" on:click={() => appMode = 'reading'}>
          Read Book
        </button>
      </div>

      <!-- Mini Timer (Global) -->
      <div class="flex items-center bg-slate-900 border border-slate-700 rounded-lg overflow-hidden h-9">
        <div class="px-3 bg-slate-950 font-mono font-bold {timeRemaining < 60 ? 'text-amber-500' : 'text-teal-400'} border-r border-slate-700 h-full flex items-center justify-center min-w-[70px]">
          {formatTime(timeRemaining)}
        </div>
        {#if !timerActive}
          <button class="px-3 h-full hover:bg-slate-800 text-slate-400 hover:text-teal-400 transition-colors flex items-center justify-center cursor-pointer" on:click={startTimer} title="Start Timer">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2e-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" /></svg>
          </button>
        {:else}
          <button class="px-3 h-full hover:bg-slate-800 text-amber-500 hover:text-amber-400 transition-colors flex items-center justify-center cursor-pointer" on:click={pauseTimer} title="Pause Timer">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
          </button>
        {/if}
        <button class="px-3 h-full border-l border-slate-700 hover:bg-slate-800 text-indigo-400 hover:text-indigo-300 transition-colors flex items-center justify-center cursor-pointer" on:click={logStudySession} title="Log Time">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
        </button>
        <button class="px-3 h-full border-l border-slate-700 hover:bg-slate-800 text-fuchsia-400 hover:text-fuchsia-300 transition-colors flex items-center justify-center cursor-pointer font-bold text-[11px] uppercase tracking-wider" on:click={openInteractionsModal} title="Saved Learnings">
          History
        </button>
      </div>

      <!-- Progress & Analytics -->
      <div class="flex items-center">
        <!-- Focus Analytics -->
        <div class="text-right border-l border-slate-800 pl-6 pr-6">
          <div class="text-xs text-slate-400 mb-1">FOCUS HOURS (600H)</div>
          <div class="flex items-center gap-3 justify-end">
            <span class="font-mono font-bold {sessionStats.total_hours > 100 ? 'text-teal-400' : 'text-sky-400'}">{sessionStats.total_hours} <span class="text-xs text-slate-500">h</span></span>
          </div>
        </div>
        
        <!-- Module Progress -->
        <div class="text-right border-l border-slate-800 pl-6 pr-4">
          <div class="text-xs text-slate-400 mb-1">OVERALL COMPLETION RISK</div>
          <div class="flex items-center gap-3">
            <div class="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-teal-500 rounded-full transition-all duration-500" style="width: {progressPercent}%"></div>
            </div>
            <span class="font-mono font-bold {progressPercent > 50 ? 'text-teal-400' : 'text-amber-400'}">{progressPercent}%</span>
          </div>
        </div>
      </div>

      <!-- Hide Header Button -->
      <button class="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors cursor-pointer" on:click={() => showHeader = false} title="Hide Top Navigation">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
      </button>
    </div>
  </header>
  {:else}
  <!-- Floating Show Header Button -->
  <button class="fixed top-0 left-1/2 -translate-x-1/2 z-50 bg-slate-800 hover:bg-teal-600 text-slate-400 hover:text-slate-950 px-6 py-1 rounded-b-xl shadow-lg border-b border-x border-slate-700 hover:border-teal-500 transition-all cursor-pointer group flex flex-col items-center justify-center gap-0.5" on:click={() => showHeader = true} title="Show Top Navigation">
    <span class="text-[9px] font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity h-0 group-hover:h-auto overflow-hidden">Show Navbar</span>
    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
  </button>
  {/if}

  <!-- ============================================== -->
  <!-- DASHBOARD MODE LAYOUT (3-6-3)                  -->
  <!-- ============================================== -->
  {#if appMode === 'dashboard'}
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 overflow-hidden relative z-10">
    
    <!-- Left Column: Syllabus Tree (Scrollable) -->
    <section class="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full overflow-hidden">
      
      <!-- Weekly Progress Chart -->
      <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 pb-1 border-b border-slate-800">Weekly Progress</h2>
      <div class="flex items-end justify-between h-20 gap-1 mb-5 px-1 shrink-0">
        {#each weeklyStats as stat}
          <div class="flex flex-col items-center flex-1 group">
            <div class="relative w-full flex justify-center h-16 items-end bg-slate-800/30 rounded-t-sm">
              <div class="w-full max-w-[20px] bg-sky-500 rounded-t-sm opacity-80 group-hover:opacity-100 transition-all duration-300 relative group-hover:bg-teal-400" style="height: {Math.max(Math.min((stat.minutes / 120) * 100, 100), stat.minutes > 0 ? 5 : 0)}%;">
                <span class="absolute -top-5 left-1/2 -translate-x-1/2 text-[9px] font-bold text-teal-300 opacity-0 group-hover:opacity-100 transition-opacity">{stat.minutes}m</span>
              </div>
            </div>
            <span class="text-[9px] text-slate-500 mt-1 font-mono uppercase tracking-widest">{stat.day_name}</span>
          </div>
        {/each}
        {#if weeklyStats.length === 0}
          <div class="text-xs text-slate-600 w-full text-center">Loading chart...</div>
        {/if}
      </div>

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

      {#if sessionStats.last_topic}
        <div class="mt-4 pt-3 border-t border-slate-800 shrink-0">
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Last Studied Topic</div>
          <div class="text-xs text-indigo-400 truncate bg-slate-950 p-2 rounded border border-slate-800">{topicNames[sessionStats.last_topic] || sessionStats.last_topic}</div>
        </div>
      {/if}
    </section>

    <!-- Center Column: Main Operations (Timer & Logger) -->
    <section class="lg:col-span-6 flex flex-col gap-6 h-full overflow-y-auto custom-scrollbar pr-2">
      
      <!-- Timer Panel -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden shrink-0">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-teal-500 to-sky-500"></div>
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider">Phase Controller</h2>
          <span class="px-3 py-1 bg-slate-800 rounded-full text-xs font-mono text-teal-400 border border-slate-700">{pillars[currentPillarIndex]}</span>
        </div>
        
        <div class="text-center">
          <div class="text-7xl font-black tracking-tight tabular-nums text-white mb-4 font-mono drop-shadow-[0_0_10px_rgba(20,184,166,0.3)]">
            {formatTime(timeRemaining)}
          </div>
          <div class="flex justify-center gap-2 mb-6">
            <input type="number" bind:value={customMinutes} min="1" max="120" class="w-16 bg-slate-950 text-center rounded border border-slate-700 text-slate-200 outline-none focus:border-teal-500 text-sm py-1">
            <span class="text-slate-400 self-center text-xs">min</span>
            <button on:click={() => { timeRemaining = customMinutes * 60; elapsedSessionSeconds = 0; pauseTimer(); }} class="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-xs font-bold text-slate-300 transition-colors cursor-pointer">Set Time</button>
            {#if sessionStatus} <span class="text-teal-400 self-center text-xs ml-2">{sessionStatus}</span> {/if}
          </div>
          <div class="flex justify-center gap-3">
            {#if !timerActive}
              <button class="px-6 py-2 rounded-lg font-bold bg-teal-500 hover:bg-teal-400 text-slate-950 transition-colors cursor-pointer" on:click={startTimer}>Start Run</button>
            {:else}
              <button class="px-6 py-2 rounded-lg font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-colors cursor-pointer" on:click={pauseTimer}>Pause</button>
            {/if}
            <button class="px-6 py-2 rounded-lg font-bold bg-rose-600 hover:bg-rose-500 text-white transition-colors cursor-pointer disabled:opacity-50" on:click={logStudySession} disabled={elapsedSessionSeconds < 60}>Stop & Save</button>
            <button class="px-6 py-2 rounded-lg font-bold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors cursor-pointer disabled:opacity-50" on:click={resetTimer}>Reset</button>
            <button class="px-6 py-2 rounded-lg font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 transition-colors cursor-pointer disabled:opacity-50" on:click={nextPillar} disabled={currentPillarIndex === pillars.length - 1}>Next Stage</button>
          </div>
        </div>
      </div>

      <!-- Logger Panel -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex-1 flex flex-col">
        <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">Documentation Input</h2>
        
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div class="flex flex-col gap-1.5 relative">
            <span class="text-xs text-slate-500">Mapping Topic:</span>
            <button class="bg-slate-950 border border-slate-800 text-slate-300 text-sm rounded-lg py-2 px-3 text-left focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none flex justify-between items-center" on:click={() => topicDropdownOpen = !topicDropdownOpen}>
              <span class="truncate">{topicNames[selectedTopic] || "Select Topic..."}</span>
              <svg class="w-4 h-4 text-slate-500 transition-transform {topicDropdownOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </button>

            {#if topicDropdownOpen}
              <div class="fixed inset-0 z-40" on:click={() => topicDropdownOpen = false}></div>
              <div class="absolute top-[100%] left-0 w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl z-50 max-h-64 overflow-y-auto custom-scrollbar p-2">
                {#each syllabusData as block}
                  <div class="mb-1">
                    <button class="w-full text-left px-2 py-1.5 text-xs font-bold text-slate-300 hover:bg-slate-800 rounded flex items-center gap-2" on:click={() => toggleDropdownBlock(block.id)}>
                      <span class="text-slate-500 transition-transform {ddBlocks[block.id] ? 'rotate-90 text-teal-400' : ''}">▶</span>
                      {block.name}
                    </button>
                    {#if ddBlocks[block.id]}
                      <div class="ml-3 border-l border-slate-700 pl-2 mt-1">
                        {#each block.children as chapter}
                          <button class="w-full text-left px-2 py-1 text-[11px] text-slate-400 hover:bg-slate-800 rounded flex items-center gap-2" on:click={() => toggleDropdownChapter(chapter.id)}>
                            <span class="text-slate-600 transition-transform {ddChapters[chapter.id] ? 'rotate-90 text-teal-400' : ''}">▶</span>
                            {chapter.name}
                          </button>
                          {#if ddChapters[chapter.id]}
                            <div class="ml-3 border-l border-dashed border-slate-700 pl-2 mt-1 mb-1 flex flex-col items-start">
                              {#each chapter.children as sub}
                                <button class="w-full text-left px-2 py-1 text-[11px] text-slate-500 hover:text-teal-400 hover:bg-slate-800 rounded truncate {selectedTopic === sub.id ? 'bg-slate-800 text-teal-400 font-bold' : ''}" on:click={() => selectTopic(sub.id)}>
                                  • {sub.name}
                                </button>
                              {/each}
                              {#if chapter.children.length === 0}
                                <button class="w-full text-left px-2 py-1 text-[11px] text-slate-500 hover:text-teal-400 hover:bg-slate-800 rounded truncate {selectedTopic === chapter.id ? 'bg-slate-800 text-teal-400 font-bold' : ''}" on:click={() => selectTopic(chapter.id)}>
                                  • Select Chapter
                                </button>
                              {/if}
                            </div>
                          {/if}
                        {/each}
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            {/if}
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
        
        <div class="flex-1 flex flex-col min-h-[200px]">
          <textarea id="content" bind:value={logContent} class="flex-1 w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg p-4 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none resize-none" placeholder="Draft your technical summary here... (Markdown supported)"></textarea>
        </div>

        <!-- AI Grammar Checker Results -->
        {#if grammarError}
          <div class="mt-3 p-3 bg-red-950/40 border border-red-800 rounded-lg text-xs text-red-300">
            <strong>Error:</strong> {grammarError}
          </div>
        {/if}
        {#if grammarResult}
          <div class="mt-3 p-3 bg-indigo-950/40 border border-indigo-800 rounded-lg shadow-inner max-h-[200px] overflow-y-auto custom-scrollbar">
            <div class="mb-2">
              <span class="text-[10px] font-bold text-teal-400 uppercase tracking-wider">Corrected Grammar</span>
              <p class="text-xs text-slate-200 mt-1">{grammarResult.corrected}</p>
            </div>
            <div class="mb-2">
              <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider">Native Alternative</span>
              <p class="text-xs text-slate-200 mt-1 italic">"{grammarResult.native_alternative}"</p>
            </div>
            <div>
              <span class="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Explanation</span>
              <p class="text-[11px] text-slate-400 mt-1">{grammarResult.explanation}</p>
            </div>
          </div>
        {/if}
        
        <div class="mt-4 flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <button class="px-6 py-2 rounded-lg font-bold bg-white text-slate-900 hover:bg-slate-200 transition-colors disabled:opacity-50 cursor-pointer" on:click={submitLog} disabled={!logContent.trim() || isCheckingGrammar}>
              Save to IDE
            </button>
            <button class="px-3 py-2 rounded-lg font-bold bg-indigo-600 hover:bg-indigo-500 text-slate-100 transition-colors cursor-pointer flex items-center gap-1 disabled:opacity-50" on:click={checkGrammar} disabled={!logContent.trim() || isCheckingGrammar}>
              {#if isCheckingGrammar}
                <svg class="animate-spin h-3 w-3 text-slate-100" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Checking...
              {:else}
                🤖 Check Grammar
              {/if}
            </button>
            <button class="px-3 py-2 rounded-lg font-bold transition-colors cursor-pointer flex items-center gap-1 disabled:opacity-50 {isRecording ? 'bg-red-600 hover:bg-red-500 text-white animate-pulse' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'}" on:click={toggleRecording} disabled={isTranscribing || isCheckingGrammar}>
              {#if isTranscribing}
                <svg class="animate-spin h-3 w-3 text-slate-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Transcribing...
              {:else if isRecording}
                🛑 Stop Recording
              {:else}
                🎤 Record Speech
              {/if}
            </button>
          </div>
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
      <div class="bg-slate-950 border border-slate-800 rounded-lg p-3 mb-4 shrink-0">
        <input type="text" bind:value={newTerm} placeholder="Risk Term (e.g. LGD)" class="w-full bg-transparent border-b border-slate-800 text-sm text-slate-200 px-1 py-2 mb-2 focus:border-teal-500 outline-none">
        <textarea bind:value={newDef} rows="2" placeholder="English definition/circumlocution..." class="w-full bg-transparent text-sm text-slate-300 px-1 py-1 focus:outline-none resize-none mb-2"></textarea>
        <div class="flex justify-between items-center">
          <div class="flex gap-2">
            <button class="text-xs bg-slate-800 hover:bg-slate-700 text-white px-3 py-1.5 rounded cursor-pointer transition-colors disabled:opacity-50" on:click={addVocab} disabled={isAskingAI}>+ Add Term</button>
            <button class="text-xs bg-fuchsia-900/50 hover:bg-fuchsia-800 text-fuchsia-300 px-3 py-1.5 rounded cursor-pointer transition-colors disabled:opacity-50 flex items-center gap-1" on:click={askAIVocab} disabled={isAskingAI || !newTerm.trim()}>
              {#if isAskingAI}
                <svg class="animate-spin h-3 w-3 text-fuchsia-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Asking AI...
              {:else}
                🤖 Ask AI
              {/if}
            </button>
          </div>
          {#if vocabStatus} <span class="text-teal-400 text-xs truncate max-w-[80px]">{vocabStatus}</span> {/if}
        </div>
      </div>

      <div class="flex justify-between items-center mb-2 px-1">
        <span class="text-xs text-slate-500 font-bold uppercase">Saved Lexicon</span>
        <button class="text-[10px] bg-slate-800 hover:bg-teal-700 text-teal-400 hover:text-white px-2 py-1 rounded cursor-pointer transition-colors flex items-center gap-1 disabled:opacity-50" on:click={exportVocabPDF} disabled={isExportingPDF || vocabularies.length === 0}>
          {#if isExportingPDF}
            <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          {:else}
            🖨️
          {/if}
          Export PDF
        </button>
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

  <!-- ============================================== -->
  <!-- RESIZABLE PDF READING MODE                     -->
  <!-- ============================================== -->
  {:else}
  
  <div class="flex flex-1 overflow-hidden relative z-10 w-full h-full">
    <!-- Reading Mode Layout -->
    {#if appMode === 'reading'}
    <div class="flex-1 min-h-0 flex gap-4 pb-4 w-full" style="{isResizing || isResizingCompanion ? 'pointer-events: none;' : ''}">
      
      <!-- PDF Viewer Area -->
      <section class="flex flex-col h-full overflow-hidden flex-1 relative">
        
        <!-- Floating Action Bar (Draggable) -->
        <div class="fixed bottom-[5.5rem] right-6 z-[100] cursor-grab active:cursor-grabbing" use:draggable>
          <button 
            class="bg-gradient-to-r from-amber-500 to-orange-500 text-white p-4 rounded-full shadow-[0_0_20px_rgba(245,158,11,0.4)] hover:shadow-[0_0_25px_rgba(245,158,11,0.6)] hover:scale-105 transition-all cursor-pointer border-2 border-slate-900 group flex items-center gap-2"
            on:click={() => showCompanion = !showCompanion}
          >
            <span class="text-white/60 mr-1 text-xs">⠿</span>
            <span class="text-xl leading-none">📖</span>
            <span class="max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-300 ease-in-out whitespace-nowrap font-bold text-sm">
              {showCompanion ? 'Close Companion' : 'Reading Companion'}
            </span>
          </button>
        </div>
        <!-- PDF Iframe -->
        <div class="flex-1 rounded-xl overflow-hidden shadow-xl bg-slate-900 border border-slate-800 relative z-0">
          {#key pdfPage}
            <iframe src={`http://localhost:6234/api/pdf?t={Date.now()}#page=${pdfPage}&pagemode=bookmarks`} type="application/pdf" class="w-full h-full" title="Credit Intelligence PDF"></iframe>
          {/key}
        </div>
      </section>

    <!-- Reading Companion Sidebar -->
    {#if showCompanion}
      <!-- Resizer Handle for Companion -->
      <div class="w-4 shrink-0 flex items-center justify-center cursor-col-resize group z-10 mx-1" on:mousedown={startResizeCompanion} title="Drag to resize">
        <div class="w-1 h-12 bg-slate-700 rounded-full group-hover:bg-amber-500 transition-colors duration-300"></div>
      </div>

      <section class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col h-full overflow-hidden shrink-0 transition-all" style="width: {companionWidth}px;">
        <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">Reading Companion</h2>
        
        <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-6">
          
          <!-- Vocab Catcher -->
          <div class="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
            <h3 class="text-xs font-bold text-teal-400 mb-2">⚡ Quick Vocab Catcher</h3>
            <p class="text-[10px] text-slate-400 mb-3 leading-relaxed">Found a new technical word? Save it directly to your Lexicon Bank.</p>
            <input type="text" bind:value={newTerm} placeholder="Risk Term (e.g. PD, LGD)" class="w-full bg-slate-950 border border-slate-800 text-xs text-slate-200 px-2 py-2 rounded mb-2 focus:border-teal-500 outline-none">
            <textarea bind:value={newDef} rows="2" placeholder="Translation or Definition..." class="w-full bg-slate-950 border border-slate-800 text-xs text-slate-300 px-2 py-2 rounded focus:outline-none resize-none mb-2 custom-scrollbar"></textarea>
            <div class="flex justify-between items-center gap-2">
              <div class="flex gap-2">
                <button class="text-xs bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold px-3 py-1.5 rounded cursor-pointer transition-colors disabled:opacity-50" on:click={addVocab} disabled={isAskingAI}>Save to Lexicon</button>
                <button class="text-xs bg-fuchsia-900/50 hover:bg-fuchsia-800 text-fuchsia-300 px-3 py-1.5 rounded cursor-pointer transition-colors disabled:opacity-50 flex items-center gap-1" on:click={askAIVocab} disabled={isAskingAI || !newTerm.trim()}>
                  {#if isAskingAI}
                    <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  {:else}
                    🤖 Ask AI
                  {/if}
                </button>
              </div>
              {#if vocabStatus} <span class="text-teal-400 text-[10px] truncate max-w-[80px]">{vocabStatus}</span> {/if}
            </div>

            <!-- Saved Vocabularies -->
            {#if vocabularies.length > 0}
              <div class="mt-3 flex flex-col gap-2 max-h-[200px] overflow-y-auto custom-scrollbar pr-1 border-t border-slate-700 pt-3">
                {#each vocabularies as v}
                  <div class="bg-slate-900 border border-slate-800 p-2 rounded flex justify-between items-start group">
                    <div class="flex flex-col gap-1 flex-1">
                      <span class="text-[11px] font-bold text-teal-400">{v.term}</span>
                      <span class="text-[10px] text-slate-300 leading-relaxed">{v.definition}</span>
                    </div>
                    <button class="text-slate-500 hover:text-teal-400 transition-colors p-1" on:click={() => playAudio(v.term)} title="Play Pronunciation">
                      🔊
                    </button>
                  </div>
                {/each}
              </div>
            {/if}
          </div>

          <!-- Doubt Catcher -->
          <div class="bg-slate-800/50 rounded-lg p-3 border border-slate-700 flex flex-col flex-1">
            <h3 class="text-xs font-bold text-amber-400 mb-2">❓ Confusing Concept / Grammar</h3>
            <p class="text-[10px] text-slate-400 mb-3 leading-relaxed">Paste complex English grammar or confusing risk concepts here to be reviewed by AI IDE later.</p>
            
            <textarea bind:value={doubtContent} on:paste={handlePaste} class="flex-1 w-full min-h-[150px] bg-slate-950 border border-slate-800 text-xs text-slate-300 px-2 py-2 rounded focus:border-amber-500 outline-none resize-none mb-3 custom-scrollbar" placeholder="Paste confusing sentence from the book here... (Or Ctrl+V to paste an image screenshot!)"></textarea>
            
            {#if doubtImageBase64}
              <div class="relative inline-block mb-3 bg-slate-900 border border-slate-700 p-1 rounded max-w-fit">
                <img src={doubtImageBase64} alt="Pasted snapshot" class="max-h-[100px] object-contain rounded" />
                <button class="absolute -top-2 -right-2 bg-rose-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px] font-bold hover:bg-rose-400 border-2 border-slate-800" on:click={() => doubtImageBase64 = null}>×</button>
              </div>
            {/if}
            <div class="flex flex-col gap-2">
              <div class="flex gap-2">
                <button class="text-[10px] flex-1 font-bold bg-sky-600 hover:bg-sky-500 text-slate-950 px-2 py-2 rounded cursor-pointer transition-colors uppercase tracking-wider flex items-center justify-center gap-1" on:click={() => translateDoubt('quick')} disabled={!doubtContent || !doubtContent.trim() || isTranslating}>
                  {#if isTranslating && translateMode === 'quick'}
                    <svg class="animate-spin h-3 w-3 text-slate-950" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Translating...
                  {:else}
                    ⚡ Quick ID
                  {/if}
                </button>

                <button class="text-[10px] flex-1 font-bold bg-indigo-600 hover:bg-indigo-500 text-slate-100 px-2 py-2 rounded cursor-pointer transition-colors uppercase tracking-wider flex items-center justify-center gap-1" on:click={() => translateDoubt('comprehensive')} disabled={!doubtContent || !doubtContent.trim() || isTranslating}>
                  {#if isTranslating && translateMode === 'comprehensive'}
                    <svg class="animate-spin h-3 w-3 text-slate-100" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Deep Scan...
                  {:else}
                    🔍 Comprehensive
                  {/if}
                </button>
              </div>

              <button class="text-[10px] font-bold bg-fuchsia-600 hover:bg-fuchsia-500 text-white px-3 py-2 rounded cursor-pointer transition-colors w-full uppercase tracking-wider flex items-center justify-center gap-1 shadow-[0_0_10px_rgba(192,38,211,0.5)] disabled:opacity-50 disabled:cursor-not-allowed" on:click={explainDoubt} disabled={(!doubtContent || !doubtContent.trim()) && !doubtImageBase64 || isExplaining}>
                {#if isExplaining}
                  <svg class="animate-spin h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Thinking...
                {:else}
                  🪄 Magic Explain (ELI5)
                {/if}
              </button>
              
              <button class="text-[10px] font-bold bg-amber-600 hover:bg-amber-500 text-slate-950 px-3 py-2 rounded cursor-pointer transition-colors w-full uppercase tracking-wider" on:click={submitDoubt} disabled={!doubtContent || !doubtContent.trim()}>Save for AI Review</button>
              
              {#if doubtStatus} <span class="text-amber-400 text-[10px] text-center mt-1">{doubtStatus}</span> {/if}
            </div>

            <!-- Beautiful Explain Result UI -->
            {#if explainResult}
              <div class="mt-4 p-4 bg-fuchsia-950/20 border border-fuchsia-800 rounded-lg shadow-[0_0_15px_rgba(192,38,211,0.1)] flex flex-col gap-3">
                <div>
                  <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1 mb-1">🎯 Core Concept (ID)</span>
                  <div class="text-[11px] text-slate-200 leading-relaxed markdown-body">{@html renderMarkdown(explainResult.core_concept)}</div>
                </div>
                <div>
                  <span class="text-[10px] font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1 mb-1">💡 Practical Example (ID)</span>
                  <div class="text-[11px] text-slate-300 leading-relaxed bg-amber-950/30 p-2 rounded border-l-2 border-amber-500 markdown-body">{@html renderMarkdown(explainResult.practical_example)}</div>
                </div>
                <div>
                  <span class="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1 mb-1">🧠 Smart Analogy</span>
                  <div class="text-[11px] text-slate-300 leading-relaxed bg-emerald-950/30 p-2 rounded border-l-2 border-emerald-500 markdown-body">{@html renderMarkdown(explainResult.analogy)}</div>
                </div>
                <div>
                  <span class="text-[10px] font-bold text-fuchsia-400 uppercase tracking-wider flex items-center gap-1 mb-1">💬 English Explanation</span>
                  <div class="text-[11px] text-slate-300 leading-relaxed italic bg-fuchsia-900/30 p-2 rounded border-l-2 border-fuchsia-500 markdown-body">{@html renderMarkdown(explainResult.english_explanation)}</div>
                </div>
                <div>
                  <span class="text-[10px] font-bold text-teal-400 uppercase tracking-wider flex items-center gap-1 mb-1">🔍 Phrasing Breakdown</span>
                  <div class="text-[11px] text-slate-300 leading-relaxed bg-teal-900/30 p-2 rounded border-l-2 border-teal-500 markdown-body">{@html renderMarkdown(explainResult.phrasing_breakdown)}</div>
                </div>
              </div>
            {/if}

            <!-- Beautiful Translation Result UI -->
            {#if translateResult}
              <div class="mt-4 p-3 bg-slate-900 border border-slate-700 rounded-lg shadow-inner max-h-[300px] overflow-y-auto custom-scrollbar">
                <div class="mb-3">
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider">Terjemahan Indonesia:</span>
                    <button class="text-[10px] text-slate-400 hover:text-teal-400 transition-colors flex items-center gap-1 cursor-pointer" on:click={() => playAudio(doubtContent)} title="Listen Original English">🔊 Original</button>
                  </div>
                  <p class="text-xs text-slate-200 mt-1 leading-relaxed bg-slate-800/50 p-2 rounded">{translateResult.translation}</p>
                </div>

                {#if translateResult.dictionary && translateResult.dictionary.length > 0}
                  <div class="mb-3">
                    <span class="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">📖 General Dictionary</span>
                    {#each translateResult.dictionary as dict}
                      <div class="mt-2 bg-slate-800 p-2 rounded border-l-2 border-emerald-500">
                        <div class="flex items-center gap-2 mb-1">
                          <p class="text-sm font-bold text-slate-200">{dict.word} <span class="text-xs font-normal text-slate-400">{dict.phonetic}</span></p>
                          <button class="text-slate-400 hover:text-teal-400 transition-colors p-0.5 cursor-pointer" on:click={() => playAudio(dict.word)} title="Listen">🔊</button>
                        </div>
                        <ul class="mt-1 list-disc list-inside text-xs text-slate-300">
                          {#each dict.meanings as meaning}
                            <li class="mb-1"><span class="italic text-emerald-400">({meaning.pos})</span> {meaning.def}
                              {#if meaning.ex}
                                <br><span class="text-slate-500 ml-4">"{meaning.ex}"</span>
                              {/if}
                            </li>
                          {/each}
                        </ul>
                      </div>
                    {/each}
                  </div>
                {/if}

                {#if translateResult.glossary && translateResult.glossary.length > 0}
                  <div>
                    <span class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1">🧠 Credit Risk Context</span>
                    {#each translateResult.glossary as gloss}
                      <div class="mt-2 bg-indigo-950/30 p-2 rounded border-l-2 border-indigo-500">
                        <div class="flex items-center gap-2 mb-1">
                          <p class="text-sm font-bold text-indigo-300">{gloss.term}</p>
                          <button class="text-indigo-400 hover:text-teal-400 transition-colors p-0.5 cursor-pointer" on:click={() => playAudio(gloss.term)} title="Listen">🔊</button>
                        </div>
                        <div class="text-[10px] mt-1 space-y-1">
                          <p><span class="text-slate-400 font-semibold w-16 inline-block">General:</span> <span class="text-slate-300">{gloss.general}</span></p>
                          <p><span class="text-slate-400 font-semibold w-16 inline-block">Credit:</span> <span class="text-amber-300 font-medium">{gloss.credit}</span></p>
                          <p><span class="text-slate-400 font-semibold w-16 inline-block leading-tight">Context:</span> <span class="text-slate-300 italic">{gloss.context}</span></p>
                        </div>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {/if}
          </div>

        </div>
      </section>
    {/if}

  </div>
  {/if}
</div>
{/if}

  <!-- ============================================== -->
  <!-- FLOATING CHATBOT WIDGET                        -->
  <!-- ============================================== -->

  <div class="fixed bottom-6 right-6 z-[100] cursor-grab active:cursor-grabbing" use:draggable>
    <button 
      class="bg-gradient-to-r from-teal-500 to-sky-500 text-white p-4 rounded-full shadow-[0_0_20px_rgba(20,184,166,0.4)] hover:shadow-[0_0_25px_rgba(20,184,166,0.6)] hover:scale-105 transition-all cursor-pointer border-2 border-slate-900 group flex items-center gap-2"
      on:click={() => { isChatOpen = !isChatOpen; if(isChatOpen) scrollToBottom(); }}
    >
      <span class="text-white/60 mr-1">⠿</span>
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
      {#if !isChatOpen}
        <span class="max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-300 ease-in-out whitespace-nowrap font-bold text-sm">Ask AI Assistant</span>
      {/if}
    </button>
  </div>

  {#if isChatOpen}
    <div class="fixed {isChatMaximized ? 'inset-4 md:inset-10 z-[200] w-auto h-auto' : 'bottom-24 right-6 z-[100] w-80 md:w-96'} bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300" style="{isChatMaximized ? '' : 'height: 500px; max-height: calc(100vh - 120px);'}">
      <!-- Header -->
      <div class="bg-gradient-to-r from-slate-800 to-slate-900 p-4 border-b border-slate-700 flex justify-between items-center shrink-0">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></div>
          <span class="font-bold text-slate-200 text-sm">English AI Assistant</span>
        </div>
        <div class="flex items-center gap-3">
          <button class="text-slate-400 hover:text-white transition-colors cursor-pointer" on:click={() => isChatMaximized = !isChatMaximized} title={isChatMaximized ? "Minimize" : "Maximize"}>
            {#if isChatMaximized}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 14h6v6m10-10h-6V4m0 10l6 6M4 4l6 6" /></svg>
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
            {/if}
          </button>
          <button class="text-slate-400 hover:text-white transition-colors cursor-pointer" on:click={() => isChatOpen = false}>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
          </button>
        </div>
      </div>
      
      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4 custom-scrollbar bg-slate-950" bind:this={chatContainer}>
        {#if chatMessages.length === 0}
          <div class="text-center mt-10">
            <div class="text-4xl mb-3">👋</div>
            <h3 class="text-slate-300 font-bold mb-1">Hi there!</h3>
            <p class="text-xs text-slate-500">I can help you understand grammar, explain difficult concepts, or translate phrases. What's on your mind?</p>
          </div>
        {/if}
        {#each chatMessages as msg}
          <div class="flex flex-col {msg.role === 'user' ? 'items-end' : 'items-start'}">
            <span class="text-[9px] text-slate-500 font-bold uppercase mb-1 px-1">{msg.role === 'user' ? 'You' : 'AI Assistant'}</span>
            <div class="p-3 rounded-2xl max-w-[85%] text-[13px] leading-relaxed shadow-sm {msg.role === 'user' ? 'whitespace-pre-wrap bg-teal-600 text-white rounded-tr-sm' : 'markdown-body bg-slate-800 text-slate-200 border border-slate-700 rounded-tl-sm'}">
              {#if msg.role === 'assistant'}
                {@html renderMarkdown(msg.content)}
              {:else}
                {msg.content}
              {/if}
            </div>
          </div>
        {/each}
        {#if isChatLoading && (!chatMessages.length || chatMessages[chatMessages.length - 1].role !== 'assistant')}
          <div class="flex flex-col items-start">
            <div class="p-4 rounded-2xl bg-slate-800 border border-slate-700 rounded-tl-sm flex gap-1 items-center">
              <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
              <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
          </div>
        {/if}
      </div>
      
      <!-- Input -->
      <div class="p-3 bg-slate-900 border-t border-slate-700 shrink-0">
        <form class="flex gap-2" on:submit|preventDefault={sendChatMessage}>
          <input 
            type="text" 
            bind:value={chatInput} 
            placeholder="Ask something..." 
            class="flex-1 bg-slate-800 text-slate-200 text-sm rounded-xl px-4 py-2 border border-slate-700 focus:border-teal-500 focus:outline-none placeholder-slate-500 disabled:opacity-50"
            disabled={isChatLoading}
          >
          <button 
            type="submit" 
            class="bg-teal-500 hover:bg-teal-400 text-slate-950 p-2.5 rounded-xl cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shrink-0"
            disabled={!chatInput.trim() || isChatLoading}
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          </button>
        </form>
      </div>
    </div>
  {/if}
</main>
