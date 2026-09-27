# Issue #119｜Research-to-Production Architecture Recovery

Owner: 璃子（Research / Creative Direction / Architecture Recovery）  
Highest Human Reality: **「画像品質は上がったが全体デザインは酷い」**  
Baseline main: `81de8970bd25f9c1f44cca99a3430ea6654cc370`

## 1. Executive conclusion

Shun's VALUE_RETURN is valid and overrides the prior internal PASS on visible design quality.

The repository already contains strong benchmark research, Creative Families, and a Module Composition Pattern Registry. The problem is not that the research never happened. The problem is that the Production path does not contain a faithful visual bridge from those researched mechanisms into real renderer variants.

The actual chain today is closer to:

`benchmark research -> pattern registry -> semantic CompositionPlan -> generic authored labels/tokens -> one shared renderer skeleton -> screenshot`

The intended chain must become:

`Company Truth -> Creative Fit -> Family freeze -> Decision Signature -> compatible research patterns -> company-specific Production Variant selection -> Page Art Direction Spine -> variant-faithful renderer -> screenshot -> whole-page Human Reality gate`

This is a systemic design-architecture recovery, not a CSS polish task.

## 2. Verified root cause

### 2.1 Research exists

Issue #44 defines research patterns including:

- `M-HERO-01..03`
- `M-TRUST-01..02`
- `M-PROBLEM-01`
- `M-STORY-01`
- `M-SERVICE-01`
- `M-PROCESS-01`
- `M-HUMAN-01`
- `M-GALLERY-01`
- `M-OFFER-01`
- `M-CTA-01`
- `M-END-01..02`

These are explicitly research grammars, not a component library.

### 2.2 The bridge is missing

Production code does not consume the Issue #44 `pattern_id` chain as dedicated renderer variants. Instead, `authored_composition_contract.py` compresses decisions into small semantic sets such as hero/core/trust/closing plus scene intents. Then `premium_authorship.py` compresses the visual layer again into global copy dictionaries, a handful of hero labels, four visual voice modes, a small density vocabulary and a shared HTML/CSS page skeleton.

That shared skeleton includes the same broad vocabulary across samples: header, hero, offer grid, indexed `premium-scene`, proof cards, CTA pills, dark closing panel and common responsive collapse.

This means upstream semantic divergence can be real while downstream visual divergence remains weak.

### 2.3 Why #114/#116 did not solve it

Issue #114 correctly identified public-copy, hero, rhythm, media-story, CTA, motion and mobile gaps. The mistaken assumption was that a **minimal uplift on top of the existing renderer** would be enough.

Issue #116 implemented those uplifts but preserved the compression architecture. Better assets, public copy and a few visual modes improved the surface without restoring the missing benchmark-mechanism-to-visual-variant bridge.

Therefore the statement from #114 that a renderer-level redesign was unnecessary is withdrawn.

## 3. Why internal PASS was possible

The internal gates proved useful things:

- Family remained frozen;
- rights/provenance were safe;
- evidence boundaries were respected;
- no identity routing occurred;
- CompositionPlan was preserved;
- responsive widths rendered safely;
- images improved;
- local topology/metadata differences existed.

But those are not equivalent to whole-page premium design quality.

The missing gate asked neither:

> Is the selected benchmark mechanism visibly recognizable in the screenshot?

nor:

> Does this entire page feel like one company-specific piece of art direction rather than the same renderer wearing different content?

As a result, **defect absence + semantic divergence was treated as visual quality**, which allowed Aoi/internal PASS despite poor owner-level whole-page design.

## 4. Production-ready Premium Module Variant Library

A Production Variant is not a generic block and not a token bundle.

Each variant must encode:

- composition/silhouette;
- grid/alignment;
- typography hierarchy;
- spacing / negative-space rhythm;
- media geometry / crop / layering;
- material/decorative behavior;
- copy-density contract;
- adjacency / transition behavior;
- meaningful motion where relevant;
- desktop behavior;
- mobile re-art-direction;
- compatible/incompatible Family and decision conditions;
- evidence/media requirements;
- template-risk controls;
- concrete renderer implementation identity;
- screenshot acceptance evidence.

Initial contracts map every Issue #44 module pattern to at least one Production Variant blueprint. These are contracts only in Issue #119; they are **not yet implemented** and must not be called visually verified.

## 5. Page Art Direction Spine

Premium modules alone can still create a component collage. Therefore each page also requires a Page Art Direction Spine with:

- primary visual thesis;
- silhouette strategy;
- type authority strategy;
- density arc;
- media arc;
- material language;
- contrast strategy;
- closing resolution.

The spine coordinates modules but may not erase their mechanism-specific design behavior.

## 6. Deterministic company-specific selection

The Production selection path is:

`Company Truth`
→ `Creative Fit`
→ `Family freeze`
→ `Decision Signature`
→ `compatible research patterns`
→ `compatible Production Variants`
→ `company-specific Variant Ensemble`
→ `topology/composition`
→ `feasibility adaptation`
→ `renderer`
→ `QA / Human-visible review`

