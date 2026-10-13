// Inputs typed once; everything shown or spoken is derived from them. No DOM in this file (lesson.py also runs it in node).
const fmt = (x, d = 0) => x.toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
const pct = (x, d = 0) => fmt(x * 100, d) + '%';

const EX = (() => {
  const a = 150, b = 750;               // the two inputs of the worked example
  return {a, b, ratio: a / b};
})();
const QUIZ = {b: 1000};
QUIZ.answer = EX.a / QUIZ.b * 100;

// <span data-v="key"> in scenes.html and ${V.key} in script.js
const V = {
  a: fmt(EX.a), b: fmt(EX.b), ratio: pct(EX.ratio),
  quizB: fmt(QUIZ.b), quizAnswer: fmt(QUIZ.answer) + '%',
};
