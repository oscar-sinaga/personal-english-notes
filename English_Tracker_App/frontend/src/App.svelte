<script>
  import { onMount, tick } from 'svelte';
  import syllabusData from './syllabus.json';
  import { marked } from 'marked';
  import DOMPurify from 'dompurify';
  import markedKatex from 'marked-katex-extension';
  import 'katex/dist/katex.min.css';
  import DailyPractice from './lib/DailyPractice.svelte';
  import BookReader from './lib/BookReader.svelte';
  import Lexicon from './lib/Lexicon.svelte';
  import PracticeJournal from './lib/PracticeJournal.svelte';
  import StudyTutor from './lib/StudyTutor.svelte';
  import { apiUrl as API_URL, contexts, requestJson, saveEntry, skills, statuses } from './practice.js';

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

  let pendingProgress = new Set();
  let progressStatus = '';
  const topicGroups = syllabusData.map(block => ({
    label: block.name,
    topics: [block, ...block.children.flatMap(chapter => [chapter, ...chapter.children])],
  }));
  const topicNames = Object.fromEntries(topicGroups.flatMap(group => group.topics.map(topic => [topic.id, topic.name])));
  const courseTopics = syllabusData.flatMap(group => group.children.flatMap(chapter =>
    chapter.children.length ? chapter.children : [chapter]));

  let timerActive = false;
  let timerMinutes = 20;
  let customMinutes = timerMinutes;
  let timeRemaining = timerMinutes * 60;
  let timerDeadline = 0;
  let timerDialog;
  let timerSettingsOpen = false;
  let currentPillarIndex = 0;
  const pillars = ["Active Writing", "Thinking & Circumlocution", "Role-Play"];
  let interval;
  let activeTimerPillar = "";
  let activeTimerTopic = "";
  let elapsedSessionSeconds = 0;
  let savingSession = false;
  let lastSession = null;

  let selectedTopic = syllabusData.length > 0 ? syllabusData[0].id : "";
  let logContent = "";
  const emptyPractice = () => ({ id: null, version: 0, skill: 'Writing', context: 'Study',
    status: 'draft', source: '', prompt: '', feedback: '', revision: '', session_id: null });
  let practice = emptyPractice();
  let savedSnapshot = "";
  let savingPractice = false;
  let showPracticeJournal = false;
  let aiEnabled = false;
  let transcriptionEnabled = false;
  let subscriptionAI = false;
  let showAISettings = false;
  let aiSettingsBusy = false;
  let aiSettingsStatus = '';
  let aiProvider = 'codex';
  let aiModel = '';
  let aiModels = [];
  let activeAI = null;
  let onlineHelpers = false;
  let books = null;
  let exportStatus = "";
  let practiceEditor;
  let practiceHeading;
  let manualEntry;
  let workspaceContent;
  let voiceTutor;
  let readingTutor;
  let guidedKey = 0;
  const guidedModes = { Speaking: 'speaking', Listening: 'listening', 'Credit Risk': 'case' };

  // Lexicon state
  let vocabularies = [];
  let newTerm = "";
  let newDef = "";
  let vocabStatus = "";
  let isAskingAI = false;
  let savingVocab = false;
  let isExportingPDF = false;

  // Session Stats
  let sessionStats = { total_hours: 0, total_minutes: 0, last_topic: null };
  let sessionStatus = "";
  let weeklyStats = [];
  $: peakMinutes = Math.max(1, ...weeklyStats.map(day => day.minutes));

  // App Layout State
  let appMode = "dashboard"; // 'dashboard' or 'reading'
  
  const bookTitles = { anderson: 'Anderson', siddiqi: 'Siddiqi' };
  let currentBook = 'anderson';
  let bookPages = { anderson: 1, siddiqi: 1 };
  let readerExpanded = false;
  let nativePdfAvailable = false;
  let useBrowserPdf = false;
  let studyReader;
  let notesButton;
  let showReadingHeader = false;
  let browserFullscreenAvailable = false;
  let browserPdf;
  let browserPdfStatus = '';
  $: compactReading = appMode === 'reading' && nativePdfAvailable;
  $: desktopReading = compactReading && useBrowserPdf;
  $: headerVisible = !compactReading || showReadingHeader;
  $: selectedBook = books?.[currentBook] ? currentBook : Object.keys(bookTitles).find(book => books?.[book]);

  $: pdfUrl = selectedBook ? `${API_URL}/pdf?book=${selectedBook}` : '';

  // Reading Mode Layout State
  let companionWidth = 384;
  let readingLayout;
  let isResizingCompanion = false;
  let historyDialog;
  let historyError = '';

  let savedInteractions = [];
  let interactionsFilter = "All"; // 'All', 'Chatbot', 'Grammar', 'Explain'
  let isFetchingInteractions = false;
  let showCompanion = false;
  let companionOpened = false;
  let doubtContent = "";
  let doubtImageBase64 = null;
  let doubtStatus = "";

  // Chatbot State
  let assistantDialog;
  let isChatMaximized = false;
  let chatMessages = [];
  let chatInput = "";
  let isChatLoading = false;
  let chatContainer;


  onMount(() => {
    nativePdfAvailable = navigator.pdfViewerEnabled &&
      window.matchMedia('(any-hover: hover) and (any-pointer: fine)').matches;
    useBrowserPdf = nativePdfAvailable;
    try {
      if (localStorage.getItem('english-notes.pdf-reader') === 'study') useBrowserPdf = false;
    } catch { /* Keep the current reader when storage is unavailable. */ }
    browserFullscreenAvailable = document.fullscreenEnabled && !!Element.prototype.requestFullscreen;
    if (syllabusData.length > 0) {
      expandedBlocks[syllabusData[0].id] = true;
    }
    fetchProgress();
    fetchVocab();
    fetchSessionStats();
    fetchWeeklyStats();
    requestJson('/config').then(config => {
      aiEnabled = config.ai_enabled;
      transcriptionEnabled = config.transcription_enabled ?? config.ai_enabled;
      subscriptionAI = config.subscription_ai ?? false;
      onlineHelpers = config.online_helpers;
      books = config.books;
    }).catch(() => { books = { anderson: false, siddiqi: false }; });
    const warnUnsaved = event => {
      if (hasUnsavedPractice()) {
        event.preventDefault();
        event.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', warnUnsaved);
    return () => {
      window.removeEventListener('beforeunload', warnUnsaved);
      stopResizeCompanion();
      pauseTimer();
    };
  });

  async function showBrowserPdfFullscreen() {
    browserPdfStatus = '';
    try {
      await browserPdf.requestFullscreen();
    } catch {
      browserPdfStatus = 'Open the PDF in its own tab to use your browser’s full screen.';
    }
  }

  function switchPdfReader() {
    useBrowserPdf = !useBrowserPdf;
    browserPdfStatus = '';
    try {
      localStorage.setItem('english-notes.pdf-reader', useBrowserPdf ? 'browser' : 'study');
    } catch { /* The new reader is still available for this tab. */ }
  }

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
      vocabularies = await requestJson('/vocabulary');
    } catch (error) { vocabStatus = error.message; }
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
    if (savingVocab || !newTerm.trim() || !newDef.trim()) return;
    savingVocab = true;
    vocabStatus = '';
    try {
      await requestJson('/vocabulary', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ term: newTerm, definition: newDef })
      });
      newTerm = '';
      newDef = '';
      vocabStatus = 'Term saved.';
      await fetchVocab();
    } catch (error) {
      vocabStatus = error.message;
    } finally {
      savingVocab = false;
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
    if (pendingProgress.has(id)) return;
    const newState = !(progressMap[id] || false);
    pendingProgress = new Set(pendingProgress).add(id);
    progressMap = { ...progressMap, [id]: newState };
    progressStatus = '';
    try {
      await requestJson('/progress', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ module_name: id, is_completed: newState })
      });
    } catch (error) {
      progressMap = { ...progressMap, [id]: !newState };
      progressStatus = error.message;
    } finally {
      pendingProgress.delete(id);
      pendingProgress = new Set(pendingProgress);
    }
  }

  function toggleBlock(id) { expandedBlocks[id] = !expandedBlocks[id]; }
  function toggleChapter(id) { expandedChapters[id] = !expandedChapters[id]; }

  function selectTopic(id) {
    if (id !== selectedTopic) practice.session_id = null;
    selectedTopic = id;
  }

  // --- Resize Handlers (Companion) ---
  function startResizeCompanion(event) {
    if (event.button !== 0) return;
    event.preventDefault();
    isResizingCompanion = true;
    document.addEventListener('mousemove', handleResizeCompanion);
    document.addEventListener('mouseup', stopResizeCompanion);
  }
  function handleResizeCompanion(e) {
    if (isResizingCompanion && readingLayout) {
      setCompanionWidth(readingLayout.getBoundingClientRect().right - e.clientX);
    }
  }
  function setCompanionWidth(value) {
    companionWidth = Math.round(Math.min(800, window.innerWidth * .52, Math.max(280, value)));
  }
  function resizeCompanionWithKeys(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      setReadingNotes(false);
      return;
    }
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    setCompanionWidth(companionWidth + (event.key === 'ArrowLeft' ? 24 : -24));
  }
  function stopResizeCompanion() {
    isResizingCompanion = false;
    document.removeEventListener('mousemove', handleResizeCompanion);
    document.removeEventListener('mouseup', stopResizeCompanion);
  }

  function setTimer() {
    if (!Number.isInteger(customMinutes) || customMinutes < 1 || customMinutes > 120) {
      sessionStatus = "Enter a whole number from 1 to 120.";
      return;
    }
    pauseTimer();
    timerMinutes = customMinutes;
    sessionStatus = 'Duration set to ' + timerMinutes + ' min.';
    timeRemaining = timerMinutes * 60;
    elapsedSessionSeconds = 0;
  }

  function startTimer() {
    if (timerActive || savingSession || !timeRemaining) return;
    sessionStatus = '';
    timerActive = true;
    if (!elapsedSessionSeconds) {
      activeTimerPillar = appMode === 'reading' ? "Reading Comprehension" : pillars[currentPillarIndex];
      activeTimerTopic = selectedTopic || "General";
    }
    timerDeadline = performance.now() + timeRemaining * 1000;
    interval = setInterval(() => {
      updateClock();
      if (!timeRemaining) {
        pauseTimer();
        logStudySession();
      }
    }, 250);
  }
  function updateClock() {
    const remaining = Math.max(0, Math.min(timeRemaining, Math.ceil((timerDeadline - performance.now()) / 1000)));
    elapsedSessionSeconds += timeRemaining - remaining;
    timeRemaining = remaining;
  }
  function pauseTimer() {
    if (timerActive) updateClock();
    timerActive = false;
    clearInterval(interval);
  }
  async function nextPillar() {
    if (savingSession || currentPillarIndex >= pillars.length - 1) return;
    if (timerActive) updateClock();
    if (elapsedSessionSeconds >= 60 && !(await logStudySession())) return;
    pauseTimer();
    currentPillarIndex++;
    elapsedSessionSeconds = 0;
    timeRemaining = timerMinutes * 60;
    sessionStatus = 'Next stage: ' + pillars[currentPillarIndex] + '.';
  }
  function resetTimer() {
    pauseTimer();
    currentPillarIndex = 0;
    elapsedSessionSeconds = 0;
    timeRemaining = timerMinutes * 60;
    sessionStatus = 'Timer reset.';
  }
  function formatTime(secs) {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  function showTimerSettings() {
    timerSettingsOpen = true;
    timerDialog.showModal();
  }

  async function logStudySession() {
    if (savingSession) return false;
    if (timerActive) updateClock();
    const elapsedMins = Math.round(elapsedSessionSeconds / 60);
    
    if (elapsedMins <= 0) {
      sessionStatus = 'Log at least one minute of study time.';
      return false;
    }
    
    pauseTimer();
    savingSession = true;
    sessionStatus = "Saving session...";
    try {
      lastSession = await requestJson('/sessions', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          topic_id: activeTimerTopic || selectedTopic || "General",
          pillar: activeTimerPillar || (appMode === 'reading' ? "Reading Comprehension" : pillars[currentPillarIndex]), 
          duration_minutes: elapsedMins 
        })
      });
      sessionStatus = `Saved ${elapsedMins} min of study time.`;
      fetchSessionStats();
      fetchWeeklyStats();
      elapsedSessionSeconds = 0;
      timeRemaining = timerMinutes * 60;
      return true;
    } catch (error) {
      sessionStatus = error.message;
    } finally {
      savingSession = false;
    }
    return false;
  }

  function practicePayload() {
    const { id, ...data } = practice;
    return {
      ...data, topic_id: selectedTopic || 'General', content: logContent.trim(),
      session_id: practice.session_id ?? (!practice.version && lastSession?.topic_id === selectedTopic ? lastSession.id : null)
    };
  }

  function snapshot(data) {
    const { version, ...values } = data;
    return JSON.stringify(values);
  }

  function hasUnsavedPractice() {
    const data = practicePayload();
    return Boolean(data.content || data.prompt || data.feedback || data.revision || data.source)
      && snapshot(data) !== savedSnapshot;
  }

  async function changeAppMode(mode) {
    if (appMode === mode) return;
    const tutor = appMode === 'reading' ? readingTutor : voiceTutor;
    if (tutor?.canLeave() === false) return;
    appMode = mode;
    await tick();
    workspaceContent?.focus();
  }

  async function setReadingNotes(open) {
    if (!open && readingTutor?.canReturnToPdf() === false) return;
    if (open) companionOpened = true;
    showCompanion = open;
    await tick();
    if (open) readingTutor?.focusLesson();
    else notesButton?.focus();
  }

  async function askAboutPdf(quote) {
    const source = { ...quote, book: selectedBook };
    const existingTutor = readingTutor;
    if (existingTutor?.useExcerpt(source) === false) return false;
    await studyReader?.leaveFullscreenForTutor();
    companionOpened = true;
    showCompanion = true;
    await tick();
    if (!readingTutor) return false;
    if (!existingTutor) readingTutor.useExcerpt(source);
    await tick();
    readingTutor.focusLesson(true);
    return true;
  }

  function changeSkill(skill) {
    if (skill === practice.skill) return true;
    if (voiceTutor?.canLeave() === false) return false;
    practice = { ...practice, skill };
    guidedKey += 1;
    return true;
  }

  async function chooseSkill(skill) {
    if (!changeSkill(skill) || !guidedModes[skill]) return;
    await tick();
    voiceTutor?.focusLesson();
  }

  function openPractice(entry) {
    if (savingPractice || (hasUnsavedPractice() && !window.confirm('Discard the unsaved changes in this editor?'))) return false;
    const tutor = appMode === 'reading' ? readingTutor : voiceTutor;
    if (tutor?.canLeave() === false) return false;
    guidedKey += 1;
    practice = entry
      ? Object.fromEntries(Object.keys(emptyPractice()).map(key => [key, entry[key]]))
      : emptyPractice();
    logContent = entry?.content ?? '';
    if (entry) selectedTopic = entry.topic_id;
    savedSnapshot = entry ? snapshot(practicePayload()) : '';
    grammarResult = null;
    grammarError = '';
    exportStatus = '';
    appMode = 'dashboard';
    if (entry) focusPracticeEditor();
    return true;
  }

  async function focusPracticeEditor() {
    await tick();
    if (manualEntry) manualEntry.open = true;
    (practiceEditor || practiceHeading)?.focus();
  }

  async function startDailyPractice(exercise, prompt) {
    if (!openPractice(null)) return;
    selectTopic(exercise.topic);
    practice = { ...practice, skill: exercise.skill, source: 'Latihan Hari Ini', prompt };
    await focusPracticeEditor();
  }

  async function submitLog() {
    if (savingPractice || !logContent.trim()) return;
    savingPractice = true;
    exportStatus = "Saving...";
    practice.id ??= crypto.randomUUID();
    const data = practicePayload();
    try {
      const entry = await saveEntry(practice.id, data);
      practice = { ...practice, version: entry.version, session_id: entry.session_id };
      savedSnapshot = snapshot(data);
      exportStatus = entry.status === 'completed' ? 'Completed practice saved.' : 'Draft saved.';
    } catch (issue) {
      exportStatus = issue.message;
    } finally {
      savingPractice = false;
    }
  }

  let pendingDoubtId = null;
  let savingDoubt = false;

  async function submitDoubt() {
    if (savingDoubt || !doubtContent.trim()) return;
    savingDoubt = true;
    pendingDoubtId ??= crypto.randomUUID();
    const content = doubtContent.trim();
    doubtStatus = "Saving question...";
    try {
      await saveEntry(pendingDoubtId, {
        topic_id: selectedTopic || 'General', context: 'Study', skill: 'Reading',
        prompt: 'Question from Reading Companion', content
      });
      pendingDoubtId = null;
      if (doubtContent.trim() === content) doubtContent = "";
      doubtStatus = "Question saved to the practice journal.";
    } catch (issue) {
      doubtStatus = issue.message;
    } finally {
      savingDoubt = false;
    }
  }

  function playAudio(text) {
    if (!('speechSynthesis' in window)) {
      window.alert('Speech playback is unavailable in this browser.');
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en';
    window.speechSynthesis.speak(utterance);
  }

  // Flat map for topic names
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
      if (!res.ok) throw new Error();
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
      if (!subscriptionAI && item.type.startsWith('image/')) {
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
      
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || 'Could not explain this text.');
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
      doubtStatus = e.message || "Could not explain this text.";
      setTimeout(() => { doubtStatus = "" }, 3000);
    } finally {
      isExplaining = false;
    }
  }

  async function loadAISettings(provider) {
    aiSettingsBusy = true;
    aiSettingsStatus = '';
    try {
      const info = await requestJson('/ai/preferences' + (provider ? '?provider=' + provider : ''));
      activeAI = info.active;
      aiProvider = provider || activeAI.provider;
      aiModels = info.models;
      aiModel = aiProvider === activeAI.provider ? activeAI.model : aiModels[0];
    } catch (error) {
      aiSettingsStatus = error.message;
    } finally {
      aiSettingsBusy = false;
    }
  }

  async function saveAISettings() {
    aiSettingsBusy = true;
    aiSettingsStatus = '';
    try {
      activeAI = await requestJson('/ai/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: aiProvider, model: aiModel }),
      });
      aiSettingsStatus = 'AI preferences saved.';
    } catch (error) {
      aiSettingsStatus = error.message;
    } finally {
      aiSettingsBusy = false;
    }
  }

  function scrollToBottom() {
    setTimeout(() => {
      if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 50);
  }

  async function sendChatMessage() {
    if (!aiEnabled || !chatInput.trim() || isChatLoading) return;
    
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
        throw new Error((await res.json().catch(() => null))?.detail || `Server returned ${res.status}`);
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

  function openAssistant() {
    assistantDialog.showModal();
    scrollToBottom();
  }

  async function openInteractionsModal() {
    historyDialog.showModal();
    isFetchingInteractions = true;
    historyError = '';
    try {
      const data = await requestJson('/interactions');
      savedInteractions = data.interactions || [];
    } catch (error) {
      historyError = error.message;
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

  $: completedNodes = courseTopics.filter(topic => progressMap[topic.id]).length;
  $: progressPercent = courseTopics.length ? Math.round(completedNodes * 100 / courseTopics.length) : 0;
</script>

{#snippet timer(compact = false)}
  <div class="timer-tools" role="group" aria-label="Study timer">
    <span class="study-clock" role="timer" aria-label="Time remaining">{formatTime(timeRemaining)}</span>
    <button type="button" class="ui-button ui-quiet" on:click={() => timerActive ? pauseTimer() : startTimer()}
      disabled={!timerActive && (savingSession || !timeRemaining)}>
      {timerActive ? 'Pause' : elapsedSessionSeconds && timeRemaining ? 'Resume' : 'Start'}
    </button>
    <button type="button" class="ui-button ui-quiet" aria-label="Timer options" aria-haspopup="dialog" on:click={showTimerSettings}>
      {compact ? 'Timer' : 'Timer options'}
    </button>
  </div>
{/snippet}

{#snippet lexicon()}
  <Lexicon terms={vocabularies} bind:term={newTerm} bind:definition={newDef} status={vocabStatus}
    {aiEnabled} askingAI={isAskingAI} saving={savingVocab} exporting={isExportingPDF}
    add={addVocab} ask={askAIVocab} listen={playAudio} download={exportVocabPDF} />
{/snippet}

{#snippet manualPractice()}
  <form class="grid gap-4" on:submit|preventDefault={submitLog}>
    <div class="ui-label">
      <label for="content">Original response or transcript</label>
      <textarea id="content" bind:this={practiceEditor} bind:value={logContent} maxlength="25000" rows="5" class="ui-input"
        placeholder="Write your answer or paste your speaking transcript."></textarea>
    </div>
    <details open={Boolean(practice.prompt)} class="ui-details rounded-lg border border-slate-700 px-3">
      <summary class="text-sm font-medium text-slate-300">Source, prompt, feedback, and revision</summary>
      <div class="grid gap-3 pb-3">
        <label class="ui-label">Source or case reference
          <input bind:value={practice.source} maxlength="500" class="ui-input" />
        </label>
        <label class="ui-label">Exercise prompt
          <textarea bind:value={practice.prompt} maxlength="5000" rows="2" class="ui-input"></textarea>
        </label>
        <label class="ui-label">Feedback
          <textarea bind:value={practice.feedback} maxlength="15000" rows="3" class="ui-input"></textarea>
        </label>
        <label class="ui-label">Revised response
          <textarea bind:value={practice.revision} maxlength="25000" rows="4" class="ui-input"></textarea>
        </label>
      </div>
    </details>
    {#if grammarError}<p role="alert" class="text-sm text-rose-200">{grammarError}</p>{/if}
    {#if grammarResult}
      <section class="rounded-lg border border-slate-700 bg-slate-950 p-4" aria-label="Grammar feedback">
        <dl class="grid gap-3 text-sm leading-relaxed">
          <div><dt class="font-semibold text-teal-300">Corrected grammar</dt><dd class="whitespace-pre-wrap wrap-anywhere">{grammarResult.corrected}</dd></div>
          <div><dt class="font-semibold text-teal-300">Natural alternative</dt><dd class="whitespace-pre-wrap wrap-anywhere">{grammarResult.native_alternative}</dd></div>
          <div><dt class="font-semibold text-teal-300">Explanation</dt><dd class="whitespace-pre-wrap wrap-anywhere">{grammarResult.explanation}</dd></div>
        </dl>
        <button type="button" class="ui-button mt-3" on:click={() => {
          practice.feedback = grammarResult.explanation || '';
          practice.revision = grammarResult.corrected || '';
          exportStatus = 'Feedback and revision added to this entry.';
        }}>Copy feedback and correction to this entry</button>
      </section>
    {/if}
    <div class="ui-label max-w-44">
      <label for="entry-status">Status</label>
      <select bind:value={practice.status} id="entry-status" class="ui-input">
        {#each Object.entries(statuses) as [value, label]}<option {value}>{label}</option>{/each}
      </select>
    </div>
    <div class="ui-actions">
      <button class="ui-button ui-primary" disabled={!logContent.trim() || savingPractice}>
        {savingPractice ? 'Saving…' : 'Save practice'}
      </button>
      {#if aiEnabled}
        <button type="button" class="ui-button" on:click={checkGrammar}
          disabled={!logContent.trim() || isCheckingGrammar || isTranscribing}>{isCheckingGrammar ? 'Checking…' : 'Check grammar'}</button>
      {/if}
      {#if transcriptionEnabled}
        <button type="button" class="ui-button" on:click={toggleRecording} disabled={isTranscribing || isCheckingGrammar}>
          {isTranscribing ? 'Transcribing…' : isRecording ? 'Stop recording' : 'Record speech'}
        </button>
      {/if}
      {#if practice.version}
        <a class="ui-button ui-quiet" href={API_URL + '/practice/' + practice.id + '/markdown'}>Download Markdown</a>
      {/if}
    </div>
    {#if exportStatus}<p role="status" class="text-sm text-slate-200">{exportStatus}</p>{/if}
  </form>
{/snippet}

{#if showPracticeJournal}
  <PracticeJournal close={() => showPracticeJournal = false} openEntry={openPractice} />
{/if}

<div class="app-shell" class:reading-shell={appMode === 'reading'} class:compact-reader={compactReading}
  style:cursor={isResizingCompanion ? 'col-resize' : undefined}>
  <a class="ui-button ui-primary skip-link" inert={readerExpanded} href="#workspace-content">Skip to content</a>
  {#if headerVisible}
    <header class="app-header" id="tracker-header" inert={readerExpanded}>
      <div class="app-brand">
        <div class="app-brand-mark" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5c-1.746 0-3.332.477-4.5 1.253v13C4.168 18.477 5.754 18 7.5 18c1.746 0 3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <div>
          <h1 class="text-lg font-semibold leading-tight tracking-tight">English Notes</h1>
          <p class="text-sm text-slate-400">English &amp; credit risk</p>
        </div>
      </div>
      <nav class="app-nav" aria-label="Main navigation">
        <button type="button" class="ui-button ui-quiet" aria-current={appMode === 'dashboard' ? 'page' : undefined}
          on:click={() => changeAppMode('dashboard')}>Dashboard</button>
        <button type="button" class="ui-button ui-quiet" aria-current={appMode === 'reading' ? 'page' : undefined}
          on:click={() => changeAppMode('reading')}>Read Book</button>
        <button type="button" class="ui-button ui-quiet" aria-haspopup="dialog" aria-label="Practice Journal"
          on:click={() => showPracticeJournal = true}>Journal</button>
        <button type="button" class="ui-button ui-quiet" aria-haspopup="dialog" on:click={openAssistant}>AI Assistant</button>
      </nav>
      {@render timer()}
    </header>
  {/if}
  {#if sessionStatus && !timerSettingsOpen}
    <p class="session-status mb-3 text-sm text-slate-300" role="status">{sessionStatus}</p>
  {/if}

  <main id="workspace-content" tabindex="-1" bind:this={workspaceContent}
    class={appMode === 'reading' ? 'flex min-h-0 flex-1' : ''}>
  {#if appMode === 'dashboard'}
    <div class="study-layout">
      <div class="study-column">
        <DailyPractice start={startDailyPractice} />
        <section class="ui-card practice-editor" id="practice-editor" aria-labelledby="practice-editor-title">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h2 class="ui-title" id="practice-editor-title" bind:this={practiceHeading} tabindex="-1">Practice Editor</h2>
            <div class="ui-actions">
              <a class="ui-button ui-quiet lg:hidden" href="#study-resources">Study resources</a>
              <button type="button" class="ui-button ui-quiet" disabled={savingPractice}
                on:click={() => { if (openPractice(null)) focusPracticeEditor(); }}>New entry</button>
            </div>
          </div>
          <div class="skill-picker" role="group" aria-label="Practice skill">
            {#each skills as skill}
              <button type="button" class="ui-button" aria-pressed={practice.skill === skill}
                on:click={() => chooseSkill(skill)}>{skill === 'Credit Risk' ? 'Credit Risk Case Lab' : skill}</button>
            {/each}
          </div>
          <div class="mb-4 grid gap-3 min-[480px]:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
            <div class="ui-label">
              <label for="practice-topic">Topic</label>
              <select class="ui-input" id="practice-topic" value={selectedTopic} on:change={event => selectTopic(event.currentTarget.value)}>
                {#if selectedTopic && !topicNames[selectedTopic]}<option value={selectedTopic}>{selectedTopic}</option>{/if}
                {#each topicGroups as group}
                  <optgroup label={group.label}>
                    {#each group.topics as topic}<option value={topic.id}>{topic.name}</option>{/each}
                  </optgroup>
                {/each}
              </select>
            </div>
            <div class="ui-label">
              <label for="entry-context">Context</label>
              <select bind:value={practice.context} id="entry-context" class="ui-input">
                {#each contexts as context}<option value={context}>{context}</option>{/each}
              </select>
            </div>
          </div>
          {#if guidedModes[practice.skill]}
            {#key guidedKey}
              <StudyTutor bind:this={voiceTutor} initialMode={guidedModes[practice.skill]} aiEnabled={subscriptionAI}
                topicId={selectedTopic || 'General'} topicLabel={topicNames[selectedTopic] || selectedTopic || 'Credit risk'} context={practice.context} />
            {/key}
            <details class="ui-details mt-4 rounded-lg border border-slate-700 px-3" bind:this={manualEntry}>
              <summary class="text-sm font-medium text-slate-300">Manual journal entry</summary>
              <div class="pb-3">{@render manualPractice()}</div>
            </details>
          {:else}
            {@render manualPractice()}
          {/if}
        </section>
      </div>
      <aside id="study-resources" class="resource-column" aria-label="Study resources" tabindex="-1">
        <section class="ui-card" aria-labelledby="progress-title">
          <h2 class="ui-title" id="progress-title">Study progress</h2>
          <dl class="my-4 grid grid-cols-2 gap-3">
            <div>
              <dt class="text-sm text-slate-400">Focus time</dt>
              <dd class="mt-1 text-2xl font-semibold tabular-nums">{sessionStats.total_hours} <span class="text-sm font-normal text-slate-300">h</span></dd>
            </div>
            <div>
              <dt class="text-sm text-slate-400">Course completed</dt>
              <dd class="mt-1 text-2xl font-semibold tabular-nums">{progressPercent}%</dd>
            </div>
          </dl>
          <progress class="course-progress" aria-label="Course completed" max="100" value={progressPercent}></progress>
          <p class="mt-2 text-sm text-slate-400">{completedNodes} of {courseTopics.length} topics</p>
          {#if weeklyStats.some(stat => stat.minutes > 0)}
            <h3 class="mt-5 text-sm font-semibold">Focus time this week</h3>
            <ul class="mt-3 grid grid-cols-7 gap-1" aria-label="Weekly minutes studied" role="list">
              {#each weeklyStats as stat}
                <li class="flex min-w-0 flex-col items-center gap-1 text-xs text-slate-300">
                  <span>{stat.minutes}m</span>
                  <span class="flex h-14 w-full items-end rounded-sm bg-slate-800" aria-hidden="true">
                    <span class="w-full rounded-sm bg-teal-400"
                      style:height={stat.minutes * 100 / peakMinutes + '%'}></span>
                  </span>
                  <span>{stat.day_name}</span>
                </li>
              {/each}
            </ul>
          {:else if weeklyStats.length}
            <p class="mt-4 text-sm text-slate-400">No focus time logged this week.</p>
          {/if}
          {#if sessionStats.last_topic}
            <p class="mt-4 wrap-anywhere border-t border-slate-700 pt-3 text-sm text-slate-300">
              Last studied · {topicNames[sessionStats.last_topic] || sessionStats.last_topic}
            </p>
          {/if}
        </section>
        <details class="ui-card ui-details">
          <summary class="ui-title">Course syllabus</summary>
          {#if progressStatus}<p role="alert" class="mt-2 text-sm text-rose-200">{progressStatus}</p>{/if}
          <div class="mt-2 grid gap-1">
            {#each syllabusData as block, blockIndex (block.id)}
              <button type="button" class="ui-button ui-quiet w-full justify-start text-left"
                aria-expanded={!!expandedBlocks[block.id]} aria-controls={'module-' + blockIndex}
                on:click={() => toggleBlock(block.id)}>{block.name}</button>
              <div id={'module-' + blockIndex} hidden={!expandedBlocks[block.id]} class="ml-3 border-l border-slate-700 pl-2">
                {#each block.children as chapter, chapterIndex (chapter.id)}
                  {#if chapter.children.length}
                    <button type="button" class="ui-button ui-quiet w-full justify-start text-left"
                      aria-expanded={!!expandedChapters[chapter.id]} aria-controls={'chapter-' + blockIndex + '-' + chapterIndex}
                      on:click={() => toggleChapter(chapter.id)}>{chapter.name}</button>
                  {/if}
                  <div id={'chapter-' + blockIndex + '-' + chapterIndex} hidden={chapter.children.length && !expandedChapters[chapter.id]}>
                    {#each chapter.children.length ? chapter.children : [chapter] as item (item.id)}
                      <label class="flex min-h-11 cursor-pointer items-center gap-2 py-2 text-sm text-slate-300">
                        <input type="checkbox" class="size-4 shrink-0 accent-teal-400" checked={!!progressMap[item.id]}
                          disabled={pendingProgress.has(item.id)} on:change={() => toggleNode(item.id)} />
                        {item.name}
                      </label>
                    {/each}
                  </div>
                {/each}
              </div>
            {/each}
          </div>
        </details>
        {@render lexicon()}
      </aside>
    </div>
  {:else}
  {#if !headerVisible}<h1 class="sr-only">Credit risk library</h1>{/if}
  <div class="flex flex-1 min-h-0 lg:overflow-hidden relative z-10 w-full" style:z-index={readerExpanded ? 60 : undefined}>
    <!-- Reading Mode Layout -->
    {#if appMode === 'reading'}
    <div class="flex-1 min-h-0 flex gap-2 pb-4 w-full" bind:this={readingLayout}
      style:pointer-events={isResizingCompanion ? 'none' : undefined}
      style:padding-bottom={compactReading ? 0 : undefined}>
      
      <!-- PDF Viewer Area -->
      <section class="min-w-0 flex-1 flex-col relative lg:h-full lg:overflow-hidden {showCompanion ? 'hidden lg:flex' : 'flex'}">
        
        <div class="mb-2 flex shrink-0 flex-wrap items-center gap-2" inert={readerExpanded}>
          {#if selectedBook}
          <div class="flex flex-wrap gap-1 rounded-lg border border-slate-800 p-0.5" role="group" aria-label="Credit risk books">
            {#each Object.entries(bookTitles) as [book, title]}
              {#if books?.[book]}
                <button type="button" class="ui-button ui-quiet aria-pressed:bg-teal-950 aria-pressed:font-semibold aria-pressed:text-teal-200"
                  aria-pressed={selectedBook === book} on:click={() => {
                    currentBook = book;
                    browserPdfStatus = '';
                  }}>{title} PDF</button>
              {/if}
            {/each}
          </div>
          {/if}
          {#if selectedBook && nativePdfAvailable}
            <button type="button" class="ui-button" class:ui-primary={desktopReading}
              on:click={switchPdfReader}>{desktopReading ? 'Study reader' : 'Browser PDF'}</button>
          {/if}
          <button type="button" class="ui-button"
            bind:this={notesButton} aria-expanded={showCompanion} aria-controls={showCompanion ? 'reading-companion' : undefined}
            on:click={() => setReadingNotes(!showCompanion)}>
            {showCompanion ? 'Hide reading notes' : 'Reading notes'}
          </button>
          {#if compactReading}
            <div class="ui-actions reader-controls ml-auto" role="group" aria-label="Reader controls">
              {#if !headerVisible}
                <button type="button" class="ui-button ui-quiet" aria-haspopup="dialog" on:click={openAssistant}>AI Assistant</button>
                {@render timer(true)}
              {/if}
              {#if selectedBook}
                <a class="ui-button ui-quiet"
                  href={pdfUrl + '#page=' + bookPages[selectedBook]} target="_blank" rel="noopener">Open PDF tab</a>
                {#if desktopReading && browserFullscreenAvailable}
                  <button type="button" class="ui-button ui-quiet"
                    on:click={showBrowserPdfFullscreen}>Full screen</button>
                {/if}
              {/if}
              <button type="button" class="ui-button ui-quiet"
                aria-expanded={showReadingHeader} aria-controls={showReadingHeader ? 'tracker-header' : undefined}
                on:click={() => showReadingHeader = !showReadingHeader}>
                {showReadingHeader ? 'Hide header' : 'Show header'}
              </button>
            </div>
          {/if}
        </div>
        {#if browserPdfStatus && desktopReading}
          <p role="status" class="mb-2 text-sm text-slate-300">{browserPdfStatus}</p>
        {/if}
        {#if selectedBook}
          {#key selectedBook}
            {#if desktopReading}
              <iframe bind:this={browserPdf} src={pdfUrl + '#page=' + bookPages[selectedBook]} title={bookTitles[selectedBook] + ' PDF'}
                class="min-h-0 w-full flex-1 rounded-lg border border-slate-800 bg-slate-900" allowfullscreen></iframe>
            {:else}
              <BookReader url={pdfUrl} title={bookTitles[selectedBook]} bind:this={studyReader}
                filename={selectedBook + '.pdf'} bind:page={bookPages[selectedBook]} bind:expanded={readerExpanded}
                onExcerpt={askAboutPdf} />
            {/if}
          {/key}
        {:else}
          <p class="rounded-xl border border-slate-800 bg-slate-900 p-5 text-sm text-slate-300">
            {books ? 'No books are available in the private library.' : 'Loading the private library…'}
          </p>
        {/if}
      </section>

    <!-- Reading Companion Sidebar -->
    {#if companionOpened}
      <!-- Resizer Handle for Companion -->
      {#if showCompanion}
      <!-- svelte-ignore a11y_no_noninteractive_tabindex a11y_no_noninteractive_element_interactions (WAI-ARIA focusable window splitter.) -->
      <div class="group z-10 hidden w-4 shrink-0 cursor-col-resize items-center justify-center rounded focus-visible:outline-2 focus-visible:outline-teal-300 lg:flex"
        role="separator" tabindex="0" aria-label="Reading notes width" aria-orientation="vertical" aria-controls="reading-companion"
        aria-valuemin="280" aria-valuemax="800" aria-valuenow={companionWidth}
        on:mousedown={startResizeCompanion} on:keydown={resizeCompanionWithKeys}>
        <div class="h-12 w-1 rounded-full bg-slate-600 group-hover:bg-teal-400 group-focus-visible:bg-teal-400"></div>
      </div>
      {/if}

      <section id="reading-companion" aria-labelledby="companion-title" inert={readerExpanded || !showCompanion}
        class="max-h-[82dvh] min-w-0 flex-1 flex-col overflow-hidden rounded-xl border border-slate-700 bg-slate-900 p-3 shadow-xl lg:h-full lg:max-h-none lg:max-w-[52vw] lg:w-(--companion-width) lg:flex-none lg:p-4 {showCompanion ? 'flex' : 'hidden'}"
        style:--companion-width="{companionWidth}px">
        <div class="mb-3 flex shrink-0 items-center justify-between gap-2 border-b border-slate-800 pb-2">
          <h2 id="companion-title" class="text-base font-semibold text-slate-100">Reading Companion</h2>
          <button type="button" class="ui-button ui-quiet"
            on:click={() => setReadingNotes(false)}><span class="lg:hidden">Back to PDF</span><span class="hidden lg:inline">Close notes</span></button>
        </div>
        
        <div class="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto custom-scrollbar">
          <StudyTutor bind:this={readingTutor} initialMode="excerpt" aiEnabled={subscriptionAI}
            topicId={selectedTopic || 'General'} topicLabel={topicNames[selectedTopic] || selectedTopic || 'Credit risk'}
            book={selectedBook || 'anderson'} page={desktopReading ? null : bookPages[selectedBook]} />

          {@render lexicon()}

          <details class="ui-card ui-details p-3">
            <summary class="ui-title">Other reading tools</summary>
          <div class="pt-2">
            <label class="ui-label">Reading note
              <textarea bind:value={doubtContent} on:paste={handlePaste} rows="4" class="ui-input"
                placeholder={subscriptionAI ? "Paste a sentence from the book…" : "Paste a sentence or an image from the book…"}></textarea>
            </label>
            {#if doubtImageBase64}
              <div class="mt-3 flex flex-wrap items-center gap-2">
                <img src={doubtImageBase64} alt="Pasted snapshot" class="max-h-28 max-w-full rounded object-contain" />
                <button type="button" class="ui-button" on:click={() => doubtImageBase64 = null}>Remove image</button>
              </div>
            {/if}
            <div class="ui-actions mt-3">
              {#if onlineHelpers}
                <button type="button" class="ui-button" on:click={() => translateDoubt('quick')} disabled={!doubtContent.trim() || isTranslating}>
                  {isTranslating && translateMode === 'quick' ? 'Translating…' : 'Translate to Indonesian'}
                </button>
                <button type="button" class="ui-button" on:click={() => translateDoubt('comprehensive')} disabled={!doubtContent.trim() || isTranslating}>
                  {isTranslating && translateMode === 'comprehensive' ? 'Analyzing…' : 'Detailed translation'}
                </button>
              {/if}
              {#if aiEnabled}
                <button type="button" class="ui-button" on:click={explainDoubt} disabled={(!doubtContent.trim() && !doubtImageBase64) || isExplaining}>
                  {isExplaining ? 'Preparing…' : 'Explain note'}
                </button>
              {/if}
              <button type="button" class="ui-button ui-primary" on:click={submitDoubt} disabled={!doubtContent.trim() || savingDoubt}>Save question to journal</button>
            </div>
            {#if doubtStatus}<p role="status" class="mt-2 text-sm text-slate-300">{doubtStatus}</p>{/if}

            {#if explainResult}
              <dl class="mt-4 grid gap-3 rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm leading-relaxed">
                {#each [
                  ['Core concept in Indonesian', explainResult.core_concept],
                  ['Practical example in Indonesian', explainResult.practical_example],
                  ['Analogy', explainResult.analogy],
                  ['Explanation in English', explainResult.english_explanation],
                  ['Useful phrases', explainResult.phrasing_breakdown],
                ] as [label, value]}
                  {#if value}
                    <div>
                      <dt class="font-semibold text-teal-300">{label}</dt>
                      <dd class="markdown-body text-slate-200">{@html renderMarkdown(value)}</dd>
                    </div>
                  {/if}
                {/each}
              </dl>
            {/if}

            {#if translateResult}
              <section aria-label="Translation result" class="mt-4 grid gap-4 rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm leading-relaxed">
                <div>
                  <div class="flex flex-wrap items-center justify-between gap-1">
                    <h3 class="font-semibold text-teal-300">Indonesian translation</h3>
                    <button type="button" class="ui-button ui-quiet" on:click={() => playAudio(doubtContent)}>Listen to original</button>
                  </div>
                  <p class="whitespace-pre-wrap wrap-anywhere">{translateResult.translation}</p>
                </div>
                {#if translateResult.dictionary?.length}
                  <div class="grid gap-3">
                    <h3 class="font-semibold text-teal-300">Dictionary</h3>
                    {#each translateResult.dictionary as entry}
                      <div class="border-l-2 border-slate-700 pl-3">
                        <div class="flex flex-wrap items-center justify-between gap-1">
                          <p class="wrap-anywhere font-medium">{entry.word} <span class="text-slate-400">{entry.phonetic}</span></p>
                          <button type="button" class="ui-button ui-quiet" aria-label={'Listen to ' + entry.word} on:click={() => playAudio(entry.word)}>Listen</button>
                        </div>
                        <ul class="list-disc space-y-1 pl-5">
                          {#each entry.meanings as meaning}
                            <li class="wrap-anywhere">
                              <em class="text-teal-300">{meaning.pos}</em> {meaning.def}
                              {#if meaning.ex}<p class="text-slate-400">{meaning.ex}</p>{/if}
                            </li>
                          {/each}
                        </ul>
                      </div>
                    {/each}
                  </div>
                {/if}
                {#if translateResult.glossary?.length}
                  <div class="grid gap-3">
                    <h3 class="font-semibold text-teal-300">Credit risk context</h3>
                    {#each translateResult.glossary as entry}
                      <div class="border-l-2 border-slate-700 pl-3">
                        <div class="flex flex-wrap items-center justify-between gap-1">
                          <p class="wrap-anywhere font-medium">{entry.term}</p>
                          <button type="button" class="ui-button ui-quiet" aria-label={'Listen to ' + entry.term} on:click={() => playAudio(entry.term)}>Listen</button>
                        </div>
                        <dl class="grid gap-1 wrap-anywhere">
                          <div><dt class="font-medium">General meaning</dt><dd class="text-slate-300">{entry.general}</dd></div>
                          <div><dt class="font-medium">Credit risk meaning</dt><dd class="text-slate-300">{entry.credit}</dd></div>
                          <div><dt class="font-medium">In this passage</dt><dd class="text-slate-300">{entry.context}</dd></div>
                        </dl>
                      </div>
                    {/each}
                  </div>
                {/if}
              </section>
            {/if}
          </div>
          </details>

        </div>
      </section>
    {/if}

  </div>
  {/if}
</div>
{/if}


  </main>

  <dialog class="ui-dialog max-w-md" bind:this={timerDialog} on:close={() => timerSettingsOpen = false} aria-labelledby="timer-dialog-title">
    <div class="ui-dialog-header">
      <h2 class="ui-dialog-title" id="timer-dialog-title">Study timer</h2>
      <button type="button" class="ui-button ui-quiet" on:click={() => timerDialog.close()}>Close</button>
    </div>
    <p class="mt-4 text-sm text-slate-300">Stage · {timerActive || elapsedSessionSeconds ? activeTimerPillar : appMode === 'reading' ? 'Reading Comprehension' : pillars[currentPillarIndex]}</p>
    <form class="mt-4 flex flex-wrap items-end gap-2" on:submit|preventDefault={setTimer}>
      <label class="ui-label">Duration in minutes
        <input class="ui-input" type="number" bind:value={customMinutes} min="1" max="120" step="1" required
          disabled={timerActive || savingSession} />
      </label>
      <button class="ui-button" disabled={timerActive || savingSession || elapsedSessionSeconds > 0}>Set duration</button>
    </form>
    {#if elapsedSessionSeconds > 0}
      <p class="mt-2 text-sm text-slate-400">Save or reset the current session to change the duration.</p>
    {/if}
    <div class="ui-actions mt-4">
      <button type="button" class="ui-button ui-primary" on:click={logStudySession} disabled={elapsedSessionSeconds < 60 || savingSession}>
        {savingSession ? 'Saving…' : 'Stop & Save'}
      </button>
      <button type="button" class="ui-button" on:click={resetTimer} disabled={savingSession}>Reset timer</button>
      <button type="button" class="ui-button" on:click={nextPillar}
        disabled={currentPillarIndex === pillars.length - 1 || savingSession || appMode === 'reading'}>Next Stage</button>
    </div>
    {#if sessionStatus && timerSettingsOpen}<p role="status" class="mt-3 text-sm text-slate-200">{sessionStatus}</p>{/if}
  </dialog>

  <dialog bind:this={assistantDialog} class="ui-dialog assistant-dialog" class:assistant-wide={isChatMaximized} aria-labelledby="assistant-title">
    <div class="ui-dialog-header shrink-0">
      <h2 class="ui-dialog-title" id="assistant-title">English AI Assistant</h2>
      <div class="ui-actions">
        {#if subscriptionAI}
          <button type="button" class="ui-button ui-quiet" aria-expanded={showAISettings}
            aria-controls={showAISettings ? 'assistant-settings' : undefined} on:click={() => {
              showAISettings = !showAISettings;
              if (showAISettings) loadAISettings();
            }}>AI settings</button>
        {/if}
        <button type="button" class="ui-button ui-quiet" aria-haspopup="dialog" on:click={openInteractionsModal}>History</button>
        <button type="button" class="ui-button ui-quiet hidden sm:inline-flex" on:click={() => isChatMaximized = !isChatMaximized}>
          {isChatMaximized ? 'Shrink' : 'Expand'}
        </button>
        <button type="button" class="ui-button ui-quiet" on:click={() => assistantDialog.close()}>Close</button>
      </div>
    </div>
    {#if showAISettings && subscriptionAI}
      <form id="assistant-settings" class="shrink-0 space-y-3 border-b border-slate-700 py-4" on:submit|preventDefault={saveAISettings}>
        <div class="grid grid-cols-2 gap-3">
          <label class="ui-label">AI provider
            <select aria-label="AI provider" class="ui-input" bind:value={aiProvider} on:change={() => loadAISettings(aiProvider)} disabled={aiSettingsBusy}>
              <option value="codex">Codex</option>
              <option value="claude">Claude Code</option>
              <option value="gemini" disabled>Gemini · setup pending</option>
            </select>
          </label>
          <label class="ui-label">AI model
            <select aria-label="AI model" class="ui-input" bind:value={aiModel} disabled={aiSettingsBusy}>
              {#each aiModels as model (model)}<option value={model}>{model}</option>{/each}
            </select>
          </label>
        </div>
        {#if activeAI}<p class="wrap-anywhere text-sm text-slate-300">Active model · {activeAI.model}</p>{/if}
        <button class="ui-button ui-primary" disabled={aiSettingsBusy || !aiModel}>Save AI preferences</button>
        {#if aiSettingsStatus}<p role="status" class="text-sm text-slate-300">{aiSettingsStatus}</p>{/if}
      </form>
    {/if}
    <div class="my-3 flex min-h-0 flex-1 flex-col gap-4 overflow-auto rounded-lg bg-slate-950 p-3 sm:p-4"
      role="log" aria-label="Conversation" aria-busy={isChatLoading} bind:this={chatContainer}>
      {#if !chatMessages.length}
        <p class="m-auto max-w-[32ch] text-center text-sm leading-relaxed text-slate-300">{aiEnabled ? 'Ask about a credit risk concept or paste a sentence to discuss.' : 'The AI tutor is unavailable. Your books and journal are still available.'}</p>
      {/if}
      {#each chatMessages as msg}
        <article class={msg.role === 'user' ? 'ml-4 self-end' : 'mr-4 self-start'}>
          <h3 class="mb-1 text-xs font-semibold text-slate-400">{msg.role === 'user' ? 'You' : 'Tutor'}</h3>
          <div class="rounded-xl p-3 text-sm leading-relaxed wrap-anywhere {msg.role === 'user' ? 'whitespace-pre-wrap bg-teal-950 text-teal-100' : 'markdown-body bg-slate-800 text-slate-100'}">
            {#if msg.role === 'assistant'}
              {@html renderMarkdown(msg.content)}
              {#if !msg.content && isChatLoading}<span>Preparing response…</span>{/if}
            {:else}
              {msg.content}
            {/if}
          </div>
        </article>
      {/each}
    </div>
    <form class="shrink-0" on:submit|preventDefault={sendChatMessage}>
      <label for="assistant-message" class="text-sm font-medium">Message</label>
      <div class="mt-1.5 flex items-end gap-2">
        <input id="assistant-message" type="text" bind:value={chatInput} class="ui-input flex-1"
          disabled={!aiEnabled || isChatLoading} />
        <button type="submit" class="ui-button ui-primary" disabled={!aiEnabled || !chatInput.trim() || isChatLoading}>Send</button>
      </div>
    </form>
  </dialog>

  <dialog class="ui-dialog" bind:this={historyDialog} aria-labelledby="history-title">
    <div class="ui-dialog-header">
      <h2 class="ui-dialog-title" id="history-title">AI history</h2>
      <button type="button" class="ui-button ui-quiet" on:click={() => historyDialog.close()}>Close</button>
    </div>
    <div class="ui-label my-4 max-w-56">
      <label for="interaction-type">Interaction type</label>
      <select class="ui-input" id="interaction-type" bind:value={interactionsFilter}>
        <option value="All">All types</option>
        <option value="Chatbot">Chatbot</option>
        <option value="Grammar">Grammar</option>
        <option value="Explain">Explanation</option>
      </select>
    </div>
    {#if isFetchingInteractions}
      <p role="status" class="text-sm text-slate-300">Loading history…</p>
    {:else if historyError}
      <p role="alert" class="text-sm text-rose-200">{historyError}</p>
    {:else}
      <div class="grid gap-3">
        {#each savedInteractions.filter(item => interactionsFilter === 'All' || item.interaction_type === interactionsFilter) as item}
          <article class="rounded-lg border border-slate-700 p-4">
            <h3 class="text-base font-semibold">{item.interaction_type}</h3>
            <p class="mt-1 text-sm text-slate-400">{new Date(item.created_at).toLocaleString()}</p>
            <p class="my-3 whitespace-pre-wrap wrap-anywhere border-l-2 border-slate-600 pl-3 text-sm text-slate-200">{item.input_text}</p>
            <div class="markdown-body text-sm leading-relaxed text-slate-300">{@html renderMarkdown(item.response_text)}</div>
          </article>
        {:else}
          <p class="text-sm text-slate-300">No matching interactions.</p>
        {/each}
      </div>
    {/if}
  </dialog>
</div>
