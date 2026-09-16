# Phase 7 Production Hardening v1

This phase adds a vendor-neutral SQLite persistence adapter, thin service API,
private operator view, freshness and opportunity-delta contracts, measured
metrics, structured observability, dead-letter recovery boundary, and TEST_ONLY
synthetic 1000-item restart/load validation.

External sales execution, public production publish, and manual LP edit remain
hard-disabled. Synthetic rows are never sales candidates.

Known limitations: live freshness re-fetch and live current-web capture are
adapters only; SQLite, static UI, hosting, authentication, and multi-user API
are reference boundaries and require a later operating-hardening decision.
