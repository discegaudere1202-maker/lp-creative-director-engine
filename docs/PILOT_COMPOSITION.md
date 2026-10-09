# Explicit LP54 composition bridge

`lp_engine.pilot_composition` connects caller-supplied company copy, local images,
an explicit theme, and ordered design selections to an existing LP54 source
bundle. It produces a self-contained **INTERNAL_COMPOSITION_PREVIEW**. This
adapter does not author company hypotheses, select a theme, approve designs,
issue a formal production receipt, publish a page, or run a browser.

The technical input below is an adapter envelope. It does not add formal
Production Contract fields, semantic IDs, requirements, or quality thresholds.

## Source and execution

Use a repository checkout with Python dependencies and Node.js installed. Supply
an already materialized, trusted source root containing the existing `src/` and
`assets/fonts/` directories. The adapter evaluates local source as code. Its Node
VM is **not a security sandbox for arbitrary untrusted JavaScript**.

The bridge loads the unmodified `runtime.js`, the three design modules, and
`themes.js`. It uses `renderSection`, validates the selected theme's compatible
IDs, and builds an internal preview frame with the existing theme classes. It
does not load the catalog's demonstration company data, apply the theme's demo
image overrides, or use its footer that labels every business fictional.

Eight existing component/theme stylesheets and both bundled WOFF2 fonts are
included in the HTML. Only caller-pinned PNG, JPEG, or WebP image bytes are used.
Source files, fonts, images, input, and output receive hashes in the trace. The
output has no remote font/image dependency, executable JavaScript, submission
form, or external link. A static parser checks that surface; it does not measure
layout or validate rendering in a browser.

The source bundle is deliberately outside this public repository. Its original
design metadata can contain private reference locators. Generated input and
trace files can contain private company data and reference metadata as well;
save them in a private output location, not in public Git.

## Input

The envelope has `schema_version`, `company`, `selection`, `images`, and optional
`context`. `context` is preserved exactly as JSON metadata and is not interpreted
as proof, an approval, or a production status.

```json
{
  "schema_version": "lp54-composition-input/v1",
  "company": {
    "industry": "landscape",
    "brand": "合成テスト事業者",
    "brandEn": "SYNTHETIC COMPANY",
    "locality": "合成テスト地域",
    "contactLabel": "相談内容を確認する",
    "contactSub": "送信しない内部確認用です。",
    "parts": {
      "hero": {
        "title": "暮らしに合わせて、庭を整える。",
        "body": "これは接続確認のための合成本文です。"
      },
      "faq": {
        "title": "相談前に確認したいこと",
        "body": "これは接続確認のための合成Q&Aです。",
        "items": [
          {"title": "合成の質問1", "text": "合成の回答1"},
          {"title": "合成の質問2", "text": "合成の回答2"},
          {"title": "合成の質問3", "text": "合成の回答3"}
        ]
      }
    }
  },
  "selection": {
    "theme_id": "garden-studio",
    "design_ids": ["hero-02", "faq-03"]
  },
  "images": {
    "hero": {
      "path": "synthetic.png",
      "sha256": "REPLACE_WITH_THE_ACTUAL_64_CHARACTER_LOWERCASE_SHA256"
    }
  },
  "context": {"classification": "SYNTHETIC"}
}
```

The illustration's image hash must be replaced with the actual hash of the
chosen local file. The CLI resolves relative image paths against the input JSON
directory; the Python API requires an explicit `image_root` for relative paths.
Remote URLs and mismatched or undecodable image bytes are rejected.

`industry` must be `landscape`, `painting`, or `bar`. Both `theme_id` and
`design_ids` are explicit. A page starts with one Hero and uses each part at most
once. The theme's default order and picks are not substituted for caller choices.
An incompatible theme/candidate combination is rejected.

### Existing copy limits

Every selected part requires `title` and `body`; it can also have `eyebrow` and
`note`. Non-Hero parts require **exactly three items**, each with `title` and
`text`, plus optional `meta`. The adapter rejects a fourth item instead of
silently slicing it. Hero candidates currently do not support item/proof lists.

| Part | Additional existing fields |
| --- | --- |
| `trust` | Exactly three `stats`, each with `value` and `label` |
| `compare` | Each item requires `value` and `label` |
| `price` | Each item requires `price` and `label`; optional `value` must equal `price` |

Unknown fields, unselected part payloads, and unused image slots are rejected
with an explicit error. Company/research metadata belongs in `context` or in its
upstream artifact; it is not silently discarded from a render payload. No
fictional or demonstration copy is substituted when a required field is absent.

The bridge verifies every supplied nonempty part string against generated
section markup. A second render with unique field markers detects omission even
when two input fields contain identical wording. This checks text retention,
not whether CSS clips text, how line breaks appear, factual accuracy, or design
quality. Those production checks remain separate.

## Run and receive

```bash
PYTHONPATH=src python3 -m lp_engine.pilot_composition \
  --input /private/company-composition.json \
  --source-root /private/trusted-lp54-source \
  --out /private/composition-run-001
```

```python
from lp_engine.pilot_composition import compose_preview

trace = compose_preview(
    payload,
    source_root="/private/trusted-lp54-source",
    image_root="/private/selected-images",
    output_dir="/private/composition-run-001",
)
```

The destination must not already exist. A successful run writes these three
files after all static validation succeeds:

| File | Meaning |
| --- | --- |
| `index.html` | Self-contained internal composition preview |
| `composition_input.json` | Exact JSON values supplied to this adapter |
| `composition_manifest.json` | Source/input/image/output hashes, explicit selections, text/image mapping, preserved context and scope |

These files can be pinned and received through `artifact_handoff` like any other
artifact bundle. Receipt of those bytes does not promote a preview to a finished
LP or issue a P01–P22 stage receipt.

The manifest's `source_bundle_sha256` hashes the ordered 15-file list of relative
paths, sizes, and SHA-256 values. It differs from the hash of a ZIP container.
After validating an initial source bundle, supply this value through
`expected_source_sha256` or `--expected-source-sha256` to reject any source change
before executing that source. The source bytes are read once per run.

Every successful trace retains `quality_status=NOT_RUN`, `browser_qa=NOT_RUN`,
`production_ready=false`, `formal_contract_binding=NOT_ASSERTED`,
`automatic_downstream_execution=false`, and `external_actions=0`.

## Verification and remaining integration

`tests/test_pilot_composition.py` includes ordinary protocol tests using a small
synthetic source fixture. Those tests require Node.js and contain no private
source, company list, reference locator, or browser operation.

An optional pure static integration test is enabled by setting `LP54_SOURCE_ROOT`
to an explicitly trusted external source. It injects synthetic copy and images
into all 54 existing candidates and all nine themes and verifies the recorded
selections and retained text. It never opens generated HTML or the catalog in a
browser, and is not enabled by default in CI.

Remaining production work includes company-specific theme selection, actual
copy authoring, asset eligibility and placement, formal semantic/contract
bindings, layout and visual review, and a measured P01–P22 run. The adapter
reuses visual candidates; it does not declare them visually approved or count
their successful string generation as completed LPs.
