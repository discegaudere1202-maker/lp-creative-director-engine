# MELT SKIN — Hero / Concept Boundary Spec

Status: CONFIRMED HUMAN GROUND TRUTH  
Confirmed by: Shun + Sarah PM  
Date: 2026-09-28  
SSOT Issue: #135

## Confirmed recognition

Shun confirmed that Sarah's understanding of the Hero→Concept boundary is now aligned.

### 1. Hero bottom edge

The straight horizontal termination currently visible at the bottom of the rebuilt Hero is **not** the intended final section boundary.

It must disappear in the final implementation.

### 2. Concept original boundary

The intended Hero / Concept boundary is the **actual image-content seam already present in the approved Concept image**.

This seam must be recovered from the real pixel/content transition across the **entire width** of the image.

It must not be reconstructed from:
- Sarah's manual hand-traced approximation
- Shun's hand-drawn green correction line
- a guessed Bézier curve
- a raster alpha approximation

The hand-drawn lines were only communication aids for alignment.

### 3. Unwanted middle band

The region between:

- the incorrect straight Hero bottom edge, and
- the real Concept original boundary

is an **unwanted middle band**.

That band must not exist in production HTML.

### 4. Full-width rule

The boundary must be recovered from image difference/content change over the full width, not only on the right side.

Left, center, and right all follow the same rule:

> detect the true image-content seam and use that exact seam as the sole Hero→Concept boundary.

### 5. Content preservation

All approved Concept content, including the upper text and labels, must remain fully visible.

Boundary correction must never solve the seam by cropping or hiding approved Concept content.

### 6. Final implementation rule

Production target:

```text
New Hero extends underneath
        ↓
actual recovered Concept image seam = only visible boundary
        ↓
full Concept content begins immediately below that seam
```

There must be:
- no straight Hero cutoff
- no second separator
- no white gap
- no third / middle image strip
- no duplicate wave
- no content loss

## Human confirmation

Shun confirmation:

> 「おっけい！認識は完全に合ったと思う！」

This spec is the locked interpretation to use for the next HTML implementation.