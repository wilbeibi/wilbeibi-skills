// Chapters -> scenes -> beats. A beat is one subtitle and one spoken sentence; its index inside the scene is the `step`
// that data-at / data-to and HOOK.<scene>(step) see. W('...') is a beat the lesson pauses after.
// data.js is in scope, so a number in a beat is written ${V.key}, never retyped.
const SCRIPT = [
  {ch: 'Start', scenes: [
    ['intro', [
      'This is a gallery, not a lesson. Each scene shows one way to put an idea on screen.',
      'Three chapters, one per domain: finance, reinforcement learning, distributed systems.',
      'Nothing here is typed twice. Every number is computed from a handful of inputs, so the arithmetic cannot drift.',
    ]],
  ]},
  {ch: '1 Finance', scenes: [
    ['fsplit', [
      'A share price is one number. How much of it pays for the business as it runs today, and how much is a bet?',
      'Split it in two. The first part is the steady-state value; the rest is PVGO, the present value of growth opportunities.',
      'Steady-state value assumes today\'s NOPAT continues forever, so it is NOPAT divided by the cost of capital.',
      `Whatever the price holds beyond that is PVGO. Here, ${V.pvgoPct} of the price is a bet on the future.`,
    ]],
    ['ftable', [
      `Now a worked table. Start from what the company reports: revenue of ${V.revenue}.`,
      `A ${V.margin} operating margin leaves ${V.ebit} of EBIT.`,
      `Take out ${V.tax} tax on that operating profit. What remains, ${V.nopat}, is NOPAT.`,
      `Next, the capital the business needs to earn it: ${V.capital} of invested capital.`,
      `Divide one by the other. ROIC is ${V.roic}, against a cost of capital of ${V.wacc}.`,
    ]],
    ['fquiz', [
      W(`Your turn. Same NOPAT, but the business needs ${V.quizCapital} of invested capital. What is ROIC?`),
      `${V.nopat} over ${V.quizCapital} is ${V.quizRoic}. More capital for the same profit means a lower return on it.`,
    ]],
    ['fbars', [
      'Put that on bars: the same NOPAT earned on more and more invested capital.',
      'The white line is the hurdle, the cost of capital. A bar is only as good as its distance past that line.',
      'The last bar stops exactly on it. Growth at that return makes the company bigger and adds no value.',
    ]],
    ['fmodel', [
      W(`Hold NOPAT at ${V.nopat}. Predict: if more capital is needed for that profit, does ROIC rise or fall?`),
      W('Move the capital slider and watch ROIC cross the cost-of-capital line; the profit stays fixed.'),
      'More capital for the same profit lowers ROIC; this model does not predict how investment changes profit.',
    ]],
  ]},
  {ch: '2 RL', scenes: [
    ['rleq', [
      'An agent keeps a guess for how good each action is. After one step, how should it change that guess?',
      'Move the old estimate toward a target, by a fraction called the step size. That is the whole Q-learning update.',
      `The target is the reward just received plus the discounted value of the best next action. Here, ${V.tdT}.`,
      `The gap between target and old estimate is the TD error, ${V.tdE}. Half of it is added, so Q moves from ${V.tdQ} to ${V.tdU}.`,
    ]],
    ['rlgrid', [
      'A gridworld. Reaching the goal pays plus one, the pit minus one, and every cell starts with a value of zero.',
      W('One sweep updates every cell from its neighbours. Stop and predict: which cells get a value in the first sweep?'),
      'Only one: the cell beside the goal. Value has to be passed along, one cell per sweep.',
      `After the second sweep it has reached two more cells, each discounted by ${V.gamma} per step.`,
      `After ${V.sweepCount} sweeps nothing changes. Follow the largest neighbour from any cell and you have the policy.`,
    ]],
    ['rlcurve', [
      'Value iteration needed the rules of the grid. Q-learning only gets to try moves. Early episodes wander.',
      'After a couple of dozen episodes the trailing average has dropped sharply: good moves are now preferred.',
      `It settles just above the shortest path of ${V.shortest} steps. The gap is exploration, the random moves it keeps making.`,
    ]],
  ]},
  {ch: '3 Distributed systems', scenes: [
    ['dslanes', [
      'Three nodes, time running left to right. All of them are followers in term 1, and the leader has gone quiet.',
      'Node A waits the longest it is willing to wait, hears nothing, and makes itself a candidate for term 2.',
      'It asks the others for their vote. The request to B arrives. The one to C is lost on the way.',
      'B grants its vote. With its own, A holds two of three, a majority. It is the leader of term 2.',
      'The leader now sends heartbeats, so the others keep resetting their timers and no one else stands.',
    ]],
    ['dslog', [
      'Each row is one node\'s log. Each box is an entry, tagged with the term it was written in.',
      'A client writes to the leader. A appends entry 3 to its own log first. Only one node has it.',
      W('A sends it to B, and B stores it. C is slow. Stop and decide: is entry 3 committed?'),
      'Yes. Two of three nodes hold it, and that is a majority. The leader moves the commit index to 3.',
      'C catches up later and nothing changes for entry 3. Entry 4 is now in the same position entry 3 was in.',
    ]],
    ['dsstate', [
      'The same story as a state machine. Every node starts as a follower.',
      'If the election timer runs out, it becomes a candidate and asks for votes.',
      'With votes from a majority it becomes the leader.',
      'And any node that sees a higher term steps back down to follower. That one rule ends split leadership.',
    ]],
  ]},
  {ch: 'Close', scenes: [
    ['end', [
      'Three things carry over to a real lesson. First: ask the plain question, then name the term.',
      'Second: one scene, one idea, and every beat changes something on screen.',
      'Third: make the viewer commit to an answer before you show it.',
    ]],
  ]},
];
