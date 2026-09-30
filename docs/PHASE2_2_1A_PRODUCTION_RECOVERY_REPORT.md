# Phase 2.2.1A Production Capture Recovery

SSOT: Issue #143; scope is capture recovery only. Original candidate SHA ae598db0728b8b555a2eb3c6a26bb9f35e4308f0 was executed unchanged first. Subsequent batches target only still-failed original slots, with all four cell keys unchanged and separate immutable reviewed workflow pins. No smoke capture/dispatch was executed for this task.

Authoritative integrated outputs: `data/phase2_2_1a_recovery/`. The original pilot and previous source bundles are immutable historical inputs. In the recovered Master use `active_in_recovered_corpus` and the `*_derived` columns; historical fields from the old Master are preserved as historical data, not current counts. All 100 original rows remain; all replacement attempts are appended. The active corpus is 73 original usable + 27 accepted replacements = 100. No original mechanism/score is transferred to a replacement brand.

## Counts

- final_usable_reference_count: 100
- desktop_1440_durable_count: 100
- mobile_390_durable_count: 100
- both_viewports_durable_count: 100
- original_attempted: 100
- original_usable: 73
- candidate_attempts: 47
- successful_replacements: 27
- failed_attempts: 20
- capture_failed_attempts: 7
- visual_qa_rejected_attempts: 13
- reference_master_row_count: 147
- snapshot_count: 552
- scene_evidence_count: 1348
- observed_scene_evidence_count: 1014
- replacement_scene_evidence_count: 108
- archive_container_count: 16
- archive_index_entry_count: 1617
- security_bypass_count: 0
- phase2600_allowed: False
- verified_archive_member_count: 1527

## Reproduction

From this commit, install Pillow (ordinary image decoding) and run:

```sh
python scripts/materialize_phase2_2_1a_source.py --repo-root . --destination ../source_bundle
# Materialize the exact Library file/version pins listed in archive_registry.json
# into ../archive_audit using their recorded filenames. Do not use latest versions.
python scripts/build_phase2_2_1a_recovery.py --source-dir ../source_bundle --archive-dir ../archive_audit --inputs-dir data/phase2_2_1a_recovery_inputs --out-dir data/phase2_2_1a_recovery
python scripts/validate_phase2_2_1a_recovery.py --out-dir data/phase2_2_1a_recovery --archive-dir ../archive_audit
python -m unittest discover -s tests
```

The Integrated Builder derives Master, Matrix, Aggregate, QA, PM Summary, Archive Index and Failure/Replacement Ledger together from byte-verified durable archives and explicit actual image/official QA. The independent output validator checks the equality and all four 100 gates, exact-cell replacements, attempt accounting and every accepted Reference -> Snapshot -> Scene -> pinned Container -> Member -> SHA-256 chain. Archive loss, corruption, missing actual evidence and any count below 100 fail closed.

## Production pins and evidence

| Run | Candidate SHA | Artifact ID | Artifact/container SHA-256 | Durable Archive ID | Pinned file ID |
|---|---|---|---|---|---|
| 36677645592 | ae598db0728b8b555a2eb3c6a26bb9f35e4308f0 | 11080831668 | 6d509d641753f03c81a15e405e82f9f7361264b10af6c2def50a0c2c32a1843d | libfile_f01f731bc3b08191a94b0040bf3584c8 | file_0000000089bc81f5b51be20c5916ab26 |
| 36681036163 | 1a462e5a7be35f833043a0771a5f179faa90e67b | 11081383073 | a41d16795c3b410237bd60c792d795c4745f68fe337f30e28818b22a7d7425b5 | libfile_b0969bd038508191a144a5ec8e9a989e | file_0000000094e481f58c9e939998272464 |
| 36682051500 | 5c91a7818d57accd5f22782f9643f05452e833d3 | 11082202864 | 82437ae5a6c1a4a342e8984fb1a2bfccd404da01442bcecdff7ecba60e085ddc | libfile_0159e4527f0c8191858f5a0c5e054b20 | file_00000000597481f68e61b3e8b688fe24 |
| 36687315667 | 280f655ae8b635f0517db04dfe21dcef83c0ad95 | 11084366064 | a59e043fed60fcf28b931a511ce90918bfa7f7ba7ddee6f1e18d882cc3a34fe7 | libfile_118d6beb29dc8191a46f5c8f6eeb638e | file_00000000bd2881f5a1f977964f444332 |
| 36688082056 | 3299287cc4c17367364380c806444b8946f1ca29 | 11084386871 | 08b30b10b8dd4a198e8da826db7499a6482c178d5c4f60192fb102e2b8d81a61 | libfile_e3a293cf96b48191a0a6028788a7435c | file_00000000f38881f580f129441a42fef9 |

All archive pins are version 0. Five new production containers plus eleven original evidence containers were materialized and byte-verified. Actions artifacts are temporary handoff packages; acceptance is based on durable pinned archives with verified readback. Retention policy: keep at least three years after last use with yearly review; no backend retention guarantee is asserted. Any future loss/mismatch invalidates durable counts.

## Validation and limits

- Same-cell QA: 27/27 accepted; all 47 attempts passed the metadata Validator before approved_batch capture.
- Independent integrated output Validator: PASS; Master == Matrix == Aggregate == QA == PM Summary.
- Tests: 22/22 PASS. Includes missing archive, forged output, preflight cannot override capture failure, each under-100 hard gate, scroll lock and late-growing document checks.
- Actual QA rejects 20 attempts: 7 capture failures and 13 visual/evidence failures. Those records and any partial evidence remain in the audit trail. Includes challenge/403 failures, loading-only pages, ordinary notice scroll locks, unrendered content, embedded video security-denial pixels (never bypassed), and incomplete desktop tiled fallback. A successful workflow step alone never promoted a candidate.
- Static scene evidence only: 1,348 total source/replacement records; 1,014 observed; 334 original NOT_OBSERVED retained. Replacement scenes 108 (entry + full-page x both viewports x 27). No motion, compatibility, renderability, ranking or mechanism promotion is inferred.
- Ordinary capture hardening records actual window.scrollY to stable bottom, bounded load/render waits, and visible non-binding dismiss actions. The Allbirds popup uses only its observed official-host iframe and ordinary `Dismiss this popup` button; no DOM removal, cookie spoofing, browser fingerprint, proxy or CAPTCHA interaction.
- Input contract/security preserved: mode choice unchanged, target fixed to immutable reviewed SHA, read-only token, no credentials persisted, all security schema flags false, same-cell validator unchanged. No unrestricted URL/path/ref input.
- Original Pilot preserved: Git blob a2a746de3ce1be2e7ebfb6639a737fc8c0bd974f and SHA-256 dc6a369ac79f93a9e83aa0c75073757181c5bee15c892627f1cb5f06c2982c4d. Original failure ledger at ae598 is byte-preserved with SHA-256 9ca6f2608452851885d763fd3c8efee4f996bc97a28461aff30b295db172b67e; recovery is a separate overlay, not an overwrite.
- Unresolved recovery exceptions: none. Security bypass count: 0. phase2600_allowed=false.

STOP: PHASE_2_2_1_CAPTURE_RECOVERY_READY_FOR_PM_REVIEW
Compatibility Calibration, Production Renderability and 2,600 Expansion remain HOLD.
