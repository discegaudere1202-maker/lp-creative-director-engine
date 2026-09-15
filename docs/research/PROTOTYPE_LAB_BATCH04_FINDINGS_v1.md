# Prototype Lab Batch 04 Findings v1

Updated: 2026-09-15

Targets:
- P11R Observed Material Physicality — rebuild of failed P11
- P12R Verified Product Behavior — rebuild of failed P12

Research artifact:
`prototype_lab_batch04.html` generated outside the repository.

Important:
These are benchmark reconstructions of **physical principles**, not copies of benchmark visual design and not client-facing deliverables.

---

# Source basis

## P11R — Nishizaki Kougei coating process
Official source material supports:
- thin coating layers are accumulated
- coating and sanding are repeated
- spray angle / speed / volume affect finish
- gloss/finish relates to surface smoothness and light reflection

The research prototype only translates these physical facts into a neutral cross-section diagram.
It does not reproduce Nishizaki Kougei's website design.

## P12R — Shupatto mechanism
Official product explanation supports:
- pleated structure
- pulling both ends makes the bag quickly become strip-like
- it can then be made compact

The research prototype abstracts only the mechanism.
It does not reproduce the actual product design.

---

# Runtime QA

Viewports checked:
- 320
- 390
- 768
- 1440

Results:
- horizontal overflow: 0
- short semantic headline fragments: 0

Additional P12 state screenshots:
- open state
- pulled → strip state

Reduced-motion CSS remains present.

---

# P11R Observed Material Physicality

## Previous P11 result
**FAIL**

Why previous version failed:
- generic ellipses
- decorative grain
- no material-specific behavior
- could be reused by unrelated industries

## P11R result
**METHOD PASS / BENCHMARK SUPREMACY PENDING**

### What improved
The new Form is caused by actual observed properties:
1. layering — multiple thin films
2. tool/process interaction — sand / repeat
3. reflection — light response is connected to smoothness
4. time/repetition — coating is not a single-step surface effect

The diagram now loses its reason to exist if those material facts are removed.
That is the Form Causality improvement we wanted.

### Desktop visual assessment
Strong:
- the headline and material cross-section read as one idea
- the right side is quieter than the type, keeping hierarchy clear
- layer count / wood base / reflection cue make the concept interpretable without cards

Weak:
- the cross-section is still a schematic, not a screenshot-worthy craft image
- the coating layers are visually cleaner than real sprayed/finished surfaces
- hover change is educational but not emotionally compelling
- it cannot compete with excellent real craft photography on sensory richness

### Mobile visual assessment
Strong:
- copy and physical diagram become two chapters rather than a shrunken desktop split
- headline semantic integrity survives
- the layer hierarchy is legible at 390

Weak:
- the process legend becomes more instructional than premium
- lower diagram can feel textbook-like if used as the hero rather than a mid-page explainer

### New conclusion
Material Authority has two different quality ceilings:

**EXPLAINER MATERIAL**
- schematic is acceptable
- goal = understand process/physics

**SENSORY MATERIAL**
- requires authentic photography/video/material rendering
- goal = feel surface/weight/temperature/craft

Do not use an explainer diagram as a substitute for sensory evidence when real material assets are available.

---

# P12R Verified Product Behavior

## Previous P12 result
**PREMIUM FAIL**

Why previous version failed:
- generic bars
- no verified geometry or trigger
- “fold/expand” could belong to many products

## P12R result
**METHOD PASS / BENCHMARK SUPREMACY PENDING**

### What improved
The state transition now follows verified product behavior:
1. OPEN state
2. pull both ends
3. pleated body becomes strip-like
4. compact state follows

The trigger/action/benefit relationship is explicit.

### Desktop visual assessment
Strong:
- left copy and right mechanism are immediately readable
- interaction has a single semantic purpose
- pulled state is visibly different without unnecessary animation
- the pleat pattern makes the behavior understandable

Weak:
- neutralized geometry intentionally removes much of actual product identity
- therefore this is a mechanism-study frame, not a final brand frame
- large headline currently has more personality than the product diagram

### Mobile visual assessment
Strong:
- sequence labels remain understandable
- product behavior has enough screen space
- no desktop side-by-side shrink

Weak:
- long English process chips become slightly utilitarian
- in a final Japanese consumer LP, labels should be reduced or integrated more naturally

### New conclusion
There are two Product Behavior modes:

**MECHANISM EXPLAINER**
- abstracted verified geometry is acceptable
- use for technical understanding

**PRODUCT DESIRE FRAME**
- requires authentic product form / real use / texture / human interaction
- use for Hero / high-emotion screenshot peak

A mechanism diagram can support desire but should not automatically replace product reality.

---

# Batch 04 laws

1. A failed generic abstraction can improve when real physics becomes the cause of Form.
2. Form Causality is necessary but still not sufficient for Benchmark Supremacy.
3. Material has at least two authority modes: `EXPLAINER_MATERIAL` and `SENSORY_MATERIAL`.
4. Product behavior has at least two modes: `MECHANISM_EXPLAINER` and `PRODUCT_DESIRE`.
5. Do not ask diagrams to do the emotional job of authentic material/product evidence.
6. Sales State can use a precise explainer while leaving an Enriched Evidence Slot for real sensory assets.
7. Mobile diagrams should be re-chaptered, not compressed.
8. Product/mechanism labels should be reduced when they start to look like lab UI in a final customer-facing frame.

---

# Status

P11:
FAIL → **METHOD PASS / Tournament pending**

P12:
PREMIUM FAIL → **METHOD PASS / Tournament pending**

Neither is yet approved as a premium sales-sample screenshot peak.

Next:
1. put P11R against MATERIAL_PHOTO_CRAFT benchmark pool
2. put P12R against PRODUCT_BEHAVIOR benchmark pool
3. use results to decide whether each belongs as Hero, Mid explainer, or non-peak utility frame
4. continue prototype backlog until 20–30 methods have external Benchmark evidence
