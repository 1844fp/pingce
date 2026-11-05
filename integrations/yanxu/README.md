# Yanxu offline integration

From evaluation-platform run `node integrations/yanxu/adapter.mjs --serve` in a separate terminal. It binds only 127.0.0.1:8876; POST /evaluate. No existing service is restarted. Set EVAL_ALLOWED_HOSTS=127.0.0.1 before starting the evaluation platform and register http://127.0.0.1:8876/evaluate as an HTTP target. Stop this bridge with Ctrl+C.

Request: {"input":{"operation":"audit","payload":{"bundle":{"claims":[]},"currentSources":[]}},"context":{"case_id":"offline-1"}}. Expected output: {"status":"awaiting_author","issues":[],"affectedLocations":[]}.

Operations are fixed: audit(bundle,currentSources), repair(payload), directly from writing-evidence.mjs. Inputs are JSON in memory; no caller paths, shell, model calls, credentials or manuscript upload. CLI alternative: pipe request JSON to `node integrations/yanxu/adapter.mjs --stdin`. Export current hashes with --manifest; manifest.json is the inspected version, not a guarantee of a frozen live checkout. Compare hashes before experiments; shared source can change.

This is real offline module execution. It is neither a simulated response nor real-model end-to-end writing. Caller-declared source metadata and quotes are checked structurally, not independently verified against literature. Contract errors return HTTP 400 and must count as target errors, never successful outputs. Request limit 256 KiB. No reference answer is needed or consumed.

Test: python -m pytest tests/test_yanxu_adapter.py -q. Tests use pytest tmp_path, never import platform storage, and never touch evaluation.db. Requires Node and the existing E:/AI/codex/writing-site checkout.
