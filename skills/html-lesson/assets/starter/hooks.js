// Runs once at load. Build what never changes at the top level; put what depends on the beat in HOOK.<sceneId>.
// A hook must draw the same screen for the same step however it was reached: set state, never toggle or append.
// Taken by the player, do not redeclare: W B CH HOOK LESSON UI $ quiz, and the player's own state and functions
// (idx, speed, scale, last, units, scenes, render, go, play, seek, fit …). `check` names the clash.
HOOK.worked = step => { $('note').textContent = step >= 3 ? 'TODO what the viewer should notice' : ''; };

quiz('q1', 'q1fb', QUIZ.answer, 0.05, {pct: true});