Selection uses real semantic inputs such as decision job, risk, offer structure, evidence shape, sensory/craft/local relationship need, category education, choice guidance and process inspectability.

Selection must never use:

- company ID;
- reference name;
- fixture ID;
- file name;
- random diversity;
- asset scarcity to change Family;
- category -> fixed template;
- Family -> fixed layout.

Every scene must preserve selected alternatives and rejection reasons.

## 7. Renderer recovery contract

The current `render_premium_asset_bound_html` cannot remain the final authority for scenes migrated to Production Variants.

The future renderer must:

1. receive already-selected variant IDs;
2. fail closed on unknown variants;
3. dispatch to real variant-owned DOM/CSS/interaction implementations;
4. allow shared infrastructure only where it does not define authorship;
5. preserve pattern and variant identities into output trace;
6. call each variant's mobile transform;
7. never silently fall back to `premium-scene` generic markup;
8. never fabricate proof/media because a variant expects it.

Shared resets, accessibility, rights-safe media helpers and responsive safety remain reusable. Shared composition that erases the benchmark mechanism does not.

## 8. Benchmark → Screenshot provenance

A scene is not `VISUALLY_VERIFIED` until the full chain exists:

`research evidence`
→ `pattern_id`
→ `production_variant_id`
→ `selection reason`
→ `renderer implementation identity`
→ `responsive transform`
→ `final screenshot`
→ `human mechanism-fidelity review`

Metadata or DOM presence alone cannot establish visual verification.

## 9. Whole-page Aoi gate redesign

Aoi must inspect actual full-page screenshots against the selected research mechanisms.

Required dimensions:

- benchmark mechanism fidelity;
- art-direction specificity;
- module-to-module coherence;
- typography authority;
- page silhouette;
- spatial rhythm;
- image/text integration;
- screenshot-worthy authored moments;
- template resemblance;
- desktop/mobile art direction;
- overall premium impression.

The page RETURNS when overall premium impression is poor even if technical QA is green.

The following are explicitly insufficient reasons to PASS:

- no clipping/overflow;
- different Family IDs;
- different CompositionPlan digests;
- high-quality images;
- different CSS class/variant names;
- green CI.

Shun's actual HTML review remains above internal visible-design PASS.

## 10. Preserve / replace / deprecate

### Preserve

- Creative Family freeze / selector boundaries;
- normalized Company Truth / Decision State / Evidence contracts;
- rights/provenance and Visual Asset Library;
- no fabricated evidence;
- CompositionPlan and migration guards;
- 9-width responsive QA;
- safety/accessibility/reduced-motion infrastructure;
- trace digests.

### Replace as final visual authority

- shared `render_premium_asset_bound_html` page skeleton;
- generic hero labels as final design variants;
- generic `premium-scene` composition;
- four-mode visual voice as complete art direction;
- shared media aspect/crop grammar;
- equal service/offer card grids;
- generic proof card styling;
- universal dark closing panel;
- defect-absence Aoi review.

### Deprecate from Production authorship

- global decision-job copy dictionaries as final company voice;
- index-based alternating density;
- universal CHAPTER numbering;
- global reveal animation as default motion;
- generic stack-only mobile fallback;
- unknown-variant fallback into shared scene markup.

## 11. Rin implementation order

Highest visual leverage first:

1. Production Variant Registry + trace identity.
2. Three research-derived Hero variants.
3. Page Art Direction Spine + renderer dispatch.
4. Variant-owned typography, spacing and media geometry.
5. Trust / Problem / Story / Service / Process / Human / Gallery / Offer variants.
6. CTA + Utility/Emotional Ending variants.
7. Mechanism-specific mobile transforms.
8. Mechanism-specific motion.
9. Regenerate the same 9 Stage A samples and 81 screenshots.

Do not wait until the final step to inspect quality. Hero and page-spine implementation should be visually reviewed before all secondary modules are built.

## 12. Revalidation

Use the existing Stage A cohort and widths so improvement is directly comparable.

Required evidence after implementation:

- 9 samples × 9 widths = 81 full-page screenshots;
- 1440 and 390 contact sheets at minimum;
- research pattern → variant → renderer → screenshot manifest;
- selected and rejected variant reasons;
- rights/evidence provenance;
- Aoi whole-page design review;
- Shun review of actual final HTML.

No one may self-declare ¥1M quality from CI or architecture metadata.

## 13. Final verdict

**PM diagnosis validated.**

Existing research is materially richer than the visible Production system. The missing bridge is a real Production Module Variant layer plus variant-faithful renderer consumption and a whole-page human gate.

The correct recovery is **not** to restart research and **not** to keep polishing the current shared renderer. Preserve the semantic/safety architecture; replace the research-to-visible-design bridge.

Issue #119 is research/spec only. No Production implementation is included.
