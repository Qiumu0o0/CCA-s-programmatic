# Presentation Specification

## Deliverables

- Editable Beamer source: `summer_research_presentation.tex`
- Compiled presentation: `summer_research_presentation.pdf`
- XJTU theme file: `xjtu.sty`
- Visual assets: `assets/xjtu_logo.png`, `assets/xjtu_background.png`, and
  `assets/example27_reference.png`

All deliverables are stored in the current `presentation/` directory.

## Presentation Context

- Presenter: Zixi Wang
- Audience: professors, including faculty beyond the research mentor
- Evaluation purpose: assess an undergraduate summer research outcome
- Language: English
- Format: LaTeX Beamer
- Target duration: approximately 5 minutes
- Slide count: 6 slides, including the title slide

## Research Theme

**Programmatic Modeling of Concurrent Composition and High-Order Observers for Labeled Finite-State Automata**

The presentation explains how mathematical constructions for state estimation
in discrete-event systems were translated into a modular programmatic pipeline
and validated by reproducing Example 27 from the source thesis.

## Source Scope

Content is based on:

- `../docs/Outline.md`
- `../docs/科研训练报告revision.pdf`
- `../docs/2023ARC_DES.pdf`
- `../docs/High-Order_Property.pdf`
- Example 27 inputs under `../data/models/` and `../data/agents/`
- Example 27 outputs under `../data/results/`

No unsupported experimental results are added.

## Template and Visual Design

- Template: XJTU LaTeX Beamer theme adapted from
  `hjnnjh/XJTU-LaTeX-Beamer-Template`
- Native aspect ratio: 4:3
- Primary color: XJTU blue (`#074287`)
- Repeated elements: XJTU campus background, blue header, two-level footer,
  presenter, institution, short title, and slide number
- Title slide: title, subtitle, presenter, institution, event label, and XJTU logo
- Evidence slide: published Example 27 figure, enlarged to preserve legibility
- Typography: Latin Modern Sans for text and serif mathematics

The downloaded template is unofficial. Its repository states that it is based
on the XJTU Beamer template published on Overleaf.

## Narrative and Timing

1. **Title** — 15 seconds
2. **Research Goal** — 45 seconds
3. **Concurrent Composition and Observers** — 55 seconds
4. **Order-2 Observer Pipeline** — 75 seconds
5. **Validation with Example 27** — 80 seconds
6. **Outcomes and Future Work** — 30 seconds

Estimated total: 5 minutes.

## Example 27 Validation Evidence

- Input automaton: 6 states and 7 transitions
- Agents: two distinct observation models
- Agent 1 observer: 4 states and 5 transitions
- Intermediate composition: 24 states and 23 transitions
- Final order-2 observer: 5 states and 5 transitions
- Structural result: the generated observer reproduces the published diagram
- Property result: reachable state `{(2,B)}` contains only a singleton estimate,
  so the tested order-2 estimation property does not hold

## Content Rules

- Prioritize the student's implementation and validation outcome
- Include only the mathematical definitions needed to understand the result
- Use concise, direct slide text suitable for a mixed faculty audience
- Keep implementation filenames visible because modular software is a key output
- Cite the two research sources on the relevant slides
- Do not claim formal software correctness beyond the reproduced validation case

## Build and Verification

Compile from `presentation/` with:

```powershell
pdflatex --interaction=nonstopmode --halt-on-error summer_research_presentation.tex
pdflatex --interaction=nonstopmode --halt-on-error summer_research_presentation.tex
```

Verification includes successful compilation, six-page output, visual rendering
of every page, checks for clipped or overlapping text, and comparison of the
Example 27 result with the published figure.

## Known Limitations

- Example 27 is the principal validation case presented.
- The deck does not report scalability measurements because the supplied
  materials contain no runtime benchmark.
- The XJTU Beamer theme used here is community-maintained rather than an
  officially issued university presentation template.
