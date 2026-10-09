# Authored P01 to private composition

`pilot_pipeline.compose_authored_preview` connects the two local integration
adapters: a source-linked, authored P01 design-reference packet and an explicit
LP54 composition request. This connection is available for landscaping,
painting, and bars. It does not replace a formal Production Contract.

The original P01 packet is re-created and compared with its source snapshots
before rendering. The intake industry must match the composition industry.
The entire packet, including its 22 original field wrappers, hypotheses,
evidence references, publication policies, and quality states, is copied into
`composition.context.p01_design_brief`. That context key is reserved; callers
cannot substitute their own projection. Other caller context is preserved.

The embedded brief is provenance and decision context. Its internal hypotheses
are not used as displayed company text. Callers still supply the overall theme,
ordered design IDs, company copy, and pinned local images explicitly. The
renderer does not choose a theme from industry alone or fill omitted text from
the catalog's fictional companies. Selection reasoning can be retained in the
caller's context while the actual selection is pinned in the saved input.

```python
from lp_engine.pilot_authoring import build_theme_design_brief
from lp_engine.pilot_pipeline import compose_authored_preview

brief = build_theme_design_brief(private_intake, authored_p01)
manifest = compose_authored_preview(
    brief,
    explicit_composition,
    source_root=trusted_lp54_source,
    output_dir=new_private_output_directory,
    image_root=private_image_directory,
    expected_source_sha256=previously_pinned_source_bundle_hash,
)
```

The output remains `INTERNAL_COMPOSITION_PREVIEW`: browser and visual review
are `NOT_RUN`, formal stage completion is not asserted, and nothing is
published or sent. The saved input and manifest contain the full private
authoring context and must remain outside a public repository. They may be
transferred with the existing artifact-only handoff API without upgrading
their quality or stage-completion status.

See [PILOT_AUTHORING.md](PILOT_AUTHORING.md) for the P01 source boundary and
[PILOT_COMPOSITION.md](PILOT_COMPOSITION.md) for the renderer's payload and source
requirements. Formal P01 authoring, company-specific design decisions,
production orchestration, visual acceptance, and full production timing still
require their respective implementation and review work.
