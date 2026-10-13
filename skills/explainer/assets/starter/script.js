// Chapters -> scenes -> beats. One beat = one subtitle = one spoken sentence, at most two subtitle lines.
// A chapter's name is the question it answers, cut short enough for the control bar (outline.md, chapter chain).
// A beat's index inside its scene is the `step` that data-at / data-to and HOOK.<scene>(step) see.
// W('...') is a beat the lesson stops after until the viewer presses a [data-go] button.
// D('direction', beat) tells the voice how to read that beat, in one English line: a stance toward the listener,
// then where the reading changes inside this sentence. Write them once the words are final (authoring.md, Directions).
// Numbers come from data.js: write `${V.key}`, never retype a value.
const SCRIPT = [
  {ch: 'TODO the question', scenes: [
    ['intro', [
      'TODO the concrete situation and what we are trying to do.',
      D('TODO how this turn should sound, e.g. curious, like posing a puzzle to a friend; slower on the contrast',
        'TODO why the obvious approach leaves a question unresolved.'),
      'TODO the question this lesson will answer, and its answer in one line.',
    ]],
  ]},
  {ch: 'TODO what that leaves', scenes: [
    ['context', [
      'TODO what this example or experiment is meant to find out, connected to the opening question.',
      'TODO what we will change or compare, and what stays fixed.',
      'TODO what to observe and how it will help answer the question.',
    ]],
    ['worked', [
      'TODO why we need this calculation to answer that question; name the objects before their values.',
      `TODO first input: ${V.a}.`,
      `TODO second input: ${V.b}.`,
      `TODO the result, ${V.ratio}, and only now the name of the concept.`,
    ]],
    ['compute', [
      W(`TODO your turn: same first input, but ${V.quizB}. What is the result?`),
      `TODO the answer is ${V.quizAnswer}, and what it shows.`,
    ]],
  ]},
  {ch: 'Close', scenes: [
    ['end', [
      'TODO takeaway one.',
      'TODO takeaway two.',
      'TODO takeaway three, and what to read or do next.',
    ]],
  ]},
];
