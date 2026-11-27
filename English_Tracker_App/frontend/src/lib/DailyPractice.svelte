<script>
  import { onMount } from 'svelte';

  export let start;

  const exercises = [
    {
      skill: 'Writing',
      topic: 'Follow up on a loan application',
      instruction: 'Write a short email asking for the latest bank statement. Explain why you need it and when you need it.',
      check: 'Make the request polite and include a clear deadline.'
    },
    {
      skill: 'Speaking',
      topic: 'Explain a credit decision',
      instruction: 'In English, explain to a colleague why you would approve a loan at a lower limit. Speak for one minute.',
      check: 'State your decision, give two reasons, and finish with a next step.'
    },
    {
      skill: 'Reading',
      topic: 'Find the risk in a case note',
      passage: 'Sales rose by 12 percent this quarter, but customers took longer to pay. The borrower used its credit line to cover payroll twice.',
      instruction: 'Read the case note and summarize the risk in two sentences.',
      check: 'Explain why higher sales may still leave the borrower short of cash.'
    },
    {
      skill: 'Listening',
      topic: 'Catch the key details in an update',
      passage: 'We received the application on Monday. The income documents are still missing. If they arrive by Thursday, we can send the decision on Friday.',
      instruction: 'Listen to the update, then write down what is missing and when a decision is expected.',
      check: 'Reveal the transcript after answering and check both details.'
    },
    {
      skill: 'Speaking',
      topic: 'Describe a risk in plain English',
      instruction: 'Explain what late payments can tell a lender. Speak for one minute and use an example from an imaginary business.',
      check: 'Use short sentences and explain any technical term.'
    },
    {
      skill: 'Writing',
      topic: 'Recommend a next step',
      instruction: 'Write three sentences to your manager about a borrower whose monthly repayments have increased. Recommend one action.',
      check: 'Separate the fact, the risk, and your recommendation.'
    },
    {
      skill: 'Reading',
      topic: 'Distinguish a fact from an assumption',
      passage: 'The customer has never missed a payment. The analyst believes income will rise next year, but the customer has not provided a written offer.',
      instruction: 'Identify one confirmed fact and one assumption. Explain what evidence you would ask for.',
      check: 'Make it clear which part of your answer needs verification.'
    }
  ];

  const today = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    timeZone: 'Asia/Jakarta'
  }).format(new Date());
  const exercise = exercises[['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(today)];
  const journalPrompt = [exercise.instruction, exercise.passage, exercise.check].filter(Boolean).join('\n\n');

  let englishVoice;
  let listening = false;
  let utterance;
  let live = true;
  let status = '';
  let requesting = false;
  let recording = false;
  let recorder;
  let stream;
  let audioUrl = '';

  function releaseMicrophone(microphone = stream) {
    microphone?.getTracks().forEach(track => track.stop());
    if (stream === microphone) stream = undefined;
  }

  onMount(() => {
    const synth = window.speechSynthesis;
    function findVoice() {
      englishVoice = synth?.getVoices().find(voice => voice.localService && /^en(?:-|$)/i.test(voice.lang));
    }
    if (exercise.skill === 'Listening') {
      findVoice();
      synth?.addEventListener('voiceschanged', findVoice);
    }
    return () => {
      live = false;
      synth?.removeEventListener('voiceschanged', findVoice);
      if (listening) synth.cancel();
      if (recorder?.state === 'recording') recorder.stop();
      releaseMicrophone();
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  });

  function listen() {
    if (!englishVoice || listening) return;
    status = '';
    utterance = new SpeechSynthesisUtterance(exercise.passage);
    utterance.voice = englishVoice;
    utterance.lang = englishVoice.lang;
    utterance.onend = () => { listening = false; };
    utterance.onerror = () => {
      listening = false;
      status = 'Could not play the audio. Open the transcript to continue.';
    };
    listening = true;
    window.speechSynthesis.speak(utterance);
  }

  async function record() {
    if (requesting || recording) return;
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      status = 'Recording is unavailable in this browser. Say your answer aloud and summarize it in the journal.';
      return;
    }
    requesting = true;
    status = '';
    try {
      const microphone = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!live) {
        microphone.getTracks().forEach(track => track.stop());
        return;
      }
      stream = microphone;
      const capture = new MediaRecorder(stream);
      const chunks = [];
      capture.ondataavailable = ({ data }) => {
        if (data.size) chunks.push(data);
      };
      capture.onstop = () => {
        releaseMicrophone(microphone);
        if (!live || recorder !== capture) return;
        recording = false;
        if (!chunks.length) return;
        if (audioUrl) URL.revokeObjectURL(audioUrl);
        audioUrl = URL.createObjectURL(new Blob(chunks, { type: capture.mimeType || chunks[0].type }));
      };
      capture.onerror = () => {
        releaseMicrophone(microphone);
        if (!live || recorder !== capture) return;
        recording = false;
        status = 'Recording stopped unexpectedly. Check your microphone and try again.';
      };
      capture.start();
      recorder = capture;
      recording = true;
    } catch (error) {
      releaseMicrophone();
      status = error.name === 'NotAllowedError'
        ? 'Microphone access is blocked. Allow it in your browser, or write a summary in the journal.'
        : 'Could not open the microphone. You can still practice aloud and save a summary.';
    } finally {
      requesting = false;
    }
  }
</script>

<section aria-labelledby="daily-title" class="ui-card daily-practice">
  <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
    <h2 id="daily-title" class="text-sm font-semibold text-teal-300">Today’s practice</h2>
    <span class="text-sm text-slate-400">{exercise.skill} · 3–5 min</span>
  </div>
  <h3>{exercise.topic}</h3>
  {#if exercise.skill === 'Reading'}
    <blockquote class="mt-2 border-l-2 border-slate-600 pl-3 text-sm text-slate-300">{exercise.passage}</blockquote>
  {/if}
  <p class="mt-3 max-w-[62ch] text-base leading-relaxed text-slate-200">{exercise.instruction}</p>
  <p class="mt-2 max-w-[62ch] text-sm leading-relaxed text-slate-400">{exercise.check}</p>

  {#if exercise.skill === 'Listening'}
    {#if englishVoice}
      <button type="button" class="ui-button mt-3" on:click={listen} disabled={listening}>
        {listening ? 'Playing…' : 'Play update'}
      </button>
    {:else}
      <p class="mt-3 text-sm text-slate-400">This device has no local English voice. Read the transcript to continue.</p>
    {/if}
    <details class="ui-details mt-2 text-sm text-slate-300">
      <summary class="cursor-pointer">Show transcript</summary>
      <p class="mt-2">{exercise.passage}</p>
    </details>
  {:else if exercise.skill === 'Speaking'}
    {#if recording}
      <button type="button" class="ui-button mt-3" on:click={() => { if (recorder.state === 'recording') recorder.stop(); }}>
        Stop practice recording
      </button>
    {:else}
      <button type="button" class="ui-button mt-3" on:click={record} disabled={requesting}>
        {requesting ? 'Waiting for microphone…' : 'Record on this device'}
      </button>
    {/if}
    {#if audioUrl}
      <audio class="mt-3 w-full max-w-sm" controls src={audioUrl} aria-label="Your practice recording"></audio>
    {/if}
    <p class="mt-2 text-sm text-slate-400">Your recording stays in this tab. Play it back, then save a summary or transcript in the journal.</p>
  {/if}
  {#if status}
    <p role="status" class="mt-2 text-sm text-amber-200">{status}</p>
  {/if}
  <button type="button" class="ui-button ui-primary mt-4"
    disabled={requesting || recording} on:click={() => start(exercise, journalPrompt)}>
    Start today’s practice
  </button>
</section>
