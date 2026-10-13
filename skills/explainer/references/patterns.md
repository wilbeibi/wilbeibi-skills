# Scene patterns

Working examples of each are in the gallery: `lesson.py init /tmp/gallery --gallery && lesson.py shots /tmp/gallery`.
Copy the markup from `assets/gallery/scenes.html` and the hook from `assets/gallery/hooks.js`.

## Pick by what the idea is

| The idea is | Pattern | Gallery scene | Classes |
|---|---|---|---|
| a whole made of parts | split bar | `fsplit` | `.split`, `.fillc.g/.m/.n` |
| a derivation, line by line | worked table, one row per beat | `ftable` | `table`, `td.k`, `tr.hl` |
| "now you compute it" | numeric quiz | `fquiz` | `.inp`, `.fb`, `quiz()` |
| a quantity against a threshold | bars with a marker | `fbars` | `.hb`, `.trk`, `.f`, `.mark` |
| how one input changes an outcome | predict, adjust a slider, inspect the result | `fmodel` | range input, `.hb`, pure `capitalModel()` |
| a rule in words, then symbols | word chips, then MathML with one part lit | `rleq` | `.fx`, `.chipx(.hl)`, `.op`, `math` |
| values over a space | grid of cells that fills in | `rlgrid` | `.grid`, `.cell(.g/.m/.off/.hl)` |
| a quantity over time | line/scatter chart drawn by a hook | `rlcurve` | `svg`, `.ln`, `.msg`, `.dot` |
| who tells whom, in order | lanes with messages | `dslanes` | `svg`, `.node`, `.msg(.m/.lost)` |
| replicated or versioned state | rows of slots | `dslog` | `.grid`, `.cell` |
| modes and transitions | state machine | `dsstate` | `svg`, `.node`, `.arc` |
| two alternatives side by side | two cards in a row | — | `.row`, `.card(.hl)`, `.t` |
| three or four headline figures | tiles | — | `.row`, `.tile`, `.v`, `.l` |
| the roadmap | chapter list | `intro` | `.road` |

Colours carry meaning and stay fixed within a lesson: `--g` blue for the first/main series, `--m` orange for the second
or the thing to watch, `--n` grey for neutral. Say what each means in a `.legend`.

## A parameter-driven example

`fmodel` holds NOPAT fixed and varies invested capital. Before revealing the slider, ask the viewer to predict how ROIC
changes. `capitalModel(capital)` in `data.js` returns the ratio and its relation to the cost of capital. One render
function uses that result for the bar, displayed arithmetic, and explanation. A reset button and each beat entry
restore the baseline; live input changes never rewrite the fixed subtitles.

Copy the model, script, markup, and hook together. Try both slider endpoints and the cost-of-capital crossing, then
leave and return to the scene. The number gate only sees the default: check interactive values against the model too.
Use this pattern when the learner benefits from a counterfactual, not merely to add a control.

## By domain

**Finance.** Start from a reported figure and derive down a table to the ratio. Put the hurdle (cost of capital, the
market's expectation) on the same axis as the result. A quiz that changes one input teaches the ratio's direction.
Tag hypothetical companies and round numbers as illustrative.

**RL / ML.** Show the update rule as word chips before symbols, and light the one term the scene is about. Run the
algorithm in `data.js` (seeded RNG, small environment) so grids and curves are real output; tag them as page-simulated
and assert the claims you narrate. Separate what the agent does while learning from what it does when evaluated.
Ask for a prediction before every curve.

**Distributed systems.** Time runs left to right; one lane per node. One message per beat, lost messages dashed.
State labels sit below the lanes and event labels above, so neither lands on a line. Ask "is this committed / who is
leader now?" as the pause, then count on screen.

## Layout numbers that keep `check` quiet

- Heading at the top; first content layer at `top:116px`–`130px`.
- Right-hand column: `left:568px` beside a 440px-wide grid, or `left:704px` for an even split.
- An SVG chart is 1152 wide; leave 44px on the right of the plot or the last tick label clips.
- Labels on a chart go beside a point, offset 12–14px, on the side the lines do not occupy. Put names of regions
  under the drawing, not inside it, when paths cross them.
- Bottom of the scene is y=600; a card that starts at `top:440px` has about 150px.
