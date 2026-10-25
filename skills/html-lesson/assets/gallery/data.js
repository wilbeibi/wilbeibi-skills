// Everything the gallery shows is derived here. Inputs are typed once, at the top of each block; no DOM in this file.
const fmt = (x, d = 0) => x.toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
const pct = (x, d = 0) => fmt(x * 100, d) + '%';

// ---------- finance: one made-up company ----------
const FIN = (() => {
  const revenue = 1000, margin = 0.20, tax = 0.25, capital = 750, wacc = 0.08, price = 2600;
  const ebit = revenue * margin, nopat = ebit * (1 - tax), steady = nopat / wacc;
  return {revenue, margin, tax, capital, wacc, price, ebit, nopat, steady, pvgo: price - steady, roic: nopat / capital};
})();
// worked table: [line, how it is computed, value]
const FIN_ROWS = [
  ['Revenue', 'given', fmt(FIN.revenue)],
  ['EBIT', `Revenue × operating margin = ${fmt(FIN.revenue)} × ${pct(FIN.margin)}`, fmt(FIN.ebit)],
  ['NOPAT', `EBIT × (1 − tax rate) = ${fmt(FIN.ebit)} × (1 − ${pct(FIN.tax)})`, fmt(FIN.nopat)],
  ['Invested capital', 'given', fmt(FIN.capital)],
  ['ROIC', `NOPAT ÷ Invested capital = ${fmt(FIN.nopat)} ÷ ${fmt(FIN.capital)}`, pct(FIN.roic)],
];
const FIN_QUIZ = {capital: 1000};
FIN_QUIZ.roic = FIN.nopat / FIN_QUIZ.capital * 100;
// same NOPAT on more and more capital; the last one is where ROIC equals the cost of capital
const FIN_BARS = [500, 750, 1000, FIN.nopat / FIN.wacc].map(capital => ({capital, roic: FIN.nopat / capital}));

// Counterfactual: profit stays fixed while the viewer changes the capital needed to earn it.
const CAPITAL = {min: FIN_BARS[0].capital, max: 2500, step: 125, initial: FIN.capital};
const capitalModel = capital => ({
  capital,
  roic: FIN.nopat / capital,
  relation: capital < FIN.nopat / FIN.wacc ? 'above' : capital > FIN.nopat / FIN.wacc ? 'below' : 'at',
});
const CAPITAL_BASE = capitalModel(CAPITAL.initial);
if (!(capitalModel(CAPITAL.min).roic > capitalModel(CAPITAL.max).roic))
  throw new Error('With fixed positive profit, more capital must lower ROIC');

// ---------- RL: one Q-learning update, then a 4x3 gridworld ----------
const TD = (() => {
  const q = 2, alpha = 0.5, r = 1, gamma = 0.9, qnext = 4;
  const target = r + gamma * qnext;
  return {q, alpha, r, gamma, qnext, target, error: target - q, updated: q + alpha * (target - q)};
})();

const GW = (() => {
  const cols = 4, rows = 3, gamma = 0.9;
  const goal = 3, pit = 7, wall = 5, start = 8;          // cell = row * cols + col, row 0 on top
  const moves = [[0, -1, '↑'], [1, 0, '→'], [0, 1, '↓'], [-1, 0, '←']];
  const next = (s, [dx, dy]) => {
    const c = s % cols + dx, r = Math.floor(s / cols) + dy, t = r * cols + c;
    return c < 0 || c >= cols || r < 0 || r >= rows || t === wall ? s : t;
  };
  const terminal = s => s === goal || s === pit;
  const reward = s => s === goal ? 1 : s === pit ? -1 : 0;   // paid on entering s
  const backup = (v, s, m) => { const t = next(s, m); return reward(t) + gamma * (terminal(t) ? 0 : v[t]); };
  // value iteration, one full sweep per entry: V[k+1](s) = max over moves of reward + gamma * V[k](next)
  const sweeps = [Array(cols * rows).fill(0)];
  for (;;) {
    const v = sweeps[sweeps.length - 1];
    const w = v.map((x, s) => terminal(s) || s === wall ? 0 : Math.max(...moves.map(m => backup(v, s, m))));
    if (w.every((x, s) => Math.abs(x - v[s]) < 1e-9)) break;
    sweeps.push(w);
  }
  const final = sweeps[sweeps.length - 1];
  const greedy = s => moves.reduce((best, m) => backup(final, s, m) > backup(final, s, best) + 1e-9 ? m : best);
  let shortest = 0;
  for (let s = start; !terminal(s); s = next(s, greedy(s))) shortest++;
  return {cols, rows, gamma, goal, pit, wall, start, moves, next, terminal, reward, sweeps, greedy, shortest};
})();

