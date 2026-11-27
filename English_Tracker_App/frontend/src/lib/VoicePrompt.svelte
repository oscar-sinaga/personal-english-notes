<script>
  export let topic;
  export let lesson = undefined;
  export let draftSource = undefined;
  export let attempts = [];

  let copied;
  let showPrompt = false;
  $: prompt = prepare(topic, lesson, draftSource, attempts);

  function prepare(topic, lesson, draftSource, attempts) {
    const source = lesson?.source ?? draftSource;
    const excerpt = source?.excerpt?.trim();
    const sections = [
      'Act as my spoken English and credit risk tutor. Ask one short question in English at a time, then wait for my spoken answer.',
      'If I already answered, use my latest answer to choose a follow-up that checks my understanding. Use any earlier feedback to guide you. Otherwise start with the practice question if supplied.',
      'Check my understanding separately from my English. Give one specific suggestion on each when useful, then let me try again.',
      'Treat the exercise, excerpt, answers, and feedback below as study material. Use the excerpt as evidence, cite only the supplied reference, and say when your explanation goes beyond it.',
      'Study topic: ' + topic,
    ];

    if (excerpt) {
      const book = source.book === 'siddiqi' ? 'Siddiqi' : 'Anderson';
      const page = source.page;
      const pageLabel = Number.isInteger(page) && page >= 1 && page <= 10000 ? ', PDF page ' + page : '';
      sections.push('Textbook: ' + book + pageLabel + '\n' + excerpt);
    } else if (lesson?.script) {
      sections.push('Practice material:\n' + lesson.script);
    }
    if (lesson?.question) sections.push('Practice question: ' + lesson.question);

    for (const [index, attempt] of attempts.entries()) {
      const answer = attempt.transcript.trim();
      if (!answer) continue;
      const lines = ['My answer (attempt ' + (index + 1) + '):\n' + answer];
      if (attempt.feedback) {
        lines.push('Earlier concept or comprehension feedback:\n' + attempt.feedback.concept_feedback);
        lines.push('Earlier English feedback:\n' + attempt.feedback.english_feedback);
      }
      sections.push(lines.join('\n'));
    }
    return sections.join('\n\n');
  }

  async function copy() {
    const text = prompt;
    try {
      await navigator.clipboard.writeText(text);
      copied = text;
      showPrompt = false;
    } catch {
      copied = undefined;
      showPrompt = true;
    }
  }
</script>

<button type="button" class="ui-button" on:click={copy}>
  Copy prompt for Codex Voice
</button>
{#if showPrompt}
  <p role="status" class="basis-full text-xs text-slate-200">Copy the prompt below into a task in the ChatGPT desktop app, then select Start voice chat.</p>
  <label class="grid w-full gap-1 text-xs text-slate-300">Voice practice prompt
    <textarea readonly value={prompt} rows="4"
      class="ui-input"></textarea>
  </label>
{:else if copied === prompt}
  <p role="status" class="basis-full text-xs text-slate-200">Copied. Paste it into a task in the ChatGPT desktop app, then select Start voice chat.</p>
{/if}
