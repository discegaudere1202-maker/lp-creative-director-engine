# Scene Spec Parallel Render Architecture

Status: EXPERIMENT / ACTIVE  
Owner: Sarah PM  
Human Ground Truth: Shun  
SSOT Issue: #135  
Date: 2026-09-28

## Why this experiment exists

The previous image-first architecture proved that generated full-page visuals can reach a much wider creative range than direct HTML generation, but the reverse-conversion step from flattened design image to production HTML caused severe fidelity loss and a difficult boundary-recovery problem.

Shun's latest direction is to test a different architecture before investing further in image-to-HTML boundary reconstruction.

## Core idea

Do **not** make the generated image the parent of the HTML.

Create a shared structural source of truth — a **Visual Scene Spec** — that owns the important design decisions before either representation is rendered.

```text
Company Truth / Evidence
→ Marketing IA / Copy
→ Creative Direction
→ Visual Scene Spec
   ├─ validation visual / design image (optional during research)
   └─ HTML / CSS / Motion renderer
→ Human QA
→ Responsive QA
```

The validation visual and the HTML are siblings. The HTML is not reverse-engineered from a flattened image.

## What the Scene Spec must own

At minimum:

- section order and marketing purpose
- copy hierarchy
- layout family / composition grammar
- section geometry and spatial ratios
- media ownership and crop intent
- typography hierarchy
- palette / material treatment
- layering / z-order
- section-boundary geometry (for example reusable SVG paths)
- motion assignment per layer / section
- responsive intent
- prohibited patterns / anti-template constraints

A Scene Spec must be concrete enough that the HTML renderer does not need to invent the design.

## Critical difference from the old direct-render architecture

Old approach:

```text
Creative Direction / Tokens / Modules
→ Renderer interprets missing visual decisions
→ HTML
```

New experiment:

```text
Creative Direction
→ Visual design decisions are explicitly resolved in Scene Spec
→ HTML renderer implements those decisions
```

The objective is to move creative responsibility upstream from the renderer while preserving structural data.

## Role of image generation

### During validation / research

Image generation may still be used to compare candidate Scene Specs and determine whether a spec produces enough creative quality / originality.

### During future automated production

If Scene Spec generation and quality selection become reliable enough, a separate full-page generated image does **not** need to be produced for every LP. The production path can become:

```text
Evidence → IA / Copy → Creative Direction → Scene Spec → HTML / Motion → QA
```

The research image is therefore a validation tool, not a mandatory permanent production dependency.

## Boundary strategy

Section boundaries are no longer inferred after the fact from a flattened image.

The Scene Spec owns the boundary geometry directly, e.g. an SVG path or parametric divider definition. The same boundary definition can be used by the visual renderer and the HTML renderer.

This removes the Hero/Concept-style reverse-recognition problem by construction.

## Current experiment — MELT SKIN Scene Spec v1

Goal: build one complete sales-sample LP that feels worth a premium custom-production fee while using the new architecture.

Target sections:

1. Hero
2. Concept
3. Approach
4. Ingredients
5. Product
6. How To / Ritual
7. Story
8. Voice
9. FAQ
10. Final CTA

Creative Direction: **Quiet Mineral Editorial** — warm natural materials, quiet luxury, asymmetrical editorial layout, tactile skin / stone / water language, restrained motion.

The prototype uses clean media assets as section assets. It does not use flattened section screenshots as the layout implementation.

## Evaluation

This experiment should be compared against:

- prior direct HTML generations
- prior full-page-image → HTML attempts
- the generated-image creative-quality ceiling

Shun Human Feedback is the highest authority.

Success means the HTML itself feels like a finished premium LP rather than a generic template, while remaining real DOM, responsive and motion-capable.
