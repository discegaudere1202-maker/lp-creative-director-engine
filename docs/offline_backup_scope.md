# Offline SQLite snapshot correction

## Scope

This changes `backup_restore` only. It is a code-management change, not a
production deployment, Stage Receipt, whole-engine recovery or visual approval.
No existing workflow, permission, schema, renderer or private input is changed.

The old implementation copied only the main database file and compared four row
counts. In a local synthetic WAL reproduction, a committed insert was absent
from the copy while `data_loss` was still zero. A payload-only update produced
an equal row count and a reported `integrity=true`, but restored stale content.

## New behavior

- Pin a read snapshot and use SQLite's online backup API, including committed WAL
  content at that boundary; later commits belong to the next snapshot.
- Verify every table's row content, schema and database metadata, including audit
  events; reopen and verify the published standalone database.
- Do not create/migrate a source during verification.
- Preserve different existing targets, reject path aliases/symlinks and live
  target sidecars, reuse only an equivalent saved snapshot.
- Bound verification and backup duration. Fail without a success report.

`data_loss=0` means equality of the pinned database snapshot and its readback.
It does not assert that external LP files, media, credentials, source code or
changes committed after the snapshot were backed up. External files need their
own verified immutable storage and manifest binding.

## Validation

Run `python -m unittest discover -s tests -p test_backup_snapshot.py -v` with
`PYTHONPATH=src`. The 22 tests use synthetic data and include WAL insert/update,
uncommitted writes, concurrent post-snapshot writes, audit data, Unicode/BLOBs,
source preservation, bad input, timeout, no-overwrite and simultaneous callers.
The existing closed-database restore scenario is included. This is not the full
repository regression suite, independent review or an LP-generation benchmark.

References: https://www.sqlite.org/backup.html and the Python sqlite3 backup API.