// tabular Q-learning on the same grid. Seeded, so the curve is the same on every load.
const QL = (() => {
  let seed = 7;
  const rnd = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
  const alpha = 0.5, eps = 0.1, episodes = 60, cap = 200;
  const Q = Array.from({length: GW.cols * GW.rows}, () => [0, 0, 0, 0]);
  const steps = [];
  for (let e = 0; e < episodes; e++) {
    let s = GW.start, n = 0;
    while (!GW.terminal(s) && n < cap) {
      const top = Math.max(...Q[s]);
      const ties = [0, 1, 2, 3].filter(a => Q[s][a] === top);
      const a = rnd() < eps ? Math.floor(rnd() * 4) : ties[Math.floor(rnd() * ties.length)];
      const t = GW.next(s, GW.moves[a]);
      const target = GW.reward(t) + GW.gamma * (GW.terminal(t) ? 0 : Math.max(...Q[t]));
      Q[s][a] += alpha * (target - Q[s][a]);
      s = t; n++;
    }
    steps.push(n);
  }
  const window = 5;   // trailing mean, so one unlucky episode does not hide the trend
  const mean = steps.map((x, i) => { const w = steps.slice(Math.max(0, i - window + 1), i + 1); return w.reduce((a, b) => a + b, 0) / w.length; });
  return {alpha, eps, episodes, window, steps, mean};
})();

// ---------- distributed systems: a replicated log, three nodes ----------
// per beat: each node's log as the list of terms its entries were written in
const LOG_STEPS = [
  {A: [1, 1], B: [1, 1], C: [1, 1]},
  {A: [1, 1, 2], B: [1, 1], C: [1, 1]},
  {A: [1, 1, 2], B: [1, 1, 2], C: [1, 1]},
  {A: [1, 1, 2], B: [1, 1, 2], C: [1, 1]},
  {A: [1, 1, 2, 2], B: [1, 1, 2], C: [1, 1, 2]},
];
const LOG_SLOTS = 5;
// highest index stored on a majority: sort the log lengths, take the middle one
const majorityIndex = logs => Object.values(logs).map(l => l.length).sort((a, b) => b - a)[Math.floor(Object.keys(logs).length / 2)];

// ---------- values placed in the markup with <span data-v="key"> ----------
const V = {
  price: fmt(FIN.price), steady: fmt(FIN.steady), pvgo: fmt(FIN.pvgo), pvgoPct: pct(FIN.pvgo / FIN.price),
  revenue: fmt(FIN.revenue), margin: pct(FIN.margin), ebit: fmt(FIN.ebit), tax: pct(FIN.tax), capital: fmt(FIN.capital),
  steadyHow: `${fmt(FIN.nopat)} ÷ ${pct(FIN.wacc)}`, pvgoHow: `${fmt(FIN.price)} − ${fmt(FIN.steady)}`,
  nopat: fmt(FIN.nopat), roic: pct(FIN.roic), wacc: pct(FIN.wacc), spread: fmt((FIN.roic - FIN.wacc) * 100) + ' pp',
  quizCapital: fmt(FIN_QUIZ.capital), quizHow: `${fmt(FIN.nopat)} ÷ ${fmt(FIN_QUIZ.capital)}`, quizRoic: fmt(FIN_QUIZ.roic) + '%',
  modelCapital: fmt(CAPITAL_BASE.capital), modelRoic: pct(CAPITAL_BASE.roic),
  tdT: fmt(TD.target, 1), tdE: fmt(TD.error, 1), tdQ: fmt(TD.q, 1), tdU: fmt(TD.updated, 1),
  tdTarget: `${TD.r} + ${TD.gamma} × ${TD.qnext} = ${fmt(TD.target, 1)}`,
  tdError: `${fmt(TD.target, 1)} − ${fmt(TD.q, 1)} = ${fmt(TD.error, 1)}`,
  tdNew: `${fmt(TD.q, 1)} + ${TD.alpha} × ${fmt(TD.error, 1)} = ${fmt(TD.updated, 1)}`,
  tdGiven: `Q(s, a) = ${fmt(TD.q, 1)} · α = ${TD.alpha} · r = ${TD.r} · γ = ${TD.gamma} · best next Q = ${fmt(TD.qnext, 1)}`,
  gamma: String(GW.gamma), sweepCount: String(GW.sweeps.length - 1), shortest: String(GW.shortest),
  qlSetup: `α = ${QL.alpha} · ε = ${QL.eps} · ${QL.episodes} episodes · seeded`,
};
