# Section Boundary Recognition Method

Status: METHOD RESET / ACTIVE RESEARCH  
Owner: Sarah PM  
Human Ground Truth: Shun  
SSOT Issue: #135  
Date: 2026-09-28

## Problem

Image-to-HTML fidelity requires recovering section boundaries from a generated Master image. Two failed shortcuts have been confirmed:

1. Raw pixel/edge strength is not a section detector; it also responds to hair, skin, typography, stone, products, shadows and other internal texture edges.
2. Reusing a Shun-approved boundary line is only a regression fixture for that known boundary. It cannot discover unseen boundaries.

## Important artifact correction

The full-width Hero / Concept annotation that Shun explicitly approved with `認識は完全に合ったと思う` was:

`/mnt/data/ヒーロー境界とコンセプト境界の注釈.png`

A later attempt incorrectly treated `MELT_SKIN_hero_concept_recognition_final_v1.png` as the approved artifact. That was a record-selection error.

## Required generalizable method

Boundary discovery must infer **section ownership first**, then derive the contour separating the two ownership regions.

For each adjacent section pair:

1. Take a transition crop with enough context from both sections.
2. Identify semantic anchors for the upper and lower sections (copy block, product scene, material/background treatment, section number/title, composition ownership).
3. Build two ownership regions: `UPPER_SECTION` and `LOWER_SECTION`.
4. Use color / texture / local edges only inside the semantic transition corridor as refinement evidence; never use raw edge magnitude as ground truth.
5. Enforce a single continuous boundary across the width unless the Master clearly contains a more complex topology.
6. Extract the contour where ownership changes.
7. Validate the detector on Hero / Concept **without using the approved Hero / Concept line as an input**.
8. Use the approved Hero / Concept boundary only as evaluation ground truth. If the method cannot rediscover it independently, the detector is rejected.
9. After the detector passes on the known pair, test it on unseen adjacent pairs such as Concept / Approach.
10. A Shun-confirmed output becomes a regression fixture, not an input dependency.

## Goal

The production system must be able to discover new section boundaries from a generated Master image without requiring Shun to manually draw or approve every boundary first.

## Current status

OPEN. Do not create another full-page boundary map until a detector can independently rediscover the known Hero / Concept boundary and then generalize to at least one unseen pair.